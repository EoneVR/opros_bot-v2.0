from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext

from state import PollStates
from database import Database
from keyboard import *
from language import langs

db = Database()
admin_id = [138104571]


async def command_help(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    if message.from_user.id in admin_id:
        await message.bot.send_message(chat_id, langs[lang]['help_for_admins'])
    else:
        await message.bot.send_message(chat_id, langs[lang]['help_for_users'], reply_markup=ReplyKeyboardRemove())
    await state.finish()


async def create_poll(message: Message):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await PollStates.question.set()
    if message.from_user.id in admin_id:
        await message.bot.send_message(chat_id, langs[lang]['question'])


async def ask_type_options(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    await state.update_data(question=message.text)
    await PollStates.next()
    if message.from_user.id in admin_id:
        await message.answer(langs[lang]['type_options'], reply_markup=generate_type_button(lang))


async def process_type(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    lang = db.get_user_language(chat_id)
    user_data = await state.get_data()
    question = user_data['question']
    if callback.data == 'option':
        await callback.message.bot.send_message(chat_id=chat_id, text=langs[lang]['options'])
        await callback.answer()
        await state.update_data(answer_type=callback.data)
        await PollStates.options.set()
    else:
        db.get_question_and_options(chat_id, question, None)
        await callback.message.bot.send_message(chat_id=chat_id, text=question,
                                                reply_markup=generate_stop_and_reboot_button(lang))
        await callback.answer(langs[lang]['user_question'])
        await state.update_data(answer_type=callback.data, poll_message_id=callback.message.message_id)
        await PollStates.votes.set()


async def process_options(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    options = [option.strip() for option in message.text.split(',')]
    user_data = await state.get_data()
    question = user_data['question']
    db.get_question_and_options(chat_id, question, options)
    if message.from_user.id in admin_id:
        poll_message = await message.bot.send_message(
            chat_id=chat_id,
            text=question,
            reply_markup=generate_options_button(options)
        )
        await state.update_data(poll_message_id=poll_message.message_id, options=options, votes={})
        await PollStates.votes.set()
    await message.answer(langs[lang]['manage'], reply_markup=generate_stop_and_reboot_button(lang))


async def stop_or_reboot(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    lang = db.get_user_language(callback.from_user.id)
    user_data = await state.get_data()
    question = user_data['question']
    options = user_data.get('options', [])
    poll_message_id = user_data.get('poll_message_id')

    if callback.from_user.id in admin_id:
        if not poll_message_id:
            await callback.answer(langs[lang]['not_polls'], show_alert=True)
            return
        if callback.data == 'stop':
            is_active = 0
            db.deactivate_polls(chat_id, is_active)
            await callback.message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=poll_message_id,
                text=f"{question}\n\n{langs[lang]['stop']}",
                reply_markup=None
            )
            await state.finish()
        elif callback.data == 'reboot':
            await callback.message.bot.delete_message(chat_id=chat_id, message_id=poll_message_id)
            if options:
                poll_message = await callback.message.bot.send_message(
                    chat_id=chat_id,
                    text=question,
                    reply_markup=generate_options_button(options)
                )
                await state.update_data(poll_message_id=poll_message.message_id, options=options, votes={})
                await PollStates.votes.set()
            else:
                await callback.message.bot.send_message(
                    chat_id=chat_id,
                    text=question,
                    reply_markup=generate_stop_and_reboot_button(lang)
                )
                await state.update_data(poll_message_id=callback.message.message_id)
                await PollStates.votes.set()
        await callback.answer()


async def show_my_polls(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    active_polls = db.get_active_polls()
    if message.from_user.id in admin_id:
        if not active_polls:
            await message.answer(langs[lang]['not_polls'])
            return
        await message.answer(langs[lang]['manager_polls'], reply_markup=generate_poll_manager_buttons(active_polls))
        await state.finish()


async def my_polls_callback(callback: CallbackQuery, state: FSMContext):
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
        poll_message = await callback.message.bot.send_message(
            chat_id=callback.message.chat.id,
            text=question,
            reply_markup=generate_stop_and_reboot_button(lang)
        )
    else:
        poll_message = await callback.message.bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"{question}\n\n{langs[lang]['send_text_answer']}",
            reply_markup=generate_stop_and_reboot_button(lang)
        )

    await state.update_data(question=question, options=options, poll_message_id=poll_message.message_id, votes={})
    await PollStates.votes.set()
    await callback.answer()


async def get_statistic(message: Message, state: FSMContext):
    chat_id = message.chat.id
    lang = db.get_user_language(chat_id)
    result = db.get_quantity_of_users(chat_id)
    result1 = db.get_quantity_of_polls(chat_id)
    result2 = db.get_quantity_of_delete_polls(chat_id)
    if message.from_user.id in admin_id:
        if lang == 'ru':
            await message.answer(
                f'Количество пользователей: {len(result)}\n'
                f'Количество созданных опросов: {len(result1)}\n'
                f'Количество удаленных опросов: {len(result2)}')
        else:
            await message.answer(
                f"Foydalanuvchilar soni: {len(result)}\n"
                f"Yaratilgan so'rovlar soni: {len(result1)}\n"
                f"O'chirilgan savollar soni: {len(result2)}")
    await state.finish()
