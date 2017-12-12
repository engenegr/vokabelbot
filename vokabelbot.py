import os
import logging
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import pydeepl
from configparser import ConfigParser

from models.base import Base
from models.user import User
from models.translator import Translator
from models.base import session


# =============================================================================
# Init
# =============================================================================

# Config and Logging
cfg = ConfigParser()
cfg.read('settings.ini')
debug = cfg.getboolean('general', 'debug', fallback=False)
loglevel = logging.WARNING
if debug: loglevel = logging.DEBUG
logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s',
                    level=loglevel, filename='error.log')

# Telegram Bot
updater = telegram.ext.Updater(token=cfg.get('general', 'token'))
dispatcher = updater.dispatcher

# =============================================================================
# Helper Functions
# =============================================================================


def create_user(update):
    """ Create a new user from a telegram update object and add it to the db.
    Returns object of the User model.
    """
    print('creating')
    user = User()
    user.chat_id = update.message.chat.id
    print('id set')
    user.name = update.message.chat.first_name
    print('name set')
    session.add(user)  # cashes data for db
    print('added')
    # Care if commit does not work no error is raised it just stops there
    session.commit()  # writes all cached data to file
    print('creating done')
    return user


def get_user(update):
    """ Takes the telegram update and returns the user model from database.
    If it doesnt exists it creates a new one. Returns a User model object.
    """
    print('start get')
    chat_id = update.message.chat.id  # get id from telegram-update
    # session appears everywhere since its imported
    users = session.query(User).filter(User.chat_id == chat_id).all()
    print('query done')
    if len(users) == 0:  # if no user exists create a new from update
        print('no user.. creating')
        logging.warning('Msg from Unregistred User, creating new db entry.')
        user = create_user(update)
    elif len(users) == 1:  # if a user is found return it
        print('match')
        user = users[0]
    else: 
        print('problem')
        logging.error('Found multiple users with chat_id: {}'.format(chat_id))
        error_contact_string = """If this problem persists contact a developer: 
            telebotter@sarbot.de"""
        error_msg = """I'm sorry something went wrong with your user id. """
        update.message.reply_text(error_msg + error_contact_string)
        user = None
    return user


def translate(text, user):
    """ Takes a string and tries to find the correct translation direction
    between the two languages. If both give results, both are printed.
    It uses the translation engine specified in the users preferences.
    """
    print('starting')
    # TODO: move the translate functions to the translator classes/objects
    # somehow and select it from user settings
    lan1 = user.lan1.upper()
    lan2 = user.lan2.upper()  # 'DE', 'EN' ...
    trans1 = pydeepl.translate(text, lan1, lan2)
    trans2 = pydeepl.translate(text, lan2, lan1)
    # TODO: logic depends on user.direction
    user.count += 1
    session.add(user)
    session.commit()
    if user.direction == 1:
        return [trans1]
    elif user.direction == 2:
        return [trans2]
    else:  # auto
        if trans1.lower() == text.lower() and trans2.lower() != text.lower():
            return [trans2]
        if trans1.lower() != text.lower() and trans2.lower() == text.lower():
            return [trans1]
        else:
            return [trans1, trans2]


# =============================================================================
# Handled
# =============================================================================


def send_translation(bot, update):
    user = get_user(update)  # or just chat_id?
    trans = translate(update.message.text, user)
    # translation='bo'
    # todo if user.confirm add 2 buttons (or three in double case)
    print('got')
    if len(trans) == 1:
        answer = trans[0]
    else:
        answer = user.lan1 + ': ' + trans[0]+'\n' + user.lan2+':' + trans[1]
    update.message.reply_text(answer)


dispatcher.add_handler(MessageHandler(Filters.text, send_translation))
print('starting bot')
updater.start_polling()
updater.idle()
