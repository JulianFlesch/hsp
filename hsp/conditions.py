from selenium.common.exceptions import NoSuchElementException
import time


class submit_successful(object):
    """An expectation for checking if submit was successful,
    based on the disappearance of a second element.
    """
    def __init__(self, submit_locator, observed_locator):
        self.submit_locator = submit_locator
        self.observed_locator = observed_locator

    def __call__(self, driver):
        # submit the element
        driver.find_element(*self.submit_locator).submit()

        time.sleep(0.1)

        try:
            _ = driver.find_element(*self.observed_locator)
            return False
        except NoSuchElementException:
            # succeeded
            return True
