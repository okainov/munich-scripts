# -*- coding: utf-8 -*-
import os

import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.conversationhandler import ConversationHandler

import job_storage
import utils
from handlers import main_handler, termin_type_handler, quering_termins_handler, interval_handler, stat_handler
from metrics import MetricCollector
from states import MAIN, SELECTING_TERMIN_TYPE, QUERING_TERMINS, SCHEDULE_APPOINTMENT, SELECT_INTERVAL
from utils import get_bot

BOT_TOKEN = os.getenv("TG_TOKEN")
DEBUG = True if os.getenv("DEBUG") else False

logger = utils.get_logger()
metric_collector = MetricCollector.get_collector()


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary

    updater = Updater(bot=get_bot(), use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', main_handler, pass_user_data=True),
                      CommandHandler('stats', stat_handler, pass_user_data=True)],

        states={
            MAIN: [CallbackQueryHandler(main_handler, pass_user_data=True)],
            SELECTING_TERMIN_TYPE: [CallbackQueryHandler(termin_type_handler, pass_user_data=True)],
            QUERING_TERMINS: [CallbackQueryHandler(quering_termins_handler, pass_user_data=True)],
            SCHEDULE_APPOINTMENT: [CallbackQueryHandler(interval_handler, pass_user_data=True)],
            SELECT_INTERVAL: [MessageHandler(Filters.text, interval_handler)],
        },

        fallbacks=[CommandHandler('start', main_handler)],
        allow_reentry=True
    )
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    job_storage.init_scheduler()

    # Start the Bot
    if DEBUG:
        logger.info('Starting bot in debug polling mode')
        updater.start_polling()
        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()
    else:
        logger.info('Starting bot in production webhook mode')
        HOST_URL = os.environ.get("HOST_URL")
        if HOST_URL is None:
            logger.critical('HOST URL is not set!')
            sys.exit(-1)
        updater.start_webhook(listen="0.0.0.0",
                              port='8443',
                              url_path=BOT_TOKEN)
        updater.bot.set_webhook("https://{}/{}".format(HOST_URL, BOT_TOKEN))
        # heroku makes the app sleep after an hour of no incoming requests, so we will ping our app every 20 minutes


if __name__ == '__main__':
    main()
