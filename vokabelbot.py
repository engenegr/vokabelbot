import logging
from asyncio import sleep
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor

from configparser import ConfigParser
from yandex_dictionary import Dictionary

from models.base import Base
from models.user import User
from models.translator import Translator
from models.card import Card
from models.base import session


from yandex_dictionary import Dictionary


# =============================================================================
# Init
# =============================================================================

# Config and Logging
cfg = ConfigParser()
cfg.read('settings.ini')
debug = cfg.getboolean('general', 'debug', fallback=False)
logfile = cfg.getboolean('general', 'logfile', fallback=False)
loglevel = logging.WARNING
filename = None
if debug: loglevel = logging.DEBUG
if logfile: filename='error.log'
logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s',
                    level=loglevel, filename=filename)

bot = Bot(token=cfg.get('general', 'token'))

YANDEX_API = cfg.get('general', 'yandex')

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# States
class Form(StatesGroup):
    setup_1st_lang = State()
    setup_2nd_lang = State()
    select = State()
    adding = State()
    training = State()


select_keys = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
select_keys.add("🔄1️⃣", "🔄2️⃣")
select_keys.add("💪")

stop_key = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
stop_key.add("🛑")

restart_msg = "Please, restart the bot"

@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await Form.setup_1st_lang.set()

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("EN", "DE", "RU")

    await message.reply("Hi there! Whats is your native language?",
                        reply_markup=markup)


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(lambda message: message.text in ["EN", "DE", "RU"],
                    state=Form.setup_1st_lang)
async def process_1st_language(message: types.Message, state: FSMContext):
    await Form.next()
    async with state.proxy() as data:
        data['native'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("EN", "DE", "RU")

    await message.reply("What language do you learn?", reply_markup=markup)


@dp.message_handler(lambda message: message.text in ["EN", "DE", "RU"],
                    state=Form.setup_2nd_lang)
async def process_2nd_language(message: types.Message, state: FSMContext):
    # Update state and data
    await Form.select.set()
    async with state.proxy() as data:
        data['learning'] = message.text
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Native:', md.code(data['native'])),
                md.text('Learning:', data['learning']),
                sep='\n',
            ),
            reply_markup=select_keys,
            parse_mode=ParseMode.MARKDOWN,
        )
        users = session.query(User).filter(User.chat_id == message.chat.id).all()
        logging.info(f'checking if user {message.chat.id} in the system')
        if len(users) == 0:  # if no user exists create a new from update
            user = User()
            user.chat_id = message.chat.id
            user.name = message.chat.first_name
            user.lan1 = data['native']
            user.lan2 = data['learning']
            session.add(user)  # cashes data for db
            session.commit()  # writes all cached data to file
            logging.info(f'new user {user.chat_id} created {user.lan1} {user.lan2}')
        elif len(users) == 1:  # if a user is found return it
            user = users[0]
            user.lan1 = data['native']
            user.lan2 = data['learning']
            session.commit()  # writes all cached data to file
            logging.info(f'updated {user.chat_id}, {user.lan1} {user.lan2}')
        else:
            logging.error(f'found multiple users id: {message.chat.id}')
            await bot.send_message(
                message.chat.id,
                md.text("I'm sorry something went wrong with your user id."),
                reply_markup=None,
                parse_mode=ParseMode.MARKDOWN,
            )

    # from now all info in DB
    #await state.finish()


@dp.message_handler(lambda message: message.text in ["🔄1️⃣"], state="*")
async def process_gender(message: types.Message, state: FSMContext):
    await Form.adding.set()
    async with state.proxy() as data:
        logging.debug(f"add-native: looking for {message.chat.id}")
        user = session.query(User).filter(User.chat_id == message.chat.id).all()
        if len(user) != 1:
            logging.debug(f"nobody with {message.chat.id} found in db")
            await state.finish()
            return await message.reply(restart_msg)
        user = user[0]
        data['native'] = user.lan1
        data['learning'] = user.lan2
        data['direction'] = 1
        data['user'] = user.id

        return await message.reply("Drop words here", reply_markup=stop_key)


@dp.message_handler(lambda message: message.text in ["🔄2️⃣"], state='*')
async def process_gender(message: types.Message, state: FSMContext):
    await Form.adding.set()
    async with state.proxy() as data:
        logging.debug(f"add-native: looking for {message.chat.id}")
        user = session.query(User).filter(User.chat_id == message.chat.id).all()
        if len(user) != 1:
            logging.debug(f"nobody with {message.chat.id} found in db")
            await state.finish()
            return await message.reply(restart_msg)
        user = user[0]
        data['native'] = user.lan1
        data['learning'] = user.lan2
        data['direction'] = 2
        data['user'] = user.id

        return await message.reply("Drop words here", reply_markup=stop_key)


@dp.message_handler(lambda message: message.text in ["💪"], state='*')
async def process_gender(message: types.Message, state: FSMContext):
    await Form.training.set()
    async with state.proxy() as data:
        if 'user' not in data.keys():
            logging.debug(f"add-native: looking for {message.chat.id}")
            user = session.query(User).filter(User.chat_id == message.chat.id).all()
            if len(user) != 1:
                logging.debug(f"nobody with {message.chat.id} found in db")
                await state.finish()
                return await message.reply(restart_msg)
            user = user[0]
            data['user'] = user.id
            data['native'] = user.lan1
            data['learning'] = user.lan2
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Native:', md.code(data['native'])),
                md.text('Learning:', data['learning']),
                md.bold('Be ready 3, 2, 1 ...'),
                sep='\n',
            ),
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN,
        )
        cards = session.query(Card).filter(Card.user_id == data['user']).all()
        logging.info(f'training {data["user"]} in total {len(cards)} cards')
        for card in cards:
            await bot.send_message(
                message.chat.id,
                md.text(
                    md.text(card.side1),
                    md.bold(card.side2),
                    sep=' ',
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            await sleep(1.)
    # from now all info in DB
    #await state.finish()
    return await message.reply("Completed", reply_markup=select_keys)


@dp.message_handler(Text(equals='🛑'), state='*')
async def stop_training(message: types.Message, state: FSMContext):
    await Form.select.set()
    await message.reply("Ads here", reply_markup=select_keys)


@dp.message_handler(lambda message: message.text not in ["🛑"], state=Form.adding)
async def continue_adding(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        w_native = ''
        w_learning = ''
        if data['direction'] == 1:
            dct = Dictionary(YANDEX_API,
                             from_lang=data['native'],
                             to_lang=data['learning'])
            from_lang = data['native']
            to_lang = data['learning']
            w_native = str(message.text).capitalize()
            result = dct.lookup(message.text)
        elif data['direction'] == 2:
            dct = Dictionary(YANDEX_API,
                             from_lang=data['learning'],
                             to_lang=data['native'])
            from_lang = data['learning']
            to_lang = data['native']
            w_learning = str(message.text).capitalize()
            result = dct.lookup(message.text, ui='en')
        else:
            logging.error("CHECK YOUR CODE")
            pass
        if not result.is_found:
            return await message.reply("not found")

        tr = result.get_tr('text', 'gen', 'pos')[0]

        if from_lang == 'DE':
            if result.gen == 'n':
                article = "das"
            elif result.gen == 'm':
                article = "der"
            else:
                article = "die"
            w_learning = f"{article} {result.text}"
        elif to_lang == 'DE':
            if tr['gen'] == 'n':
                article = "das"
            elif tr['gen'] == 'm':
                article = "der"
            else:
                article = "die"
            w_learning = f"{article} {tr['text']}"
        else:
            w_learning = tr['text']

        if data['direction'] == 2:
            w_native = str(tr['text']).capitalize()

        logging.info(f'checking if card {w_native} already exists')
        cards = session.query(Card).filter(Card.side1 == w_native).all()

        if len(cards) != 0:
            if to_lang == w_native:
                logging.debug(f'Exists! Reply native from Card')
                return await message.reply(cards[0].side1)
            else:
                logging.debug(f'Exists! Reply learning from Card')
                return await message.reply(cards[0].side2)

        logging.debug(f'adding new card')
        new_card = Card()
        new_card.user_id = data['user']
        new_card.lan1 = from_lang
        new_card.lan2 = to_lang
        new_card.side1 = w_native
        new_card.side2 = w_learning
        session.add(new_card)  # cashes data for db
        session.commit()  # writes all cached data to file
        logging.info(f'new card created {new_card.side1} {new_card.side2}')
        return await message.reply(f"{new_card.side1} - {new_card.side2}")


@dp.message_handler(lambda message: message.text not in ["🛑"], state=Form.training)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        pass
    await message.reply("trained")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
