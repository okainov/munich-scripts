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

    @staticmethod
    def get_available_appointment_types():
        """
        :return: list of available appointment types
        """
        raise NotImplementedError

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
    def get_available_appointment_types():
        return [
            'FS Fahrerlaubnis erstmalig',
            'FS Erweiterung Fahrerlaubnis',
            'FS Erweiterung C und D',
            'FS Verlängerung des Prüfauftrags',
            'FS Führerschein mit 17',
            'FS Umtausch in Kartenführerschein',
            'FS Abnutzung, Namensänderung',
            'FS Ersatzführerschein',
            'FS Karteikartenabschnitt',
            'FS Internationaler FS beantragen',
            'FS Umschreibung EU EWR FS beantragen',
            'FS Umschreibung Ausländischer FS',
            'FS Verlängerung der Fahrberechtigung bei befristetem Aufenthalt',
            'FS Verlängerung C- D-Klasse',
            'FS Eintragung BKFQ ohne Verlängerung',
            'FS Fahrerlaubnis nach Entzug',
            'FS Zuerkennung der ausländischen Fahrerlaubnis',
            'FS PBS für Taxi etc beantragen',
            'FS PBS verlängern',
            'FS Ersatz PBS',
            'FS Dienstführerschein umschreiben',
            'FS Internationaler FS bei Besitz',
            'FS Abholung Führerschein',
            'FS Auskünfte lfd Antrag allgemein',
            'FS Auskünfte lfd Antrag Begutachtung',
            'FS Auskünfte lfd Antrag Betäubungsmittel',
            'FS Auskunft zur Entziehung des Führerscheins',
            'FS Anmeldung und Vereinbarung Prüftermin',
            'FS Allgemeine Information zur Ortskundeprüfung',
            'FS Besprechung des Prüfungsergebnisses',
            'FS Beratung Fahreignung',
        ]


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
    def get_available_appointment_types():
        return [
            'An- oder Ummeldung - Einzelperson',
            'An- oder Ummeldung - Einzelperson mit eigenen Fahrzeugen',
            'An- oder Ummeldung - Familie',
            'An- oder Ummeldung - Familie mit eigenen Fahrzeugen',
            'Eintragung Übermittlungssperre',
            'Meldebescheinigung',
            'Haushaltsbescheinigung',
            'Melderegisterauskunft',
            'Abmeldung (Einzelperson oder Familie)',
            'Familienstandsänderung/ Namensänderung',
            'Antrag Personalausweis',
            'Antrag Reisepass/Expressreisepass',
            'Antrag vorläufiger Reisepass',
            'Antrag oder Verlängerung/Aktualisierung Kinderreisepass',
            'Ausweisdokumente - Familie (Minderjährige und deren gesetzliche Vertreter)',
            'Nachträgliche Anschriftenänderung Personalausweis/Reisepass/eAT',
            'Nachträgliches Einschalten eID / Nachträgliche Änderung PIN',
            'Widerruf der Verlust- oder Diebstahlanzeige von Personalausweis oder Reisepass',
            'Verlust- oder Diebstahlanzeige von Personalausweis',
            'Verlust- oder Diebstahlanzeige von Reisepass',
            'Gewerbeummeldung (Adressänderung innerhalb Münchens)',
            'Gewerbeabmeldung',
            'Führungszeugnis beantragen',
            'Gewerbezentralregisterauskunft beantragen – natürliche Person',
            'Gewerbezentralregisterauskunft beantragen – juristische Person',
            'Bis zu 5 Beglaubigungen Unterschrift',
            'Bis zu 5 Beglaubigungen Dokument',
            'Bis zu 20 Beglaubigungen',
            'Fabrikneues Fahrzeug anmelden (mit deutschen Fahrzeugpapieren und CoC)',
            'Fahrzeug wieder anmelden',
            'Fahrzeug umschreiben von außerhalb nach München',
            'Fahrzeug umschreiben innerhalb Münchens',
            'Fahrzeug außer Betrieb setzen',
            'Saisonkennzeichen beantragen',
            'Kurzzeitkennzeichen beantragen',
            'Umweltplakette/ Feinstaubplakette für Umweltzone beantragen',
            'Adressänderung in Fahrzeugpapiere eintragen lassen',
            'Namensänderung in Fahrzeugpapiere eintragen lassen',
            'Verlust oder Diebstahl der Zulassungsbescheinigung Teil I',
        ]


class ForeignLabor(Buro):
    @staticmethod
    def get_name():
        return 'Ausländerbehörde'

    @staticmethod
    def _get_base_page():
        # Apparently there is no single page for all appointments publicly available
        return 'https://www.muenchen.de/rathaus/Stadtverwaltung/Kreisverwaltungsreferat/Auslaenderwesen/Terminvereinbarung-.html'

    @staticmethod
    def get_frame_url():
        return 'https://www46.muenchen.de/termin/index.php?loc=ABH'

    @staticmethod
    def get_available_appointment_types():
        return [
            'Aufenthaltserlaubnis Blaue Karte EU',
            'Aufenthaltserlaubnis Blaue Karte EU (inländ. Hochschulabsolvent)',
            'Aufenthaltserlaubnis für Forschende',
            'Aufenthaltserlaubnis für Gastwissenschaftler, wissenschaftliche Mitarbeiter',
            'Aufenthaltserlaubnis zum Studium',
            'Aufenthaltserlaubnis zur Studienvorbereitung',
            'Aufenthaltserlaubnis für Doktoranden',
            'Fachrichtungswechsel',
            'Facharztausbildung',
            'Niederlassungserlaubnis allgemein',
            'Niederlassungserlaubnis Blaue Karte EU',
            'Aufenthaltserlaubnis zur Beschäftigung (Fachkräfte / Mangelberufe)',
            'Aufenthaltserlaubnis zur Arbeitsplatzsuche',
            'Selbständige und freiberufliche Erwerbstätigkeit',
            'Ehegattennachzug zum Drittstaatsangehörigen',
            'Eigenständiges Aufenthaltsrecht',
            'Aufenthaltserlaubnis für Kinder',
            'Familiennachzug in Ausnahmefällen',
            'Familiennachzug (SCIF)',
            'Familiennachzug (Stu)',
            'Verpflichtungserklärung (langfristige Aufenthalte)',
            'Verpflichtungserklärung (kurzfristige Aufenthalte)',
            'Erlöschen des Aufenthaltstitels, § 51 AufenthG',
            'Übertrag Aufenthaltstitel in neuen Pass',
            'Bescheinigung (Aufenthaltsstatus)',
            'Aufenthaltserlaubnis für langfristig Aufenthaltsberechtigte',
            'Niederlassungserlaubnis für Familienangehörige von Deutschen',
            'Niederlassungserlaubnis ab 16 Jahren',
            'Aufenthaltserlaubnis zur betrieblichen Ausbildung',
            'Aufenthaltserlaubnis zur Beschäftigung',
            'Niederlassungserlaubnis Asyl / int. Schutzberechtigte',
            'Familiennachzug zu EU-Staatsangehörigen',
            'Daueraufenthaltsbescheinigung',
            'Abholung elektronischer Aufenthaltstitel  (eAT)',
            'Abholung elektronischer Reiseausweis (eRA)',
            'Schülersammelliste',
            'Aufenthaltserlaubnis aus humanitären Gründen',
            'Medizinische Behandlung (Privatpatienten)',
            'Medizinische Behandlung (Botschaftspatienten)',
            'Werkverträge',
            'Firmenkunden',
            'Aufenthaltserlaubnis zur Arbeitsplatzsuche (16 V)',
            'Niederlassungserlaubnis für Hochqualifizierte',
            'Änderung der Nebenbestimmungen (AE)',
            'Niederlassungserlaubnis für Absolventen dt. Hochschulen',
            'Beratung allgemein',
            'Familiennachzug zu dt. Staatsangehörigen',
            'Aufenthaltserlaubnis zum Deutschintensivkurs',
        ]


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
    # appointments = get_termins(ForeignLabor, 'Niederlassungserlaubnis Blaue Karte EU')

    if appointments:
        print(json.dumps(appointments, sort_keys=True, indent=4, separators=(',', ': ')))
