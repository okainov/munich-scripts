# General
Some useful scripts simplifying bureaucracy, especially when living in Munich, Germany.

# termin.py
Small tool to show availability of appointments in different Departments of Munich.

Available departments are:
- Ausländerbehörde (foreign nationals affairs, residence permits, work visas etc.)
- Bürgerbüro (civil affairs, residence registration etc.)
- Führerscheinstelle (driver license and motor vehicles affairs)


Please note the script **does not perform appointment booking**, it just tells you current status, so you may run it with cron and\or add some custom notifier.


## Telegram bot

There is a simple Telegram bot at [@MunichTerminBot](https://t.me/MunichTerminBot) using `termin.py` functionality. The bot is written using [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library. Source code is also in this repo, `tg_bot.py`.

### Bot deployment

Bot is hosted on Heroku, runnning in Docker and can be deployed similar to one of [manuals](https://medium.com/python4you/creating-telegram-bot-and-deploying-it-on-heroku-471de1d96554). 

Pre-requisites:
 
 - Having Heroku CLI installed.
 - Having `TG_TOKEN` environment variable set up in Heroku app
 

    heroku login
    heroku container:login
    heroku container:push --app munich-termin-bot web
    heroku container:release --app munich-termin-bot web
    
Shortly after deploy make sure everything is running

    heroku logs --tail --app <HEROKU_APP_NAME>

## Script usage

Edit script content and select what type of appointments you actually need:

    appointments = get_termins(DMV, 'FS Umschreibung Ausländischer FS')
    # appointments = get_termins(CityHall, 'An- oder Ummeldung - Einzelperson')
    # appointments = get_termins(ForeignLabor, 'Niederlassungserlaubnis Blaue Karte EU')

Run the script

    python3 termin.py

Output will be printed in the console