from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time

from .credentials import Credentials
from .page_parser import booking_button_xpath
from .errors import (CourseIdNotListed, CourseIdAmbiguous, CourseNotBookable,
                    InvalidCredentials)

def start_firefox():

    driver = webdriver.Firefox()
    return driver


def start_headless_firefox():

    ff_options = FirefoxOptions()
    ff_options.headless = True
    driver = webdriver.Firefox(options=ff_options)
    return driver


def start_chrome():

    driver = webdriver.Chrome()
    return driver


def start_headless_chrome():

    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


class HSPCourse:
    """
    """

    BASE_URL = "https://buchung.hsp.uni-tuebingen.de/angebote/aktueller_zeitraum/"
    COURSE_LIST_URL = BASE_URL + "kurssuche.html"

    def __init__(self, course_id, driver=None):
        self.course_id = str(course_id)
        self.driver = driver or self._init_driver()
        self.course_page_url = None
        self.course_time = None
        self.course_weekday = None
        self.course_level = None
        self._scrape_course_detail()

        self.course_name = None
        self.booking_possible = None
        self.course_status = None
        self._scrape_course_status()

    def _scrape_course_detail(self):

        self.driver.get(self.COURSE_LIST_URL)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        all_course_id_fields = soup.findAll("td", {"class": "bs_sknr"})
        course_id_td = list(filter(lambda cid: cid.getText() == self.course_id,
                                    all_course_id_fields))
        if len(course_id_td) == 1:
            course_id_td = course_id_td[0]
        elif len(course_id_td) == 0:
            raise CourseIdNotListed(self.course_id)
        elif len(course_id_td) > 1:
            raise CourseIdAmbiguous(self.course_id)

        # fill in course page link
        course_page_link = course_id_td.findParent().find("a")
        self.course_page_url = self.BASE_URL + course_page_link.get("href")

        # fill in course time
        course_time_td = course_id_td.find_next_sibling("td",
                                                        {"class": "bs_szeit"})
        self.course_time = course_time_td.getText()

        # fill in course weekday
        course_weekday_td = course_id_td.find_next_sibling("td",
                                                        {"class": "bs_stag"})
        self.course_weekday = course_weekday_td.getText()

        # fill in course level
        course_level_td = course_id_td.find_next_sibling("td",
                                                        {"class": "bs_sdet"})
        self.course_level = course_level_td.getText()

    def _scrape_course_status(self):
        self.driver.get(self.course_page_url)

        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # fill in course name
        course_name_div = soup.find("div", {"class": "bs_head"})
        self.course_name = course_name_div.getText()

        # fill in course status

        # fill in course bookable boolean

    def _init_driver(self):
        try:
            driver = start_headless_chrome()
        except WebDriverException as e:
            print(e)
            print("[!] Loading Chrome webdriver failed")
            print("... Attempting to use Firefox webdriver")
            driver = start_headless_chrome()
        return driver

    def info(self):
        infostr = "#{}: {} {}, {} {}".format(self.course_id or "",
                    self.course_name or "", self.course_level or "",
                    self.course_weekday or "", self.course_time or "")
        return infostr

    def status(self):
        pass

    def is_bookable(self):
        return True

    def booking(self, credentials, confirmation_file="confirmation.png"):

        if not self.is_bookable():
            raise CourseNotBookable(self.course_id, self.status())

        if not credentials or not credentials.is_valid:
            raise InvalidCredentials("Credentials are invalid")

        self.driver.get(self.course_page_url)

        # snapshot of open windows / tabs
        old_windows = self.driver.window_handles
        # press the booking button, which opens a new tab/
        offer_id = "K" + self.course_id
        booking_btn_xpath = booking_button_xpath(self.driver.page_source, offer_id)
        self.driver.find_element_by_xpath(booking_btn_xpath).click()
        # find the new tab
        new_tab = (set(self.driver.window_handles) - set(old_windows)).pop()
        # switch to new tab
        self.driver.switch_to.window(new_tab)
        self.driver.set_window_size(height=1500, width=1000)

        # gender radio select
        gender_xpath = '//input[@name="sex"][@value="{}"]'.format(
                    credentials.gender)
        self.driver.find_element_by_xpath(gender_xpath).click()

        # name field
        name_xpath = '//input[@id="BS_F1100"][@name="vorname"]'
        self.driver.find_element_by_xpath(name_xpath).send_keys(
            credentials.name)

        # surname field
        surname_xpath = '//input[@id="BS_F1200"][@name="name"]'
        self.driver.find_element_by_xpath(surname_xpath).send_keys(
            credentials.surname)

        # street+no field
        street_xpath = '//input[@id="BS_F1300"][@name="strasse"]'
        self.driver.find_element_by_xpath(street_xpath).send_keys(
            credentials.street + " " + credentials.number)

        # zip+city field
        city_xpath = '//input[@id="BS_F1400"][@name="ort"]'
        self.driver.find_element_by_xpath(city_xpath).send_keys(
            credentials.zip_code + " " + credentials.city)

        # status dropdown and matriculation number / employee phone
        status_xpath_template = '//select[@id="BS_F1600"]//option[@value="{}"]'
        status_xpath = status_xpath_template.format(credentials.status)
        # student status
        if credentials.status in ("S-UNIT", "S-aH"):
            self.driver.find_element_by_xpath(status_xpath).click()
            pid_xpath = '//input[@id="BS_F1700"][@name="matnr"]'
            self.driver.find_element_by_xpath(pid_xpath).send_keys(
                credentials.pid)
        # employee status
        elif credentials.status in ("B-UNIT", "B-UKT", "B-aH"):
            self.driver.find_element_by_xpath(status_xpath).click()
            pid_xpath = '//input[@id="BS_F1700"][@name="mitnr"]'
            self.driver.find_element_by_xpath(pid_xpath).send_keys(
                credentials.pid)
        elif credentials.status == "Extern":
            self.driver.find_element_by_xpath(status_xpath).click()

        # email field
        email_xpath = '//input[@id="BS_F2000"][@name="email"]'
        self.driver.find_element_by_xpath(email_xpath).send_keys(
            credentials.email)

        # agree to EULA
        eula_xpath = '//input[@name="tnbed"]'
        self.driver.find_element_by_xpath(eula_xpath).click()

        # submit the form
        while True:
            self.driver.find_element_by_xpath("//input[@type='submit']").submit()
            try:
                # try to find an element that is exclusively on the confirmation
                # page
                _ = self.driver.find_element_by_xpath(
                        "//div[@class='bs_text_red bs_text_big']")

                # confirm form by submitting the form again
                self.driver.find_element_by_xpath("//input[@type='submit']").submit()
                break

            except NoSuchElementException:
                time.sleep(2)

        # save the final page as a screenshot
        self.driver.save_screenshot(confirmation_file)

        # close the driver
        self.driver.quit()
