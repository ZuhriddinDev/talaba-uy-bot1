import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import sqlite3
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Baza bilan ishlash
conn = sqlite3.connect('ads.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    description TEXT,
    price TEXT,
    location TEXT,
    phone TEXT
)
''')
conn.commit()

# Asosiy menyu
menu_kb = ReplyKeyboardMarkup(resize_keyboard=True)
menu_kb.add(KeyboardButton("Uy e'lon berish"))
menu_kb.add(KeyboardButton("Uy qidirish"))

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Salom! Talabalar uchun uy-joy topuvchi botga xush kelibsiz.\n"
                         "Quyidagi menyudan tanlang.", reply_markup=menu_kb)

@dp.message_handler(lambda message: message.text == "Uy e'lon berish")
async def ad_post_start(message: types.Message):
    await message.answer("Iltimos, uy haqidagi qisqacha ma'lumotni yozing (masalan, xona soni, joylashuvi):")
    await AdPost.description.set()

@dp.message_handler(lambda message: message.text == "Uy qidirish")
async def search_start(message: types.Message):
    await message.answer("Uy qidirish funksiyasi hozircha ishlab chiqilmoqda. Tez orada!")

# AdPost uchun holatlar
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()
dp.storage = storage

class AdPost(StatesGroup):
    description = State()
    price = State()
    location = State()
    phone = State()

@dp.message_handler(state=AdPost.description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Iltimos, narxni yozing:")
    await AdPost.next()

@dp.message_handler(state=AdPost.price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Joylashuvni yozing:")
    await AdPost.next()

@dp.message_handler(state=AdPost.location)
async def process_location(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    await message.answer("Telefon raqamingizni yozing:")
    await AdPost.next()

@dp.message_handler(state=AdPost.phone)
async def process_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    description = data.get("description")
    price = data.get("price")
    location = data.get("location")
    phone = message.text
    cursor.execute("INSERT INTO ads (user_id, description, price, location, phone) VALUES (?, ?, ?, ?, ?)",
                   (message.from_user.id, description, price, location, phone))
    conn.commit()
    await message.answer("E'loningiz qabul qilindi! Rahmat.")
    await state.finish()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
