import requests
import re
import json


def write_response_to_log(txt):
    with open('log.txt', 'w', encoding='utf-8') as f:
        f.write(txt)


def get_termins(termin_type='FS Umschreibung Ausländischer FS'):
    """
    Get termins status for given type.
    Base page https://www.muenchen.de/rathaus/terminvereinbarung_fs.html,
    and the frame for termins is https://www22.muenchen.de/termin/index.php?loc=FS
    :param termin_type: what type of appointment do you want to find?
    :return: dictionary of appointments, keys are possible dates, values are lists of available times
    """

    TERMIN_URL = 'https://www22.muenchen.de/termin/index.php?loc=FS&ct=1071898'

    # Which type of termin - change foreign driver license
    # Other available types:
    # 'CASETYPES[FS Fahrerlaubnis erstmalig]':0,
    # 'CASETYPES[FS Erweiterung Fahrerlaubnis]':0,
    # 'CASETYPES[FS Erweiterung C und D]':0,
    # 'CASETYPES[FS Verlängerung des Prüfauftrags]':0,
    # 'CASETYPES[FS Führerschein mit 17]':0,
    # 'CASETYPES[FS Umtausch in Kartenführerschein]':0,
    # 'CASETYPES[FS Abnutzung, Namensänderung]':0,
    # 'CASETYPES[FS Ersatzführerschein]':0,
    # 'CASETYPES[FS Karteikartenabschnitt]':0,
    # 'CASETYPES[FS Internationaler FS beantragen]':0,
    # 'CASETYPES[FS Umschreibung EU EWR FS beantragen]':0,
    # 'CASETYPES[FS Verlängerung der Fahrberechtigung bei befristetem Aufenthalt]':0,
    # 'CASETYPES[FS Verlängerung C- D-Klasse]':0,
    # 'CASETYPES[FS Eintragung BKFQ ohne Verlängerung]':0,
    # 'CASETYPES[FS Fahrerlaubnis nach Entzug]':0,
    # 'CASETYPES[FS Zuerkennung der ausländischen Fahrerlaubnis]':0,
    # 'CASETYPES[FS PBS für Taxi etc beantragen]':0,
    # 'CASETYPES[FS PBS verlängern]':0,
    # 'CASETYPES[FS Ersatz PBS]':0,
    # 'CASETYPES[FS Dienstführerschein umschreiben]':0,
    # 'CASETYPES[FS Internationaler FS bei Besitz]':0,
    # 'CASETYPES[FS Abholung Führerschein]':0,
    # 'CASETYPES[FS Auskünfte lfd Antrag allgemein]':0,
    # 'CASETYPES[FS Auskünfte lfd Antrag Begutachtung]':0,
    # 'CASETYPES[FS Auskünfte lfd Antrag Betäubungsmittel]':0,
    # 'CASETYPES[FS Auskunft zur Entziehung des Führerscheins]':0,
    # 'CASETYPES[FS Anmeldung und Vereinbarung Prüftermin]':0,
    # 'CASETYPES[FS Allgemeine Information zur Ortskundeprüfung]':0,
    # 'CASETYPES[FS Besprechung des Prüfungsergebnisses]':0,
    # 'CASETYPES[FS Beratung Fahreignung]':0,

    # Session is required to keep cookies between requests
    s = requests.Session()
    # First request to get and save cookies
    s.post(TERMIN_URL)

    termin_data = {
        'CASETYPES[%s]' % termin_type: 1,
        'step': 'WEB_APPOINT_SEARCH_BY_CASETYPES',
    }
    response = s.post(TERMIN_URL, termin_data)
    txt = response.text

    try:
        json_str = re.search('jsonAppoints = \'(.*?)\'', txt).group(1)
    except AttributeError:
        print('ERROR: cannot find termins data in server\'s response. See log.txt for raw text')
        write_response_to_log(txt)
        return None

    appointments = json.loads(json_str)

    if len(appointments) != 1:
        print('ERROR: termins json is malformed. See log.txt for json data')
        write_response_to_log(str(appointments))
        return None

    try:
        for key in appointments:
            appointments = appointments[key]['appoints']
    except TypeError:
        print('ERROR: termins json is malformed. See log.txt for json data')
        write_response_to_log(str(appointments))
        return None

    return appointments


if __name__ == '__main__':
    appointments = get_termins()
    if appointments:
        print(json.dumps(appointments, sort_keys=True, indent=4, separators=(',', ': ')))
