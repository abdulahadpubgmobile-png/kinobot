from aiogram.fsm.state import State, StatesGroup


class AddMovieFSM(StatesGroup):
    waiting_for_code = State()
    waiting_for_title = State()
    waiting_for_year = State()
    waiting_for_country = State()
    waiting_for_genre = State()
    waiting_for_description = State()
    waiting_for_trailer = State()
    waiting_for_video = State()
    waiting_for_poster = State()
    waiting_for_confirm = State()


class BroadcastFSM(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirm = State()


class SearchFSM(StatesGroup):
    waiting_for_query = State()


class EditMovieFSM(StatesGroup):
    waiting_for_title = State()
    waiting_for_year = State()
    waiting_for_country = State()
    waiting_for_genre = State()
    waiting_for_description = State()
    waiting_for_trailer = State()
    waiting_for_video = State()
    waiting_for_poster = State()
    waiting_for_confirm = State()
