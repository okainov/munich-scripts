# -*- coding: utf-8 -*-
import logging
import os
import requests
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup

import termin

BOT_TOKEN = os.getenv("TG_TOKEN")
DEBUG = False

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

SELECTING_TERMIN_TYPE, QUERING_TERMINS, SCHEDULE_APPOINTMENT, SELECT_INTERVAL, STOP_CHECKING = range(5)

scheduler = BackgroundScheduler()
scheduled_jobs = {}


def selecting_buro(update, context):
    # remove scheduled job for user when restarting bot
    user_id = str(update.effective_user.id)
    remove_job(user_id)

    buttons = []
    deps = termin.Buro.__subclasses__()
    for dep in deps:
        buttons.append(InlineKeyboardButton(text=dep.get_name(), callback_data=dep.__name__))
    custom_keyboard = [buttons]

    if 'buro' in context.user_data and 'termin_type' in context.user_data:
        custom_keyboard.append([InlineKeyboardButton(text='Reuse last selection', callback_data='_REUSE')])

    if update.message:
        msg = update.message
    else:
        msg = update.callback_query.message

    msg.reply_text(
        'Hi! Here are available departments. Please select one',
        reply_markup=InlineKeyboardMarkup(custom_keyboard, one_time_keyboard=True))

    return SELECTING_TERMIN_TYPE


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def select_termin_type(update, context):
    if update.callback_query and update.callback_query.data == '_REUSE':
        # All data already stored in user_data and user asked to repeat
        return quering_termins(update, context, True)
    elif not update.callback_query:
        # We returned from previous step, but buro is already known
        department = context.user_data['buro']
        msg = update.message
    else:
        msg = update.callback_query.message
        department = getattr(termin, update.callback_query.data)
        context.user_data['buro'] = department

    app_types = department.get_available_appointment_types()

    msg.reply_text(
        'There are several appointment types available. Please send the number of the desired appointment:\n%s' % '\n'.join(
            ['%s: %s' % (i, x) for i, x in enumerate(app_types, 1)]))

    return QUERING_TERMINS


def quering_termins(update, context, reuse=False):
    department = context.user_data['buro']
    if not reuse:
        msg = update.message
        try:
            termin_type_str = department.get_available_appointment_types()[int(update.message.text) - 1]
        except IndexError:
            msg.reply_text(
                'Looks like invalid number, please try again')
            return select_termin_type(update, context)
        context.user_data['termin_type'] = termin_type_str
    else:
        msg = update.callback_query.message
        termin_type_str = context.user_data['termin_type']

    msg.reply_text(
        'Great, wait a second while I\'m fetching available appointments for %s...' % termin_type_str)

    appointments = termin.get_termins(department, termin_type_str)

    found_any = False
    for k, v in appointments.items():
        caption = v['caption']
        first_date = None
        for date in v['appoints']:
            if v['appoints'][date]:
                first_date = date
                found_any = True
                break

        if first_date:
            msg.reply_text('The nearest appointments at %s are at %s:\n%s' % (
                caption, first_date, '\n'.join(v['appoints'][first_date])))

    if not found_any:
        msg.reply_text('Unfortunately, everything is booked. Please come back in several days :(')

    buttons = [InlineKeyboardButton(text="Schedule", callback_data="schedule"),
               InlineKeyboardButton(text="No, return back", callback_data="return")]
    custom_keyboard = [buttons]

    msg.reply_text(
        'If you want, you can schedule checking appointments of this type by interval',
        reply_markup=InlineKeyboardMarkup(custom_keyboard, one_time_keyboard=True))

    return SCHEDULE_APPOINTMENT


def set_retry_interval(update, context):
    if update.callback_query and update.callback_query.data == 'return':
        return selecting_buro(update, context)
    else:
        msg = update.callback_query.message if update.callback_query else update.message
        msg.reply_text('Please type interval in minutes. Interval should greater or equals 15 minutes.')
        return SELECT_INTERVAL


def print_available_termins(update, context):
    """
    Checks for available termins and prints them if any
    """
    department = context.user_data['buro']
    termin_type_str = context.user_data['termin_type']

    msg = update.message

    appointments = termin.get_termins(department, termin_type_str)
    found_any = False
    for k, v in appointments.items():
        for date in v['appoints']:
            if v['appoints'][date]:
                found_any = True
                msg.reply_text('Available appointments on date %s are %s' % (date, '\n'.join(v['appoints'][date])))

    # smth was found, print unsubscribe button
    if found_any:
        print_unsubscribe_button(msg)


def start_interval_checking(update, context):
    """
    Schedules a job for user which will check available appointments by interval
    """
    msg = update.message
    minutes = update.message.text

    # check interval at least 15 mins
    valid_interval = True
    try:
        if int(minutes) < 15:
            valid_interval = False
    except ValueError:
        valid_interval = False

    if not valid_interval:
        msg.reply_text('Interval should be greater or equals 15 minutes')
        return set_retry_interval(update, context)

    user_id = str(update.effective_user.id)

    scheduler.add_job(print_available_termins, 'interval', (update, context), minutes=int(minutes), id=user_id)
    scheduled_jobs[user_id] = datetime.now()

    msg.reply_text("Ok, I've started continuous checking with interval " + minutes + " minutes")
    msg.reply_text("I will notify you if something is available")

    print_unsubscribe_button(msg)

    return STOP_CHECKING


def print_unsubscribe_button(msg):
    buttons = [InlineKeyboardButton(text="Unsubscribe", callback_data="stop")]
    custom_keyboard = [buttons]
    msg.reply_text(
        'You can stop checking',
        reply_markup=InlineKeyboardMarkup(custom_keyboard, one_time_keyboard=True))


def stop_checking(update, context):
    user_id = str(update.effective_user.id)
    remove_job(user_id)
    return selecting_buro(update, context)


def remove_job(user_id):
    # if user does not have a subscription, we want to avoid an error
    if user_id in scheduled_jobs.keys():
        scheduled_jobs.pop(user_id, None)
        scheduler.remove_job(user_id)


def ping_myself_and_clear_jobs(app_name):
    url = "https://{}.herokuapp.com/".format(app_name)
    logger.info("Pinging myself at " + str(url))
    requests.request('get', url)

    # remove jobs scheduled more than a week ago
    to_remove = list(k for k, v in scheduled_jobs.items() if (datetime.now() - v).days >= 7)
    for user_id in to_remove:
        remove_job(user_id)
        logger.info('Job for user "%s" removed since it was scheduled more than a week ago', user_id)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', selecting_buro, pass_user_data=True)],

        states={
            SELECTING_TERMIN_TYPE: [CallbackQueryHandler(select_termin_type, pass_user_data=True)],
            QUERING_TERMINS: [MessageHandler(Filters.text, quering_termins)],
            SCHEDULE_APPOINTMENT: [CallbackQueryHandler(set_retry_interval, pass_user_data=True)],
            SELECT_INTERVAL: [MessageHandler(Filters.text, start_interval_checking)],
            STOP_CHECKING: [CallbackQueryHandler(stop_checking, pass_user_data=True)]
        },

        fallbacks=[CommandHandler('start', selecting_buro)],
        allow_reentry=True
    )
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    # scheduler for checking appointments with interval
    scheduler.start()

    # Start the Bot
    if DEBUG:
        updater.start_polling()
        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()
    else:
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=BOT_TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, BOT_TOKEN))
        # heroku makes the app sleep after an hour of no incoming requests, so we will ping our app every 20 minutes
        scheduler.add_job(ping_myself_and_clear_jobs, "interval", args=[HEROKU_APP_NAME], minutes=20, id="ping")


if __name__ == '__main__':
    main()