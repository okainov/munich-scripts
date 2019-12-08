import datetime

import requests
import re
import json


class Meta(type):
    def __repr__(cls):
        return cls.get_name()


class Buro(metaclass=Meta):
    """
    Base interface-like class for all departments providing appointments on ...muenchen.de/termin/index.php... page
    """

    appointment_types = None
    appointment_type_date = None

    @classmethod
    def get_available_appointment_types(cls):
        """
        :return: list of available appointment types
        """
        # Cache appointment type results for one day
        if cls.appointment_types and (datetime.datetime.now() - cls.appointment_type_date).days < 1:
            return cls.appointment_types

        responce = requests.get(cls.get_frame_url())
        # Search for text CASETYPES. So far the only issue was in "+" sign for CityHall in some service variable,
        #  that's why exclude it from the name
        cls.appointment_types = re.findall('CASETYPES\[([^+]*?)\]', responce.content.decode("utf-8"))
        cls.appointment_type_date = datetime.datetime.now()
        return cls.appointment_types

    @staticmethod
    def get_frame_url():
        """
        :return: URL with appointments form
        """
        raise NotImplementedError

    @staticmethod
    def _get_base_page():
        """
        :return: actual external web-page containing the frame. Not really needed for implementation, but may be useful
        for testing or debugging
        """
        raise NotImplementedError

    @staticmethod
    def get_name():
        """
        :return: human-readable name of the buro
        """
        raise NotImplementedError

    @staticmethod
    def get_id():
        """
        :return: machine-readable unique ID of the buro
        """
        return 'baseburo'

    @staticmethod
    def get_typical_appointments() -> list:
        """
        :return: list of tuples (<Name of appointment>, <index>)
        """
        return []

    @staticmethod
    def get_buro_by_id(buro_id):
        for buroClass in Buro.__subclasses__():
            if buroClass.get_id() == buro_id:
                return buroClass()

        return None


class DMV(Buro):
    @staticmethod
    def get_name():
        return 'Führerscheinstelle'

    @staticmethod
    def _get_base_page():
        return 'https://www.muenchen.de/rathaus/terminvereinbarung_fs.html'

    @staticmethod
    def get_frame_url():
        return 'https://www22.muenchen.de/termin/index.php?loc=FS'

    @staticmethod
    def get_typical_appointments() -> list:
        res = []
        # Driver license exchange - FS Umschreibung Ausländischer FS
        for index in [11]:
            res.append((index, DMV.get_available_appointment_types()[index]))
        return res

    @staticmethod
    def get_id():
        """
        :return: machine-readable unique ID of the buro
        """
        return 'fs'


class CityHall(Buro):
    @staticmethod
    def get_name():
        return 'Bürgerbüro'

    @staticmethod
    def _get_base_page():
        return 'https://www.muenchen.de/rathaus/terminvereinbarung_bb.html'

    @staticmethod
    def get_frame_url():
        return 'https://www56.muenchen.de/termin/index.php?loc=BB'

    @staticmethod
    def get_typical_appointments() -> list:
        res = []
        # Anmeldungs and Abmeldung
        for index in [0, 1, 2, 3, 4]:
            res.append((index, CityHall.get_available_appointment_types()[index]))
        return res

    @staticmethod
    def get_id():
        """
        :return: machine-readable unique ID of the buro
        """
        return 'bb'


class ForeignLabor(Buro):
    @staticmethod
    def get_name():
        return 'Ausländerbehörde'

    @staticmethod
    def _get_base_page():
        return 'https://www.muenchen.de/rathaus/terminvereinbarung_abh.html?cts='

    @staticmethod
    def get_frame_url():
        return 'https://www46.muenchen.de/termin/index.php?loc=ABH'

    @staticmethod
    def get_typical_appointments() -> list:
        res = []
        # Blue Card, Students and NE
        for index in [0, 4, 9]:
            res.append((index, ForeignLabor.get_available_appointment_types()[index]))
        return res

    @staticmethod
    def get_id():
        """
        :return: machine-readable unique ID of the buro
        """
        return 'abh'


class KFZ(Buro):
    @staticmethod
    def get_name():
        return 'Kfz-Zulassung'

    @staticmethod
    def _get_base_page():
        return 'https://www.muenchen.de/rathaus/terminvereinbarung_kfz.html'

    @staticmethod
    def get_frame_url():
        return 'https://www22.muenchen.de/termin/index.php?loc=KFZ'

    @staticmethod
    def get_typical_appointments() -> list:
        res = []
        # Initial registration and address changge
        for index in [0, 1, 2, 21]:
            res.append((index, KFZ.get_available_appointment_types()[index]))
        return res

    @staticmethod
    def get_id():
        """
        :return: machine-readable unique ID of the buro
        """
        return 'kfz'


class Pension(Buro):
    @staticmethod
    def get_name():
        return 'Versicherungsamt'

    @staticmethod
    def _get_base_page():
        return 'https://www.muenchen.de/rathaus/terminvereinbarung_va.html'

    @staticmethod
    def get_frame_url():
        return 'https://www5.muenchen.de/termin/index.php?loc=VA'

    @staticmethod
    def get_typical_appointments() -> list:
        res = []
        # Pension information for NE
        for index in [6]:
            res.append((index, Pension.get_available_appointment_types()[index]))
        return res

    @staticmethod
    def get_id():
        """
        :return: machine-readable unique ID of the buro
        """
        return 'va'


def write_response_to_log(txt):
    with open('log.txt', 'w', encoding='utf-8') as f:
        f.write(txt)


def get_termins(buro, termin_type):
    """
    Get available appointments in the given buro for the given appointment type.
    :param buro: Buro to search in
    :param termin_type: what type of appointment do you want to find?
    :return: dictionary of appointments, keys are possible dates, values are lists of available times
    """

    # Session is required to keep cookies between requests
    s = requests.Session()
    # First request to get and save cookies
    s.post(buro.get_frame_url())

    termin_data = {
        'CASETYPES[%s]' % termin_type: 1,
        'step': 'WEB_APPOINT_SEARCH_BY_CASETYPES',
    }
    response = s.post(buro.get_frame_url(), termin_data)
    txt = response.text

    try:
        json_str = re.search('jsonAppoints = \'(.*?)\'', txt).group(1)
    except AttributeError:
        print('ERROR: cannot find termins data in server\'s response. See log.txt for raw text')
        write_response_to_log(txt)
        return None

    appointments = json.loads(json_str)
    # We expect structure of this JSON should be like this:
    # {
    #     'Place ID 1': {
    #         # Address
    #         'caption': 'F\u00fchrerscheinstelle Garmischer Str. 19/21',
    #         # Some internal ID
    #         'id': 'a6a84abc3c8666ca80a3655eef15bade',
    #         # Dictionary containing data about appointments
    #         'appoints': {
    #             '2019-01-25': ['09:05', '09:30'],
    #             '2019-01-26': []
    #             # ...
    #         }
    #     }
    # }
    # So there can be several Buros located in different places in the city

    return appointments


if __name__ == '__main__':
    # Example for exchanging driver license
    appointments = get_termins(DMV, 'FS Umschreibung Ausländischer FS')

    # # Example for Anmeldung
    # appointments = get_termins(CityHall, 'An- oder Ummeldung - Einzelperson')

    # # Example for NE with Blue Card
    # appointments = get_termins(ForeignLabor, 'Niederlassungserlaubnis allgemein')

    # # Example for KFZ and car registration
    # appointments = get_termins(KFZ, 'ZUL Fabrikneues Fahrzeug')

    if appointments:
        print(json.dumps(appointments, sort_keys=True, indent=4, separators=(',', ': ')))
