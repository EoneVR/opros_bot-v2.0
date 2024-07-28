from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from language import langs


def choose_lang_button():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    russian = KeyboardButton(text='🇷🇺 Русский')
    uzbek = KeyboardButton(text='🇺🇿 Ozbek')
    markup.row(russian, uzbek)
    return markup


def generate_contact_button(lang):
    return ReplyKeyboardMarkup([
        [KeyboardButton(text=langs[lang]['contact'], request_contact=True)]
    ], resize_keyboard=True)


def generate_options_button(options):
    markup = InlineKeyboardMarkup(row_width=1)
    for option in options:
        markup.add(InlineKeyboardButton(option, callback_data=option))
    return markup


def generate_type_button(lang):
    markup = InlineKeyboardMarkup(row_width=2)
    if lang == 'ru':
        markup.row(
            InlineKeyboardButton(text='С опциями', callback_data='option'),
            InlineKeyboardButton(text='В виде текста', callback_data='text'),
        )
    else:
        markup.row(
            InlineKeyboardButton(text="To'xtatish", callback_data='option'),
            InlineKeyboardButton(text='Qayta ishga tushirish', callback_data='text'),
        )
    return markup


def generate_stop_and_reboot_button(lang):
    markup = InlineKeyboardMarkup()
    if lang == 'ru':
        markup.add(
            InlineKeyboardButton(text='⛔Остановить⛔', callback_data='stop')
        )
        markup.add(
            InlineKeyboardButton(text='♻Перезапустить♻', callback_data='reboot')
        )
    else:
        markup.add(
            InlineKeyboardButton(text="⛔To'xtatish⛔", callback_data='stop')
        )
        markup.add(
            InlineKeyboardButton(text='♻Qayta ishga tushirish♻', callback_data='reboot')
        )
    return markup


def generate_poll_manager_buttons(active_polls):
    markup = InlineKeyboardMarkup()
    for poll_id, poll_question in active_polls.items():
        button = InlineKeyboardButton(text=poll_question, callback_data=f'manage_{poll_id}')
        markup.add(button)
    return markup


def generate_poll_buttons(active_polls):
    markup = InlineKeyboardMarkup()
    for poll_id, poll_question in active_polls.items():
        button = InlineKeyboardButton(text=poll_question, callback_data=f'participate_{poll_id}')
        markup.add(button)
    return markup


def generate_active_polls_button(options, lang):
    markup = InlineKeyboardMarkup()
    for option in options:
        button = InlineKeyboardButton(text=option, callback_data=f'vote_{option}')
        markup.add(button)
    back_button = InlineKeyboardButton(text=langs[lang]['back'], callback_data='back_to_polls')
    markup.add(back_button)
    return markup
