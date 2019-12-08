# General
Some useful scripts simplifying bureaucracy, especially when living in Munich, Germany.

# termin.py
Small tool to show availability of appointments in different Departments of Munich.

Available departments are:
- [Ausländerbehörde](https://www.muenchen.de/rathaus/Stadtverwaltung/Kreisverwaltungsreferat/Auslaenderwesen.html) (foreign nationals affairs, residence permits, work visas etc.)
- [Bürgerbüro](https://www.muenchen.de/rathaus/Stadtverwaltung/Kreisverwaltungsreferat/Buergerbuero.html) (civil affairs, residence registration etc.)
- [Führerscheinstelle](https://www.muenchen.de/rathaus/Stadtverwaltung/Kreisverwaltungsreferat/Verkehr/Fuehrerschein.html) (driver license affairs)
- [Kfz-Zulassungstelle](https://www.muenchen.de/rathaus/Stadtverwaltung/Kreisverwaltungsreferat/Verkehr/KFZ-Zulassung.html) (motor vehicles affairs, registration, license plate and so on)
- [Versicherungsamt](https://www.muenchen.de/rathaus/Stadtverwaltung/Kreisverwaltungsreferat/Versicherungsamt.html) (Pension-related stuff, i.e. getting information about your contribution, necessary for NE)


Please note the script **does not perform appointment booking** (see [#4](https://github.com/okainov/munich-scripts/issues/4)), it just tells you current status and allows you to subscribe to a notifier for one week.

## Telegram bot

There is a Telegram bot at [@MunichTerminBot](https://t.me/MunichTerminBot) using `termin_api.py` functionality. The bot is written using [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library. Source code is also in this repo, `tg_bot.py`.

### Development

By default bot runs as webhook configured for personal web server. For local development it's easier to use polling. In order to get it, just set `DEBUG = True` in one of first lines of the script.

### Bot deployment

Bot is hosted on personal web server, running in Docker and automatic deploy from `master` branch of this repo is set, no action should be required.

#### Manual deployment

Pre-requisites:

 - `TG_TOKEN` environment variable is set in `.env` file

 If you want to enable Elastic statistics, then additionally set following variables to non-empty value:

 - `ELASTIC_HOST` - hostname where ELK stack is deployed
 - `ELASTIC_USER` - ElasticSearch username
 - `ELASTIC_PASS` - ElasticSearch password


Commands for manual deploy

    git pull
    docker-compose build
    docker-compose up -d
    
Shortly after deploy make sure everything is running

    docker-compose logs -f

## Script usage

Edit script content and select what type of appointments you actually need:

    appointments = get_termins(DMV, 'FS Umschreibung Ausländischer FS')
    # appointments = get_termins(CityHall, 'An- oder Ummeldung - Einzelperson')
    # appointments = get_termins(ForeignLabor, 'Niederlassungserlaubnis Blaue Karte EU')

Run the script

    python3 termin_api.py

Output will be printed in the console