# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
<Ask for language>
Provide list of Buros, ask for buro
provide list of services, ask for service
Reply with list of appointments

"""

import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup

import termin

BOT_TOKEN = 'INSERT_TOKEN'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(update, context):
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

    return BURO


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


BURO, TERMIN_TYPE = range(2)


def buro(update, context):
    if update.callback_query and update.callback_query.data == '_REUSE':
        # All data already stored in user_data and user asked to repeat
        return termin_type(update, context, True)
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

    return TERMIN_TYPE


def termin_type(update, context, reuse=False):
    department = context.user_data['buro']
    if not reuse:
        msg = update.message
        try:
            termin_type_str = department.get_available_appointment_types()[int(update.message.text) - 1]
        except IndexError:
            msg.reply_text(
                'Looks like invalid number, please try again')
            return buro(update, context)
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

    return start(update, context)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_user_data=True)],

        states={
            BURO: [CallbackQueryHandler(buro, pass_user_data=True)],
            TERMIN_TYPE: [MessageHandler(Filters.text, termin_type)],
        },

        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True
    )
    dp.add_handler(conv_handler)

    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
