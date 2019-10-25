import argparse
import os


class InputFileAction(argparse.Action):
    """
    Handles input files.
    Binds an InputFile object to the arparse namespace.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            if len(values) == 1:
                file = values[0]
                if not os.path.exists(file):
                    msg = "File not found: {}".format(file)
                    raise(parser.error(msg))
                if not file.upper().endswith("JSON") and \
                   not file.upper().endswith("YAML"):
                    msg = "Invalid file ending: {}.".format(file)
                    msg += "JSON or YAML required!"
                    raise(parser.error(msg))
            else:
                msg = "More than one input file provided."
                raise(parser.error(msg))
        except RuntimeError:
            parser.error()

        # add the object to the namespace
        setattr(namespace, self.dest, file)


class OutfileAction(argparse.Action):
    """
    Handles output files.
    Binds an InputFile object to the arparse namespace.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            file = values
            while os.path.exists(file):
                msg = "File exists: {}.".format(file) + \
                        "Overwrite? (y/N): "
                ans = None
                while ans.upper() not in ("Y", "N"):
                    ans = input(msg) or "N"

                if ans.upper() in ("", "N"):
                    file = input("Enter new file name " + \
                                 "(default: reservation.png): ") \
                            or "reservation.png"
                else:
                    # user wants to overwrite
                    break

        except RuntimeError:
            parser.error()

        # add the object to the namespace
        setattr(namespace, self.dest, file)


def add_credentials_arg(subparser):
    subparser.add_argument(
            "--credentials", type=str,
            action=InputFileAction, required=True, nargs=1,
            help="Path to a json or yaml file with booking credentials")


def add_course_arg(subparser):
    subparser.add_argument(
        "--course", type=str, required=True,
        help="ID of the hochschulsport course")


def add_browser_selection_group(subparser):
    browser_select = subparser.add_mutually_exclusive_group(
                        required=False)
    browser_select.add_argument(
            "--use-firefox", action="store_true",
            help="Use a firefox gui session during the " +
            "booking process. " +
            "IMPORTANT: This requires geckodriver!")
    browser_select.add_argument(
            "--use-headless-firefox", action="store_true",
            help="Use a headless firefox session during the " +
            "booking process. " +
            "IMPORTANT: This requires geckodriver")
    browser_select.add_argument(
            "--use-chrome", action="store_true",
            help="Use a chrome gui session during the " +
            "booking process")
    browser_select.add_argument(
            "--use-headless-chrome", action="store_true",
            help="Use a headless chrome session during the " +
            "booking process. This is used by default.")


def parse_args():

    parser = argparse.ArgumentParser(
                description="Uni Tuebingen Hochschulsport course booking " +
                "and status retrieval",
                prog="hsp")

    # version info
    parser.add_argument(
        "-V", "--version", action="version",
        version="%(prog)s 1.0")

    subparsers = parser.add_subparsers(dest="subcommand")

    # CREDENTIALS CHECKING SUBCOMMAND
    creds_parser = subparsers.add_parser(
                        "check-credentials", help="Check " +
                        "the validity of a provided credentials file")
    add_credentials_arg(creds_parser)

    # STATUS CHECKING SUBCOMMAND
    status_parser = subparsers.add_parser(
                        "course-status", help="Check the " +
                        "status of a hochschulsport course")
    add_course_arg(status_parser)
    add_browser_selection_group(status_parser)

    # BOOKING SUBCOMMAND
    booking_parser = subparsers.add_parser(
                        "booking",
                        help="book a hochschulsport course")
    add_credentials_arg(booking_parser)
    add_course_arg(booking_parser)
    add_browser_selection_group(booking_parser)
    booking_parser.add_argument(
            "--booking-out", default="confirmation.png",
            action=OutfileAction,
            help="File destination to write a screenshot of the" +
            "confirmation page to. PNG format will be used.")

    args = parser.parse_args()

    if not args.subcommand:
        msg = "No task selected. Choose on of 'check-credentials', " + \
                "'course-status', 'booking'."
        parser.error(msg)

    return args
