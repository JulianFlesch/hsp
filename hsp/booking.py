from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (NoSuchElementException,
                                        TimeoutException,
                                        WebDriverException)
from .errors import (CourseIdNotListed, CourseIdAmbiguous,
                     CourseNotBookable, InvalidCredentials, LoadingFailed)
from .conditions import submit_successful


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
        self.timeout = 20  # waiting time for site to load in seconds
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

        self._booking_page = None

    def _cl_click_filter_checkboxes(self):

        assert(self.driver.current_url == self.COURSE_LIST_URL)

        # wait until checkbox is loaded
        nonbookable_cb_id = "bs_anmeldefrei"
        checkbox_present = EC.visibility_of_element_located(
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

    def _get_el_from_courselist(self, xpath):

        assert(self.driver.current_url == self.COURSE_LIST_URL)
        return self.driver.find_element_by_xpath(xpath)

    def _get_el_from_coursepage(self, xpath):

        assert(self.driver.current_url == self.course_page_url)
        return self.driver.find_element_by_xpath(xpath)

    def _cl_get_time(self, course_row_xpath):

        time_xpath = course_row_xpath + '/td[@class="bs_szeit"]'
        return self._get_el_from_courselist(time_xpath).text

    def _cl_get_weekday(self, course_row_xpath):

        weekday_xpath = course_row_xpath + '/td[@class="bs_stag"]'
        return self._get_el_from_courselist(weekday_xpath).text

    def _cl_get_location(self, course_row_xpath):

        location_xpath = course_row_xpath + '/td[@class="bs_sort"]'
        return self._get_el_from_courselist(location_xpath).text

    def _cl_get_level(self, course_row_xpath):

        location_xpath = course_row_xpath + '/td[@class="bs_sdet"]'
        return self._get_el_from_courselist(location_xpath).text

    def _cl_get_course_link(self, course_row_xpath):

        a_xpath = course_row_xpath + '/td[@class="bs_sbuch"]//a'
        a = self._get_el_from_courselist(a_xpath)
        return a.get_property("href")

    def _cp_get_course_name(self):

        title_xp = "//div[@class='bs_head']"
        course_name_div = self._get_el_from_coursepage(title_xp)
        return course_name_div.text

    def _cp_get_bookingbtn_or_status_element(self):

        course_code = "K" + self.course_id
        xpath = "//a[@id='{}']/following::*".format(course_code)
        return self._get_el_from_coursepage(xpath)

    def _scrape_course_detail(self):

        self.driver.get(self.COURSE_LIST_URL)

        try:
            self._cl_click_filter_checkboxes()

            # course site features a table:
            # extract the row that starts with the course id
            xpath = '//td[text()="{}"]/parent::tr'
            course_row_xpath = xpath.format(self.course_id)

            self.time = self._cl_get_time(course_row_xpath)
            self.weekday = self._cl_get_weekday(course_row_xpath)
            self.location = self._cl_get_location(course_row_xpath)
            self.level = self._cl_get_level(course_row_xpath)
            self.course_page_url = self._cl_get_course_link(course_row_xpath)

        except TimeoutException:
            raise LoadingFailed("Timeout while loading course list page")

        except NoSuchElementException:
            raise CourseIdNotListed(self.course_id)

    def _scrape_course_status(self):

        self.driver.get(self.course_page_url)

        self.course_name = self._cp_get_course_name()
        bookbtn_or_status = self._cp_get_bookingbtn_or_status_element()

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

    def _switch_to_booking_page(self):

        if self.has_waitinglist() or not self.is_bookable():
            raise CourseNotBookable(self.course_id, self.status())

        self.driver.get(self.course_page_url)

        # at this point, the course is bookable
        booking_btn = self._cp_get_bookingbtn_or_status_element()

        # snapshot of open windows / tabs
        old_windows = self.driver.window_handles

        # press the booking button, which opens a new tab
        booking_btn.click()

        # find the new tab
        new_tab = (set(self.driver.window_handles) - set(old_windows)).pop()

        # switch to new tab
        self.driver.switch_to.window(new_tab)

        # make the window larger, so no fields are being hidden
        self.driver.set_window_size(height=1500, width=2000)

        self._booking_page = self.driver.current_url

    def _bp_enter_personal_details(self, credentials):

        assert (self.driver.current_url == self._booking_page)

        if not credentials or not credentials.is_valid:
            raise InvalidCredentials("Credentials are invalid")

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

    def _retry_submit(self, submit_loc, control_loc):
        """
        Retry submitting, until control_loc disappears
        """

        assert(self.driver.current_url == self._booking_page)

        wait = WebDriverWait(self.driver, self.timeout)
        wait.until(submit_successful(submit_loc, control_loc))

    def _bp_wait_until_submit(self):
        """
        Retries submitting the data, until the confirmation page is loaded.
        Pag chage is detected by observing a checkbox field, that disappears.
        """
        xpath = "//input[@type='submit'][@value='weiter zur Buchung']"
        submit_locator = (By.XPATH, xpath)

        observed_xpath = "//input[@type='checkbox'][@name='tnbed']"
        control_locator = (By.XPATH, observed_xpath)

        self._retry_submit(submit_locator, control_locator)

    def _bp_wait_until_confirm(self):
        """
        Retries confirming the form, until the ticket is loaded
        """
        xpath = "//input[@type='submit'][@value='verbindlich buchen']"
        submit_locator = (By.XPATH, xpath)

        observed_xpath = "//div[contains(@class, 'bs_text_red') and contains(@class, 'bs_text_big')]"
        control_locator = (By.XPATH, observed_xpath)

        self._retry_submit(submit_locator, control_locator)

    def _save_screenshot(self, outfile):

        if outfile is None:
            tmpl = "booking_confirmation_{}.png"
            outfile = tmpl.format(self.course_id)

        # save the final page as a screenshot
        self.driver.save_screenshot(outfile)
        print("[*] Booking ticket saved to {}".format(outfile))

    def booking(self, credentials, confirmation_file=None):

        self._switch_to_booking_page()
        self._bp_enter_personal_details(credentials)

        # wait until inputs are submited and page changes
        self._bp_wait_until_submit()

        # wait until confirm button is pressed and page changes
        self._bp_wait_until_confirm()

        self._save_screenshot(confirmation_file)

        # close the driver
        # self.driver.quit()
