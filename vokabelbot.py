import os
import logging
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import pydeepl
import configparser

cfg = configparser.Configparser()
cfg.read('settings.ini')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
updater = telegram.ext.Updater(token=cfg.get('general','token'))
dispatcher = updater.dispatcher

msg_start = "*Hi*,\n Schick mir einfach ein Wort und ich versuche es zu übersetzen. \n \
Ich merk mir auch alles was du nachschlägst, damit du diese Wörter später üben kannst. \n \
Einstellungen erreichst du /prefs alle befehle mit /help"
msg_help = " \
/start - Startmeldung \n\
/help - Diese Hilfe anzeigen \n\
/train - Etwas Üben \n\
/stop - Übung beenden \n\
/pref - Einstellungen \n"
lan1 = 'DE'
lan2 = 'EN'


def auto_translate(text):
    trans1 = pydeepl.translate(text, lan1, lan2)
    trans2 = pydeepl.translate(text, lan2, lan1)
    if trans1.lower() == text.lower() and trans2.lower() != text.lower():
        return trans2
    if trans1.lower() != text.lower() and trans2.lower() == text.lower():
        return trans1
    return lan1+': '+trans1 + '\n'+lan2+': '+trans2
        

def send_translation(bot, update):
    translation = auto_translate(update.message.text)
    update.message.reply_text(translation)

dispatcher.add_handler(MessageHandler(Filters.text, send_translation))
updater.start_polling()
updater.idle()
