# -*- coding: utf-8 -*-
import datetime
import logging
import os

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.utils.request import Request

import termin
from metrics import MetricCollector

BOT_TOKEN = os.getenv("TG_TOKEN")
MIN_CHECK_INTERVAL = 15

DEBUG = False
COLLECT_METRICS = not DEBUG

# Enable logging
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

metric_collector = MetricCollector(os.getenv('ELASTIC_HOST'), os.getenv('ELASTIC_USER'), os.getenv('ELASTIC_PASS'),
                                   debug_mode=not COLLECT_METRICS)

SELECTING_TERMIN_TYPE, QUERING_TERMINS, SCHEDULE_APPOINTMENT, SELECT_INTERVAL, STOP_CHECKING = range(5)

scheduler = BackgroundScheduler()
scheduled_jobs = {}


def selecting_buro(update, context):
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
        'Hi! Here are available departments. Please select one:',
        reply_markup=InlineKeyboardMarkup(custom_keyboard, one_time_keyboard=True))

    print_subscription_status(update, context)

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
        try:
            department = getattr(termin, update.callback_query.data)
        except AttributeError:
            return SELECTING_TERMIN_TYPE
        context.user_data['buro'] = department

    buttons = []

    for i, x in department.get_typical_appointments():
        buttons.append([InlineKeyboardButton(text=x, callback_data=i)])
    if department.get_typical_appointments():
        buttons.append([InlineKeyboardButton(text='--------------', callback_data='-1')])

    for i, x in enumerate(department.get_available_appointment_types()):
        buttons.append([InlineKeyboardButton(text=x, callback_data=i)])

    msg.reply_text(
        'There are several appointment types available. Most used types are on top. Please select one',
        reply_markup=InlineKeyboardMarkup(buttons, one_time_keyboard=True))

    return QUERING_TERMINS


def quering_termins(update, context, reuse=False):
    department = context.user_data['buro']

    if not reuse:
        index = int(update.callback_query.data)
        if index < 0:
            return QUERING_TERMINS
        msg = update.callback_query.message
        termin_type_str = department.get_available_appointment_types()[index]
        context.user_data['termin_type'] = termin_type_str
    else:
        msg = update.callback_query.message
        termin_type_str = context.user_data['termin_type']

    msg.reply_text(
        'Great, wait a second while I\'m fetching available appointments for %s...' % termin_type_str)

    metric_collector.log_search(user=update.effective_user.id, buro=department, appointment=termin_type_str)

    appointments = get_available_appointments(department, termin_type_str)

    if len(appointments) > 0:
        for caption, date, time in appointments:
            msg.reply_text('The nearest appointments at %s are on %s:\n%s' % (
                caption, date, '\n'.join(time)))
        msg.reply_text('Please book your appointment here: %s' % department._get_base_page())
    else:
        msg.reply_text('Unfortunately, everything is booked. Please come back in several days :(')

    buttons = [InlineKeyboardButton(text="Subscribe", callback_data="subscribe"),
               InlineKeyboardButton(text="No, return back", callback_data="return")]
    custom_keyboard = [buttons]

    msg.reply_text(
        'If you want, you can subscribe for available appointments of this type. '
        'After then you will receive regular updates about available appointments for a week',
        reply_markup=InlineKeyboardMarkup(custom_keyboard, one_time_keyboard=True))

    return SCHEDULE_APPOINTMENT


def get_available_appointments(department, termin_type):
    logger.info('Query for <%s> at %s' % (termin_type, department))

    appointments = termin.get_termins(department, termin_type)

    # list of tuples: (caption, date, time)
    available_appointments = []
    for k, v in appointments.items():
        caption = v['caption']
        first_date = None
        for date in v['appoints']:
            if v['appoints'][date]:
                first_date = date

                next_in = (datetime.datetime.strptime(first_date, '%Y-%m-%d').date() - datetime.date.today()).days
                logger.info('Soonest appt at %s is %s days from today' % (caption, next_in))
                metric_collector.log_result(department, caption, termin_type, next_in, amount=len(v['appoints'][date]))

                break

        if first_date:
            available_appointments.append((caption, first_date, v['appoints'][first_date]))

    if not available_appointments:
        logger.info('Nothing found')
        metric_collector.log_result(department, place="", appointment=termin_type)

    return available_appointments


def set_retry_interval(update, context):
    if update.callback_query and update.callback_query.data == 'return':
        return selecting_buro(update, context)
    elif update.callback_query and update.callback_query.data.isnumeric():
        # User clicked on some termin from the previous message, need to redirect
        department = context.user_data['buro']
        termin_type_str = department.get_available_appointment_types()[int(update.callback_query.data)]
        context.user_data['termin_type'] = termin_type_str
        return quering_termins(update, context, True)
    else:
        msg = update.callback_query.message if update.callback_query else update.message
        msg.reply_text(
            f'Please type interval in minutes. Interval should greater or equal than {MIN_CHECK_INTERVAL} minutes.')
        return SELECT_INTERVAL


def print_available_termins(update, context):
    """
    Checks for available termins and prints them if any
    """
    department = context.user_data['buro']
    termin_type_str = context.user_data['termin_type']

    msg = update.message

    appointments = get_available_appointments(department, termin_type_str)
    if len(appointments) > 0:
        for caption, date, time in appointments:
            msg.reply_text('The nearest appointments at %s are on %s:\n%s' % (
                caption, date, '\n'.join(time)))
        msg.reply_text('Please book your appointment here: %s' % department._get_base_page())
        # something was found, print unsubscribe button
        print_unsubscribe_button(msg)


def start_interval_checking(update: Update, context):
    """
    Schedules a job for user which will check available appointments by interval
    """
    msg = update.message
    minutes = update.message.text

    # check interval at least MIN_CHECK_INTERVAL mins
    valid_interval = True
    try:
        if int(minutes) < MIN_CHECK_INTERVAL:
            valid_interval = False
    except ValueError:
        valid_interval = False

    if not valid_interval:
        msg.reply_text(f'Interval should be greater or equals than {MIN_CHECK_INTERVAL} minutes')
        return set_retry_interval(update, context)

    chat_id = str(update.effective_chat.id)

    # User cannot have two or more subscriptions
    if chat_id in scheduled_jobs:
        msg.reply_text(
            '⚠️ You had some subscription already. In order to activate the new check, I have removed the old one.')
        remove_job(chat_id)

    scheduler.add_job(print_available_termins, 'interval', (update, context), minutes=int(minutes), id=chat_id)
    scheduled_jobs[chat_id] = datetime.datetime.now()

    logger.info('Subscription for %s-%s created with interval %s' % (
        context.user_data['buro'], context.user_data['termin_type'], minutes))
    metric_collector.log_subscription(buro=context.user_data['buro'], appointment=context.user_data['termin_type'],
                                      interval=minutes, user=int(chat_id))

    msg.reply_text(f"Ok, I've started subscription with checking interval {minutes} minutes\n"
                   "I will notify you if something is available")

    print_subscription_status(update, context)

    msg.reply_text("Please note the subscription will be automatically removed after one week "
                   "if not cancelled manually before")

    print_unsubscribe_button(msg)

    return STOP_CHECKING


def print_unsubscribe_button(msg):
    buttons = [InlineKeyboardButton(text="Unsubscribe", callback_data="stop")]
    custom_keyboard = [buttons]
    msg.reply_text(
        'To unsubscribe click the button',
        reply_markup=InlineKeyboardMarkup(custom_keyboard, one_time_keyboard=True))


def print_subscription_status(update, context):
    """
    Prints current subscription status
    """

    chat_id = str(update.effective_chat.id)
    msg = update.message

    # check if exists a scheduled job
    if chat_id not in scheduled_jobs:
        return

    # define subscription limit 
    subscription_limit = scheduled_jobs[chat_id].date() + datetime.timedelta(days=7)

    # format date 
    date_object = subscription_limit.strftime("%d-%m-%Y")

    # send subscription details message
    msg.reply_text('Current subscription details:\n\n - Department: %s \n\n - Type: %s \n\n - Until: %s \n' % (
        context.user_data['buro'], context.user_data['termin_type'], date_object))

    return


def stop_checking(update, context):
    chat_id = str(update.effective_chat.id)
    remove_job(chat_id)
    return selecting_buro(update, context)


def remove_job(chat_id: str):
    # if user does not have a subscription, we want to avoid an error
    if chat_id in scheduled_jobs.keys():
        scheduled_jobs.pop(chat_id, None)
        get_bot().send_message(chat_id=chat_id, text='You were unsubscribed successfully')

        scheduler.remove_job(chat_id)


def ping_myself_and_clear_jobs(app_name):
    url = "https://{}.herokuapp.com/".format(app_name)
    logger.info("Pinging myself at " + str(url))
    requests.request('get', url)

    # remove jobs scheduled more than a week ago
    to_remove = list(k for k, v in scheduled_jobs.items() if (datetime.datetime.now() - v).days >= 7)
    for chat_id in to_remove:
        remove_job(chat_id)
        logger.info('Job for chat "%s" removed since it was scheduled more than a week ago', chat_id)


def get_bot():
    # Default size from the library, 4 workers + 4 additional
    request = Request(con_pool_size=8)
    return Bot(token=BOT_TOKEN, request=request)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary

    updater = Updater(bot=get_bot(), use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', selecting_buro, pass_user_data=True)],

        states={
            SELECTING_TERMIN_TYPE: [CallbackQueryHandler(select_termin_type, pass_user_data=True)],
            QUERING_TERMINS: [CallbackQueryHandler(quering_termins, pass_user_data=True)],
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
