from telegram import Update

import job_storage
import termin_api
import utils
from printers import print_termin_type_message, print_main_message, print_quering_message, print_subscribe_message, \
    print_stat_message
from states import MAIN, SELECTING_TERMIN_TYPE, QUERING_TERMINS, SELECT_INTERVAL


def remove_subscription_helper(update: Update, context):
    chat_id = str(update.effective_chat.id)
    job_storage.remove_subscription(chat_id)

    return main_helper(update, context)


def query_termins_helper(update: Update, context):
    print_quering_message(update, context)
    return QUERING_TERMINS


def main_helper(update: Update, context):
    print_main_message(update, context)
    return MAIN


def main_handler(update: Update, context):
    if update.callback_query:
        if update.callback_query.data == '_REUSE':
            # All data already stored in user_data and user asked to repeat
            return query_termins_helper(update, context)
        elif update.callback_query.data == '_STOP':
            return remove_subscription_helper(update, context)
        else:
            # All options out, but data is here - it's the name of the department
            try:
                department = getattr(termin_api, update.callback_query.data)
            except AttributeError:
                return main_helper(update, context)
            context.user_data['buro'] = department
            print_termin_type_message(update, context)
            return SELECTING_TERMIN_TYPE
    else:
        return main_helper(update, context)


def stat_handler(update: Update, context):
    print_stat_message(update, context)
    return main_helper(update, context)


def termin_type_handler(update: Update, context):
    if update.callback_query:
        department = context.user_data['buro']
        try:
            index = int(update.callback_query.data)
        except:
            return SELECTING_TERMIN_TYPE
        if index < 0:
            return SELECTING_TERMIN_TYPE
        termin_type_str = department.get_available_appointment_types()[index]
        context.user_data['termin_type'] = termin_type_str
        return query_termins_helper(update, context)
    else:
        print_termin_type_message(update, context)
        return SELECTING_TERMIN_TYPE


def quering_termins_handler(update: Update, context):
    if update.callback_query:
        if update.callback_query.data == 'return':
            return main_helper(update, context)

        elif update.callback_query.data == 'subscribe':
            print_subscribe_message(update, context)
            return SELECT_INTERVAL

        elif update.callback_query.data == '_STOP':
            return remove_subscription_helper(update, context)
    else:
        return query_termins_helper(update, context)


def interval_handler(update: Update, context):
    """
    Schedules a job for user which will check available appointments by interval
    """

    MIN_CHECK_INTERVAL_MINUTES = utils.get_min_interval()

    msg = update.message
    minutes = update.message.text

    # check interval at least MIN_CHECK_INTERVAL mins
    valid_interval = True
    try:
        if int(minutes) < MIN_CHECK_INTERVAL_MINUTES:
            valid_interval = False
    except ValueError:
        valid_interval = False

    if not valid_interval:
        msg.reply_text(f'Interval should be greater or equals than {MIN_CHECK_INTERVAL_MINUTES} minutes')
        return SELECT_INTERVAL

    chat_id = str(update.effective_chat.id)

    subsciption_present = job_storage.get_job(chat_id)

    # User cannot have two or more subscriptions
    if subsciption_present:
        msg.reply_text(
            '⚠️ You had some subscription already. In order to activate the new check, I have removed the old one.')
        job_storage.remove_subscription(chat_id)

    job_storage.add_subscription(update, context, interval=int(minutes))

    msg.reply_text(f"Ok, I've started subscription with checking interval {minutes} minutes\n"
                   "I will notify you if something is available\n"
                   "Please note the subscription will be automatically removed after one week "
                   "if not cancelled manually before")

    return main_helper(update, context)
