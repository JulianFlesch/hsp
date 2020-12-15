
class Error(Exception):
    """ Package base Exception """

    def __init__(self, msg):
        self.msg = msg


class LoadingFailed(Error):

    def __init__(self, msg):
        self.msg = "Loading the page failed. " + msg


class CourseIdNotListed(Error):

    def __init__(self, course_id):
        self.msg = "Course with ID {} not found.".format(course_id)


class CourseIdAmbiguous(Error):

    def __init__(self, course_id):
        self.msg = "Course with ID {} is listed more than once.".format(course_id)


class CourseNotBookable(Error):

    def __init__(self, course_id, course_status):
        self.msg = "Course with ID {} is has non-bookable status: {}".format(
                    course_id, course_status)


class CourseHasNoWaitinglist(Error):

    def __init__(self, course_id):
        self.msg = "No waitinglist for course with ID {}".format(course_id)


class InvalidCredentials(Error):

    def __init__(self, msg):
        self.msg = msg


class BookingFailed(Error):

    pass


class FirefoxBinaryError(Error):
    """ Exception to express an error with the firefox Binary """

    pass


class ChromeBinaryError(Error):
    """ Exception to express an error with Chrome """

    pass
