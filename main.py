from aiogram import Bot, Dispatcher
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.methods import GetChatAdministrators
import asyncio
import json
import config
import time
import pandas as pd
from history import DataBase

from summary import SummaryAI
from utils import get_minutes



# сделать еще диаграмму бота с кнопками наверное -- а кнопок нету, только комманды 


bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
router = Router()
dp = Dispatcher(bot=bot, storage=MemoryStorage())
dp.include_router(router)

db = DataBase()
summariser = SummaryAI()


@router.message(Command("start"))
async def start_handler(msg: Message):
	if msg.chat.type == 'private':
		print(db.get_user_ids())
		if msg.from_user.id not in db.get_user_ids():
			db.add_user(msg.from_user)
		user_groups = db.get_user_groups(msg.from_user.id)
		if user_groups is not None:
			builder = InlineKeyboardBuilder()

			for group in user_groups:
				builder.row(types.InlineKeyboardButton(
					text=group['name'],
					callback_data=json.dumps({
            			"type": "answer", 
            			"text": "choose_group_chat",
            			"link": group['chat_id']}) # hlink()
				))
	
				await msg.answer(
				text="Выберите группу из списка:",
				reply_markup=builder.as_markup()
				)

	if msg.chat.type not in ('group', 'channel'):
		await msg.answer(
			"Добавьте этого бота в группу или канал, чтобы начать работу "
		)




@dp.callback_query(F.data == 'choose_group_chat')
async def choose_group_chat(callback: types.CallbackQuery, callback_data):
	db.update_current_group(json.loads(callback_data)['link'])



@router.message(Command("summary"))
async def get_summary(msg: Message):
	group_id = msg.chat.id
	if msg.chat.type == 'private':
		group_id = db.get_current_group_id(msg.from_user.id)
	args = msg.text.split()
	if len(args) == 1:
		# тогда возвращаем саммари за весь период 
		msg_history = db.get_history(group_id)
	elif len(args) == 2:
		# тогда аргумент - это число и мы возвращаем саммари последних n сообщений
		msg_history = db.get_history(group_id, last_n=int(args[1]))
	elif len(args) == 3:
		msg_history = db.get_history(group_id, start=args[1], end=args[2])
	
	db.set_summary_last_update(msg.chat.id)
	await msg.answer(summariser.get_summary(msg_history))


@router.message(Command("ask"))
async def answer_question(msg: Message):
	group_id = msg.chat.id
	if msg.chat.type == 'private':
		group_id = db.get_current_group_id(msg.from_user.id)
	args = msg.text.split()
	if len(args) >= 2:
		print('answering to', msg.text)
		await msg.answer(summariser.answer_question(db.get_history(group_id), question=msg.text[5:]))
	elif msg.reply_to_message is not None and msg.reply_to_message.text is not None:
		print('answering to with reply', msg.text)
		await msg.answer(summariser.answer_question(db.get_history(group_id), question=msg.reply_to_message.text))


new_update = [0]

async def update_summary(msg, summary_update_frequency_seconds):
	if summary_update_frequency_seconds == 0:
		return 0
	group_id = msg.chat.id
	if msg.chat.type == 'private':
		group_id = db.get_current_group_id(msg.from_user.id)
	print(db.get_last_summary_update(msg.chat.id))
	if time.time() - db.get_last_summary_update(msg.chat.id) >= summary_update_frequency_seconds:
		msg_history = db.get_history(group_id, start=float(time.time() - summary_update_frequency_seconds))
		await msg.answer(summariser.get_summary(msg_history))
		db.set_summary_last_update(msg.chat.id)
		time.sleep(4)
		await update_summary(msg, summary_update_frequency_seconds)
	else:
		await asyncio.sleep(summary_update_frequency_seconds)
		if new_update[0] == summary_update_frequency_seconds:
			await update_summary(msg, summary_update_frequency_seconds)



# формат: /set_update 2h 30m
@router.message(Command("set_update"))
async def set_update(msg: Message):
	args = msg.text.split()
	if len(args) > 1: # and msg.from_user.id in db.get_admin_ids_for_chat(msg.chat.id):
		summary_update_frequency_minutes = sum(get_minutes(arg) for arg in args[1:])
		new_update[0] = summary_update_frequency_minutes * 60
		await update_summary(msg, new_update[0])


# тут история должна хранится в виде pd.dataframe 
@router.message()
async def message_handler(msg: Message):
	if msg.text is not None or msg.caption is not None:
		db.save_msg(msg)
	if msg.chat.id not in db.get_all_group_ids():
		db.add_group_chat(msg.chat) # admins=await bot.get_chat_administrators(chat_id=msg.chat.id)
	if msg.from_user.id not in db.get_user_ids():
		db.add_user(msg.from_user)
	# здесь просто сохраняется сообщение в историю


# @dp.callback_query(F.data == "add_group_chat")
# async def add_group_chat(callback: types.CallbackQuery):
# 	# users[callback.message.chat.id].wait_wallet()
# 	await callback.message.answer("не знаю, че то надо сделать вам:")






async def main():
	await bot.delete_webhook(drop_pending_updates=True)
	await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
	asyncio.run(main())
	

