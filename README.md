# General
Some useful scripts simplifying bureaucracy, especially when living in Munich, Germany.

# termin.py
Small tool to show availability of appointments in different Departments of Munich.

Available departments are:
- Ausländerbehörde (foreign nationals affairs, residence permits, work visas etc.)
- Bürgerbüro (civil affairs, residence registration etc.)
- Führerscheinstelle (driver license and motor vehicles affairs)


Please note the script **does not perform appointment booking** (see [#4](https://github.com/okainov/munich-scripts/issues/4)), it just tells you current status and allow you to subscribe to a notifier for one week.

## Telegram bot

There is a Telegram bot at [@MunichTerminBot](https://t.me/MunichTerminBot) using `termin.py` functionality. The bot is written using [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library. Source code is also in this repo, `tg_bot.py`.

### Development

By default bot runs as webhook configured for Heroku. For local development it's easier to use polling. In order to get it, just set `DEBUG = True` in one of first lines of the script.

### Bot deployment

Bot is hosted on Heroku, running in Docker and automatic deploy from `master` branch of this repo is set, no action should be required.

#### Manual deployment

Similar to one of basic [manuals](https://medium.com/python4you/creating-telegram-bot-and-deploying-it-on-heroku-471de1d96554). 

Pre-requisites:
 
 - Heroku CLI installed.
 - `TG_TOKEN` environment variable is set in Heroku settings
 - `HEROKU_APP_NAME` environment variable is set in Heroku settings.

 If you want to enable Elastic statistics, then additionally set following variables:

 - `ELASTIC_HOST` - hostname where ELK stack is deployed
 - `ELASTIC_USER` - ElasticSearch username
 - `ELASTIC_PASS` - ElasticSearch password

 Alternatively, you can disable metrics collection by setting `COLLECT_METRICS` to `False`

Commands for manual deploy

    heroku login
    heroku container:login
    heroku container:push --app munich-termin-bot web
    heroku container:release --app munich-termin-bot web
    
Shortly after deploy make sure everything is running

    heroku logs --tail --app munich-termin-bot

## Script usage

Edit script content and select what type of appointments you actually need:

    appointments = get_termins(DMV, 'FS Umschreibung Ausländischer FS')
    # appointments = get_termins(CityHall, 'An- oder Ummeldung - Einzelperson')
    # appointments = get_termins(ForeignLabor, 'Niederlassungserlaubnis Blaue Karte EU')

Run the script

    python3 termin.py

Output will be printed in the console