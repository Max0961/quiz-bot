import logging

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters.command import Command
from aiogram import types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import API_TOKEN
from data import quiz_data
from db import *

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()
    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )
    builder.adjust(1)
    return builder.as_markup()

async def get_question(message, user_id):
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']

    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)

async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)
    await get_question(message, user_id)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)

@dp.callback_query()
async def answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']

    if callback.data == "right_answer":
        await callback.message.answer(f"Верно! Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")
        correct_answers, total_questions = await get_quiz_result(callback.from_user.id)
        await update_quiz_result(callback.from_user.id, correct_answers + 1, total_questions + 1)
    else:
        await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")
        correct_answers, total_questions = await get_quiz_result(callback.from_user.id)
        await update_quiz_result(callback.from_user.id, correct_answers, total_questions + 1)

    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)
    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        correct_answers, total_questions = await get_quiz_result(callback.from_user.id)
        await callback.message.answer(f"Ваш результат: {correct_answers} из {total_questions}")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    correct_answers, total_questions = await get_quiz_result(user_id)
    await message.answer(f"Ваш результат: {correct_answers} из {total_questions}")

logging.basicConfig(level=logging.INFO)

async def main():
    await create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())