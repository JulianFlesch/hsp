from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (NoSuchElementException,
                                        TimeoutException,
                                        WebDriverException)
from .credentials import Credentials
from .errors import (CourseIdNotListed, CourseIdAmbiguous,
                     CourseNotBookable, InvalidCredentials, LoadingFailed)
import time

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
        self.timeout = 1  # waiting time for site to load in seconds
        self.driver = driver or self._init_driver()
        self.course_id = str(course_id)
        self.course_page_url = None
        self.time = None
        self.weekday = None
        self.location = None
        self.level = None
        self._scrape_course_detail()

        self.course_name = None
        self.booking_possible = None
        self.waitinglist_exists = None
        self.course_status = None
        self._scrape_course_status()

    def _scrape_course_detail(self):

        self.driver.get(self.COURSE_LIST_URL)

        try:
            # wait until checkbox is loaded
            nonbookable_cb_id = "bs_anmeldefrei"
            checkbox_present = EC.presence_of_element_located(
                                (By.ID, nonbookable_cb_id))
            WebDriverWait(self.driver, self.timeout).until(checkbox_present)

            # show non-bookable and booked-out courses
            nonbookable_cb = self.driver.find_element_by_id(nonbookable_cb_id)
            if not nonbookable_cb.is_selected():
                nonbookable_cb.click()

            bookedout_cb_id = "bs_ausgebucht"
            bookedout_cb = self.driver.find_element_by_id(bookedout_cb_id)
            if not bookedout_cb.is_selected():
                bookedout_cb.click()

            # wait until the site displays previously hidden elements
            time.sleep(0.05)

            # course site features a table:
            # extract the row that starts with the course id
            xpath = '//td[text()="{}"]/parent::tr'
            course_row_xp = xpath.format(self.course_id)

            # find and fill in course time
            xpath = course_row_xp + '/td[@class="bs_szeit"]'
            time_td = self.driver.find_element_by_xpath(xpath)
            self.time = time_td.text

            # find and fill in course weekday
            xpath = course_row_xp + '/td[@class="bs_stag"]'
            weekday_td = self.driver.find_element_by_xpath(xpath)
            self.weekday = weekday_td.text

            # find and fill in location
            xpath = course_row_xp + '/td[@class="bs_sort"]'
            location_td = self.driver.find_element_by_xpath(xpath)
            self.location = location_td.text

            # find and fill in course level
            xpath = course_row_xp + '/td[@class="bs_sdet"]'
            level_td = self.driver.find_element_by_xpath(xpath)
            self.level = level_td.text

            # find the course site link
            xpath = course_row_xp + '/td[@class="bs_sbuch"]//a'
            a = self.driver.find_element_by_xpath(xpath)
            self.course_page_url = a.get_property("href")

        except TimeoutException:
            raise LoadingFailed("Timeout while loading course list page")

    def _scrape_course_status(self):

        self.driver.get(self.course_page_url)

        # find and fill in course name
        title_xp = "//div[@class='bs_head']"
        course_name_div = self.driver.find_element_by_xpath(title_xp)
        self.course_name = course_name_div.text

        # find and fill in course status
        course_code = "K" + self.course_id
        xpath = "//a[@id='{}']/following::*".format(course_code)
        bookbtn_or_status = self.driver.find_element_by_xpath(xpath)

        # If bookbtn_or_status is a <span> ... </span> element,
        # the course is not bookable and there is it contains a
        # no-booking-possible status
        if bookbtn_or_status.tag_name == "span":
            self.course_status = bookbtn_or_status.text
            self.booking_possible = False
            self.waitinglist_exists = False

        elif "bs_btn_warteliste" in bookbtn_or_status.get_attribute("class"):
            self.course_status = "queue signup"
            self.booking_possible = False
            self.waitinglist_exists = True

        elif "bs_btn_buchen" in bookbtn_or_status.get_attribute("class"):
            self.course_status = "booking possible"
            self.booking_possible = True
            self.waitinglist_exists = False

        else:
            self.course_status = "unknown"
            self.booking_possible = False
            self.waitinglist_exists = False

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
                                             self.course_name or "",
                                             self.course_level or "",
                                             self.course_weekday or "",
                                             self.course_time or "")
        return infostr

    def status(self):
        return "Status: {}".format(self.course_status)

    def is_bookable(self):
        return self.booking_possible

    def has_waitinglist(self):
        return self.waitinglist_exists

    def booking(self, credentials, confirmation_file="confirmation.png"):

        if self.has_waitinglist() or not self.is_bookable():
            raise CourseNotBookable(self.course_id, self.status())

        if not credentials or not credentials.is_valid:
            raise InvalidCredentials("Credentials are invalid")

        self.driver.get(self.course_page_url)
        offer_id = "K" + self.course_id
        booking_btn_xpath = booking_button_xpath(self.driver.page_source, offer_id)
        booking_btn = self.driver.find_element_by_xpath(booking_btn_xpath)

        # snapshot of open windows / tabs
        old_windows = self.driver.window_handles

        # press the booking button, which opens a new tab/
        booking_btn.click()

        # find the new tab
        new_tab = (set(self.driver.window_handles) - set(old_windows)).pop()

        # switch to new tab
        self.driver.switch_to.window(new_tab)
        self.driver.set_window_size(height=1500, width=2000)

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
            time.sleep(2)

            try:
                # try to find an element that is exclusively on the confirmation
                # page
                _ = self.driver.find_element_by_xpath(
                        "//div[@class='bs_text_red bs_text_big']")
                break

            except NoSuchElementException:
                pass


        # confirm form by submitting the form again
        self.driver.find_element_by_xpath("//input[@type='submit']").submit()

        # save the final page as a screenshot
        self.driver.save_screenshot(confirmation_file)
        print("[*] Booking ticket saved to {}".format(confirmation_file))

        # close the driver
        #self.driver.quit()
