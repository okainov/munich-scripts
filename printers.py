import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message

import utils
import worker
import job_storage
from termin_api import Buro


def get_msg(update: Update) -> Message:
    """
    Gets `Message` object which can be used for answers.
    It is needed because way to get Message is different for callback updates and normal updates
    :param update: Update
    :return: Message
    """
    if update.message:
        return update.message
    else:
        return update.callback_query.message


def print_subscription_status(update, context):
    msg = get_msg(update)

    chat_id = str(update.effective_chat.id)
    subscription = job_storage.get_job(chat_id)

    if subscription:
        subscription_limit = subscription.kwargs['created_at'] + datetime.timedelta(days=7)
        date_object = subscription_limit.strftime("%d-%m-%Y %H:%M:%S")

        department = Buro.get_buro_by_id(subscription.kwargs['buro'])
        msg.reply_text(
            'Current subscription details:\n\n - Department: %s \n - Type: %s \n - Interval: %s \n - Until: %s \n' % (
                department.get_name(), subscription.kwargs['termin'], subscription.trigger.interval, date_object))
        print_unsubscribe_button(chat_id)


def notify_about_termins(chat_id, buro, termin, created_at):
    """
    Checks for available termins and prints them if any
    """

    department = Buro.get_buro_by_id(buro)

    if department is None:
        return

    bot = utils.get_bot()

    appointments = worker.get_available_appointments(department, termin, user_id=str(chat_id))

    if appointments is None:
        bot.send_message(chat_id=chat_id,
                         text=f'Seems like appointment title <{termin}> is not accepted by the buro <%s> any more\n'
                              'Please create issue on Github (https://github.com/okainov/munich-scripts/issues/new)'
                              % department.get_name())

    if len(appointments) > 0:
        for caption, date, time in appointments:
            bot.send_message(chat_id=chat_id, text='The nearest appointments at %s are on %s:\n%s' % (
                caption, date, '\n'.join(time)))
        bot.send_message(chat_id=chat_id, text='Please book your appointment here: %s' % department.get_frame_url())
        print_unsubscribe_button(chat_id)


def print_subscription_status_for_termin(update, context):
    msg = get_msg(update)

    chat_id = str(update.effective_chat.id)
    termin = context.user_data['termin_type']
    subscription = job_storage.get_job(chat_id)

    if subscription and subscription.kwargs['termin'] == termin:
        subscription_limit = subscription.kwargs['created_at'] + datetime.timedelta(days=7)
        date_object = subscription_limit.strftime("%d-%m-%Y")

        msg.reply_text(
            'Subscription with interval %sm is already active until %s \n' % (
                subscription.trigger.interval, date_object))
        print_unsubscribe_button(chat_id)
    else:
        buttons = [InlineKeyboardButton(text="Subscribe", callback_data="subscribe")]
        custom_keyboard = [buttons]
        msg.reply_text(
            'If you want, you can subscribe for available appointments of this type. '
            'After then you will receive regular updates about available appointments for a week',
            reply_markup=InlineKeyboardMarkup(custom_keyboard, one_time_keyboard=True))


def print_main_message(update, context):
    deps = Buro.__subclasses__()

    MAX_BURO_IN_ROW = 2
    custom_keyboard = []
    buttons = []
    for i, dep in enumerate(deps):
        buttons.append(InlineKeyboardButton(text=dep.get_name(), callback_data=dep.__name__))
        if i % MAX_BURO_IN_ROW == MAX_BURO_IN_ROW - 1:
            custom_keyboard.append(buttons)
            buttons = []
    if buttons:
        custom_keyboard.append(buttons)

    if 'buro' in context.user_data and 'termin_type' in context.user_data:
        custom_keyboard.append([InlineKeyboardButton(text='Reuse last selection', callback_data='_REUSE')])

    msg = get_msg(update)

    msg.reply_text(
        'Here are available departments. Please select one:',
        reply_markup=InlineKeyboardMarkup(custom_keyboard, one_time_keyboard=True))

    print_subscription_status(update, context)


def print_stat_message(update, context):
    chat_id = update.effective_chat.id
    utils.get_logger().info(f'[{chat_id}] Displaying statistics', extra={'user': chat_id})

    msg = get_msg(update)
    all_jobs = [x for x in job_storage.get_jobs() if 'chat_id' in x.kwargs]
    average_interval = sum([x.trigger.interval.seconds for x in all_jobs]) / 60 / len(all_jobs)

    termin_list = [x.kwargs['termin'] for x in all_jobs]
    most_popular_termin = max(set(termin_list), key=lambda x: termin_list.count(x))

    msg.reply_text(f'ℹ️ Some piece of statistics:\n\n'
                   f'{len(all_jobs)} active subscription(s)\n'
                   f'{average_interval} min average interval\n'
                   f'{most_popular_termin} is the most popular termin')


def print_termin_type_message(update, context):
    buttons = []
    msg = get_msg(update)

    department = context.user_data['buro']

    msg.reply_text(
        'Fetching available appointment types...')
    for i, x in department.get_typical_appointments():
        buttons.append([InlineKeyboardButton(text=x, callback_data=i)])
    if department.get_typical_appointments():
        buttons.append([InlineKeyboardButton(text='--------------', callback_data='-1')])

    for i, x in enumerate(department.get_available_appointment_types()):
        buttons.append([InlineKeyboardButton(text=x, callback_data=i)])

    msg.reply_text(
        'There are several appointment types available. Most used types are on top. Please select one',
        reply_markup=InlineKeyboardMarkup(buttons, one_time_keyboard=True))


def print_quering_message(update, context):
    msg = get_msg(update)

    termin_type_str = context.user_data['termin_type']

    msg.reply_text(
        'Great, wait a second while I\'m fetching available appointments for %s...' % termin_type_str)

    print_available_termins(update, context, print_if_none=True)

    buttons = [InlineKeyboardButton(text="Return back", callback_data="return")]
    custom_keyboard = [buttons]

    msg.reply_text(
        text='Or just return to the main selection',
        reply_markup=InlineKeyboardMarkup(custom_keyboard, one_time_keyboard=True))


def print_available_termins(update, context, print_if_none=False):
    """
    Checks for available termins and prints them if any
    """
    department = context.user_data['buro']
    termin_type_str = context.user_data['termin_type']

    msg = get_msg(update)

    appointments = worker.get_available_appointments(department, termin_type_str, user_id=str(update.effective_chat.id))

    if appointments is None:
        msg.reply_text(
            'Seems like appointment title <%s> is not accepted by the buro <%s> any more\nPlease create issue on Github'
            ' (https://github.com/okainov/munich-scripts/issues/new)' % (
                termin_type_str, department))

    if len(appointments) > 0:
        for caption, date, time in appointments:
            msg.reply_text('The nearest appointments at %s are on %s:\n%s' % (
                caption, date, '\n'.join(time)))
        msg.reply_text('Please book your appointment here: %s' % department.get_frame_url())
        print_subscription_status_for_termin(update, context)
    elif print_if_none:
        msg.reply_text('Unfortunately, everything is booked. Please come back in several days :(')
        print_subscription_status_for_termin(update, context)


def print_unsubscribe_button(chat_id):
    buttons = [InlineKeyboardButton(text="Unsubscribe", callback_data="_STOP")]
    custom_keyboard = [buttons]
    utils.get_bot().send_message(chat_id,
                                 'To unsubscribe click the button',
                                 reply_markup=InlineKeyboardMarkup(custom_keyboard, one_time_keyboard=True))


def print_subscribe_message(update, context):
    msg = get_msg(update)
    MIN_CHECK_INTERVAL_MINUTES = utils.get_min_interval()
    msg.reply_text(
        f'Please type interval in minutes. Interval should greater or equal than {MIN_CHECK_INTERVAL_MINUTES} minutes.')
