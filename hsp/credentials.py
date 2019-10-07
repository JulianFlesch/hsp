from .errors import InvalidCredentials
import json
import yaml


class Credentials:

    def __init__(self, name=None, surname=None, gender=None, street=None,
                    number=None, zip_code=None, city=None,
                    status=None, pid=None, email=None):

        self.name = name
        self.surname = surname
        self.gender = gender
        self.street = street
        self.number = number
        self.zip_code = zip_code
        self.city = city
        self.status = status
        self.pid = pid
        self.email = email

    def is_valid(self):
        return self.name and self.surname and self.gender in ("M", "W") and \
            self.street and self.number and self.zip_code and self.city and \
            self.status in ("S-UNIT", "S-aH", "B-UNIT", "B-UKT", "B-aH", "Extern") and \
            self.pid and self.email

    @classmethod
    def from_dict(cls, d):
        try: name = d["name"]
        except KeyError: raise InvalidCredentials("No name provided")
        try: surname = d["name"]
        except KeyError: raise InvalidCredentials("No surname provided")
        try: gender = d["gender"]
        except KeyError: raise InvalidCredentials("No gender provided")
        if not gender in ("M", "W"):
            raise InvalidCredentials("Gender must be one of {'M', 'W'}")
        try: street = d["street"]
        except KeyError: raise InvalidCredentials("No street provided")
        try: number = d["number"]
        except KeyError: raise InvalidCredentials("No house number provided")
        try: zip_code = d["zipcode"]
        except KeyError: raise InvalidCredentials("No zipcode provided")
        try: city = d["city"]
        except KeyError: raise InvalidCredentials("No city  provided")
        try: status = d["status"]
        except KeyError: raise InvalidCredentials("No status provided")
        statuses = ("S-UNIT", "S-aH", "B-UNIT", "B-UKT", "B-aH", "Extern")
        if not status in statuses:
            raise InvalidCredentials("'status' must be one of {}".format(statuses))
        # external people don't have an employee phone or matriculation number
        if not status == "Extern":
            try: pid = d["pid"]
            except KeyError:
                raise InvalidCredentials("No matriculation " + \
                    "number / employee phone number ('pid') provided")
        else:
            pid = ""
        try: email = d["email"]
        except KeyError: raise InvalidCredentials("No email provided")

        return cls(name=name, surname=surname, gender=gender, street=street,
                    number=number, zip_code=zip_code, city=city,
                    status=status, pid=pid, email=email)

    @classmethod
    def from_json(cls, jsonfile):
        with open(jsonfile, "r") as jf:
            d = json.load(jf)
            return cls.from_dict(d)

    @classmethod
    def from_yaml(cls, yamlfile):
        with open(yamlfile, "r") as yf:
            d = yaml.load(yf)
            return cls.from_dict(d)
