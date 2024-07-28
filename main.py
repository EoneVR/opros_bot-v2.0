from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from state import PollStates
from database import Database
from keyboard import *
from language import langs
from admin import (
    command_help,
    create_poll,
    ask_type_options,
    process_type,
    process_options,
    stop_or_reboot,
    show_my_polls,
    my_polls_callback,
    get_statistic
)

bot = Bot(token='')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database()
admin_id = [138104571]


@dp.message_handler(commands=['start'], state='*')
async def command_start(message: Message, state: FSMContext):
    chat_id = message.chat.id
    db.create_users_table()
    await bot.send_message(chat_id, 'Выберите язык\nTilni tanlang', reply_markup=choose_lang_button())
    await state.finish()


@dp.message_handler(regexp='🇷🇺 Русский|🇺🇿 Ozbek', state='*')
async def get_lang_register_user(message: Message, state: FSMContext):
    lang = message.text
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    user = db.get_user_by_chat_id(chat_id)
    lang = 'ru' if lang == '🇷🇺 Русский' else 'uz'
    if user:
        db.set_user_language(chat_id, lang)
        await message.answer(langs[lang]['select_language'])
    else:
        db.first_register_user(chat_id, full_name)
        db.set_user_language(chat_id, lang)
    await message.answer(langs[lang]['registration'], reply_markup=generate_contact_button(lang))
    await state.finish()


@dp.message_handler(content_types=['contact'], state='*')
async def finish_register(message: Message, state: FSMContext):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    lang = db.get_user_language(chat_id)
    db.update_user_to_finish_register(chat_id, phone)
    await message.answer(langs[lang]['reg_complete'], reply_markup=ReplyKeyboardRemove())
    await state.finish()


@dp.message_handler(commands=['participate'], state='*')
async def participate(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    active_polls = db.get_active_polls()
    if not active_polls:
        await message.answer(langs[lang]['not_polls'])
        return
    await message.answer(langs[lang]['participate'], reply_markup=generate_poll_buttons(active_polls))
    await state.finish()


@dp.callback_query_handler(lambda call: call.data.startswith('participate_'), state='*')
async def handle_participate_callback(callback: CallbackQuery, state: FSMContext):
    lang = db.get_user_language(callback.from_user.id)
    poll_id = callback.data.split('_')[1] if '_' in callback.data else None
    poll_data = db.get_poll_data(poll_id) if poll_id else None

    if not poll_data:
        await callback.answer(langs[lang]['not_polls'], show_alert=True)
        return

    await callback.message.delete()

    question = poll_data['question']
    options = poll_data['options']

    if options:
        poll_message = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=question,
            reply_markup=generate_active_polls_button(options, lang)
        )
        await state.update_data(question=question, options=options, poll_message_id=poll_message.message_id, votes={})
        await PollStates.votes.set()
    else:
        poll_message = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"{question}\n\n{langs[lang]['send_text_answer']}"
        )
        await state.update_data(question=question, options=options, poll_message_id=poll_message.message_id)
        await PollStates.text_answer.set()
    await callback.answer()


@dp.callback_query_handler(lambda call: call.data not in ['stop', 'reboot', 'back_to_polls'], state=PollStates.votes)
async def process_vote(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'back_to_polls':
        return
    data = await state.get_data()
    votes = data.get('votes', {})
    option = callback.data.split('_')[1] if '_' in callback.data else None
    chat_id = callback.from_user.id
    lang = db.get_user_language(chat_id)
    votes[chat_id] = option

    await state.update_data(votes=votes)
    await callback.answer(f"{langs[lang]['vote']}{option}")

    poll_id = db.get_poll_id_by_question(data['question'])
    db.save_vote(poll_id, option, chat_id)

    votes = db.get_votes(poll_id)
    current_votes = {opt: 0 for opt in data['options']}
    for vote in votes:
        if vote in current_votes:
            current_votes[vote] += 1

    results_message = "\n".join([f"{opt}: {count}" for opt, count in current_votes.items()])
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=data['poll_message_id'],
        text=f"{data['question']}\n\n{results_message}",
        reply_markup=generate_active_polls_button(data['options'], lang)
    )


@dp.callback_query_handler(lambda call: call.data == 'back_to_polls', state='*')
async def handle_back_to_polls(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    lang = db.get_user_language(chat_id)
    active_polls = db.get_active_polls()
    await callback.message.edit_text(langs[lang]['participate'], reply_markup=generate_poll_buttons(active_polls))
    await state.finish()
    await callback.answer()


@dp.message_handler(state=PollStates.text_answer)
async def process_text_vote(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    data = await state.get_data()
    question = data['question']
    user_text_answer = message.text
    db.save_text_answer(chat_id, question, user_text_answer)
    await message.answer(langs[lang]['text_answer_received'])
    await state.finish()

dp.register_message_handler(command_help, commands=['help'], state='*')
dp.register_message_handler(create_poll, commands=['create_poll'], state='*')
dp.register_message_handler(ask_type_options, state=PollStates.question)
dp.register_callback_query_handler(process_type, lambda call: call.data in ['option', 'text'], state=PollStates.answer_type)
dp.register_message_handler(process_options, state=PollStates.options)
dp.register_callback_query_handler(stop_or_reboot, lambda call: call.data in ['stop', 'reboot'], state=PollStates.votes)
dp.register_message_handler(show_my_polls, commands=['my_polls'], state='*')
dp.register_callback_query_handler(my_polls_callback, lambda call: call.data.startswith('manage_'), state='*')
dp.register_message_handler(get_statistic, commands=['statistic'], state='*')

executor.start_polling(dp)
