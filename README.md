# General
Some useful scripts simplifying bureaucracy, especially when living in Munich, Germany.

# termin.py
Small tool to show availability of appointments in different Departments of Munich.

Available departments are:
- Ausländerbehörde (foreign nationals affairs, residence permits, work visas etc.)
- Bürgerbüro (civil affairs, residence registration etc.)
- Führerscheinstelle (driver license and motor vehicles affairs)


Please note the script **does not perform appointment booking**, it just tells you current status, so you may run it with cron and\or add some custom notifier.


## Usage

Edit script content and select what type of appointments you actually need:

    appointments = get_termins(DMV, 'FS Umschreibung Ausländischer FS')
    # appointments = get_termins(CityHall, 'An- oder Ummeldung - Einzelperson')
    # appointments = get_termins(ForeignLabor, 'Niederlassungserlaubnis Blaue Karte EU')

Run the script

    python3 termin.py

Output will be printed in the console