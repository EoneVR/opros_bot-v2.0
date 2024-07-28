from aiogram.dispatcher.filters.state import State, StatesGroup


class PollStates(StatesGroup):
    question = State()
    answer_type = State()
    options = State()
    poll_message_id = State()
    votes = State()
    text_answer = State()
