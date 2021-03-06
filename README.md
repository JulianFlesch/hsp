# HSP Booking

This is a utility for booking and checking on hochschulsport courses at EKU
Tübingen.

# Installation

This package uses Python3 and a number of third party packages.
It is recommended to set up and activate a virtualenv to contain the
dependencies by running:
```
virtualenv --python=python3 venv
source venv/bin/activate
```

Installation has to be done manually with the `setup.py` script.
```
python setup.py build sdist
pip install dist/hsp-[version].tar.gz
```
_(in above command [version] is the version of the package to be installed)_

This will also install the required Python dependencies, most importantly the
packages `selenium` and `bs4` for web automation and scraping.

## External dependencies

This package also requires an installation of Chrome/Chromium or Firefox and geckodriver available in PATH.

# Course Status

By checking on the status of a course, it can be determined if it is bookable.
With `hsp` this can be achieved from the command line by calling:

```
$ hsp course-status --course <course-number>
```

Alternatively, from inside a Python shell this can be achieved with the
following lines:

```
from hsp import HSPCourse, Credentials, start_headless_chrome
course_id = "3013"

driver = start_headless_chrome()

course = HSPCourse(course_id, driver)
course.status()
```


# Credentials

The following credentials are required for booking a hsp course:
  * name
  * surname
  * gender: Has to be one of "M" (male) or "W" (female)
  * street
  * number
  * zip_code
  * city
  * status: Has to be one of the following:
    - "S-UNIT" for students at EKU Tübingen
    - "S-aH" for students at other schools
    - "B-UNIT" for employees at EKU Tübingen
    - "B-UKT" for University Hopsital Tübingen employees
    - "B-aH" for employees at other schools
    - "Extern" all others
  * pid: Has to an employee phone or matriculation number
  * email

These credentials can be provided in JSON or YAML format.
The valid following example is JSON formatted:

```
{
"name": "Anton",
"surname": "Charlston",
"gender": "M",
"street": "Gartenstraße",
"number": "25",
"zipcode": "7207",
"city": "Tübingen",
"status": "S-UNIT",
"pid": "11111111",
"email": "someone@somedomain.de"
}
```

To validate the credentials the `hsp` command line utility, or a Python shell
can be used:

```
$ # bash
$ hsp check-credentials --credentials creds.json
```

```
# Python Shell
from hsp import Credentials

# this yields a credentials object or throws a InvalidCredentials Exception if
# a field is missing
creds = Credentials.from_json("credentials.json")
```

# Booking

To book courses, a valid course ID and credentials file has to be provided.
With `hsp` booking from the commandline then works as follows:
```
$ hsp booking --credentials creds.yaml --course 3013
```

```
from hsp import HSPCourse, Credentials, start_headless_chrome
course_id = "3013"

driver = start_headless_chrome()

hspcourse = HSPCourse(course_id, driver)
creds = Credentials(name=..., surname=..., gender=<M for male or W for female>,
  street=..., number=..., zip_code=..., city=...,
  status =..., pid=<e.g. matriculation number>, email=...)

# book the course
hspcourse.booking(creds)
```
