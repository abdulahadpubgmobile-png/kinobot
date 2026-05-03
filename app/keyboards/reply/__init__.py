from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup


def main_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎬 Kinolar")
    kb.button(text="🔍 Qidirish")
    kb.button(text="🎭 Janrlar")
    kb.button(text="ℹ️ Yordam")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="❌ Bekor qilish")
    return kb.as_markup(resize_keyboard=True)


def skip_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="⏭ O'tkazib yuborish")
    kb.button(text="❌ Bekor qilish")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)
