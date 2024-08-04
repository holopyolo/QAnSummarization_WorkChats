import pandas as pd
import sqlite3
from datetime import datetime
import time

'''
history df columns:
msg_id	|	timestamp	|	text	|	replying_to_id	|	replying_to_user_id	|	user_id	|	msg_chain	|	chat_id	
'''

class DataBase:
	def __init__(self):
		# self.history = pd.DataFrame(set_index='msg_id') # индекс это именно msg_id 
		self.db_conn = sqlite3.connect('history.db')
		# self.drop_db()
		self.db_conn.execute('CREATE TABLE IF NOT EXISTS HISTORY (msg_id, timestamp, text, replying_to_id, replying_to_user_id, user_id, username, msg_chain, chat_id);')
		self.db_conn.execute('CREATE TABLE IF NOT EXISTS GROUPS (chat_id, summary_total, summary_24h, name, username, last_summary_update);')
		self.db_conn.execute('CREATE TABLE IF NOT EXISTS USERS (user_id, chat_id_list, username, dm_chat_id, current_group_id);')
		# last_summary_update -- timestamp
		# chat_id_list -- list 

		self.history = pd.read_sql("SELECT * FROM HISTORY;", self.db_conn, index_col='msg_id')
		self.groups = pd.read_sql("SELECT * FROM GROUPS;", self.db_conn, index_col='chat_id')
		self.users = pd.read_sql("SELECT * FROM USERS;", self.db_conn, index_col='user_id')

		self.history_to_csv()
		# self.history['timestamp'] = pd.datetime(self.history['timestamp'])
		# self.groups['last_summary_update'] = pd.datetime(self.groups['last_summary_update'])

	def save_msg(self, tg_msg):
		if tg_msg.reply_to_message is not None:
			replying_to_id = str(tg_msg.reply_to_message.message_id) + ' ' + str(tg_msg.chat.id)
			if replying_to_id not in self.history.index:
				####
				replying_text = tg_msg.reply_to_message.text
				if replying_text is None:
					replying_text = tg_msg.reply_to_message.caption
				print('looking for replying text...', replying_text)
				replying_to_id = self.history[self.history['text'] == replying_text].loc[self.history['timestamp'] == tg_msg.reply_to_message.date.timestamp()].index[0]
				# ######
				print(replying_to_id)


			replying_to_user_id = tg_msg.reply_to_message.from_user.id
			msg_chain = self.history.loc[replying_to_id, 'msg_chain'] # тк индекс это msg_id, то можно так обращаться
		else:
			replying_to_id = replying_to_user_id = 'NULL'
			if len(self.history['msg_chain']) == 0:
				msg_chain = 0
			else:
				msg_chain = max(self.history['msg_chain']) + 1

		msg_timestamp = tg_msg.date.timestamp()
		# print('TIMESTAMP:', msg_timestamp)
		# print('PD DT timestamp:', pd.to_datetime(msg_timestamp, unit='s'))
		# print("DATE:", tg_msg.date)
		# print('PD DT usual:', pd.datetime(tg_msg.date))

		sender = tg_msg.from_user
		# print('msg', tg_msg.text, msg.caption)
		if tg_msg.forward_from is not None:
			print('forwarded msg', tg_msg.text, tg_msg.caption)
			sender = tg_msg.forward_from
			msg_timestamp = tg_msg.forward_date.timestamp()

		msg_text = tg_msg.text
		if msg_text is None:
			msg_text = tg_msg.caption

		new_msg = pd.DataFrame({
			'msg_id': [str(tg_msg.message_id) + ' ' + str(tg_msg.chat.id)],
			'timestamp': [msg_timestamp], # просто unix timestamp, not pd.datetime
			'text': [msg_text],
			'replying_to_id': [replying_to_id],
			'replying_to_user_id': [replying_to_user_id],
			'user_id': [sender.id],
			'username': [sender.username],
			'msg_chain': [msg_chain],
			'chat_id': [tg_msg.chat.id]
		}).set_index('msg_id')
		self.history = self.history.append(new_msg)
		self.db_conn.execute(f"INSERT INTO HISTORY (msg_id, timestamp, text, replying_to_id, replying_to_user_id, user_id, username, msg_chain, chat_id)\
		 VALUES ('{tg_msg.message_id} {tg_msg.chat.id}', {msg_timestamp}, '{tg_msg.text}', '{replying_to_id}', \
		  {replying_to_user_id}, {sender.id}, '@{sender.username}', {msg_chain}, {tg_msg.chat.id})")
		self.db_conn.commit()
		# self.history.to_sql(name='HISTORY', con=self.db_conn)
		# self.update_db()
		# replying_to -- содержит ссылку на сообщение, на которое это сообщение отвечает (через ответить)

	def update_db(self):
		self.history.to_sql(name='HISTORY', con=self.db_conn)
		self.groups.to_sql(name='GROUPS', con=self.db_conn)
		self.users.to_sql(name='USERS', con=self.db_conn)
		self.db_conn.commit()


	# WARNING !!!!! THIS DELETES ENTIRE DB!!!!!
	def drop_db(self):
		self.db_conn.execute('DROP TABLE USERS;')
		self.db_conn.execute('DROP TABLE HISTORY;')
		self.db_conn.execute('DROP TABLE GROUPS;')
		self.db_conn.commit()

	def get_history(self, group_id, last_n=None, start=None, end=None):
		result = self.history[self.history['chat_id'] == group_id]
		if len(result.index) == 0:
			return None
		# print(result['timestamp'])
		# result['timestamp'] = pd.to_datetime(result['timestamp'], unit='s')
		if last_n is not None:
			result = result[-last_n:] # last_n сообщений снизу таблицы
		if start is not None:
			# start = pd.to_datetime(start, unit='s')
			if type(start) != float: # not a timestamp 
				start = datetime(start).timestamp()

			result = result[result['timestamp'] >= start]
		if end is not None:
			if type(end) != float: # not a timestamp 
				end = datetime(end).timestamp()
			result = result[result['timestamp'] <= end]
		return result

	def update_current_group(self, user_id, group_id):
		self.users.loc[user_id, 'current_group_id'] = group_id
		self.groups.to_sql(name='GROUPS', con=self.db_conn)

	def get_current_group_id(user_id):
		return self.users.loc[user_id, 'group_id']

	def set_summary_last_update(self, group_id):
		self.groups.loc[group_id, 'last_summary_update'] = time.time()
		self.db_conn.execute(f"UPDATE GROUPS SET last_summary_update = {time.time()} WHERE chat_id = {group_id};")
		self.db_conn.commit()

	def add_group_chat(self, chat, admins = None):
		new_group = pd.DataFrame({
			'chat_id': [chat.id],
			 'admin_id': [admins], # можно не хрпнить в бд в целом
			 'summary_total': [None],
			 'summary_24h': [None],
			 'name': [chat.title],
			 'username': [chat.username],
			 'last_summary_update': [time.time()]
			}).set_index('chat_id')
		self.groups = self.groups.append(new_group)
		query = f"INSERT INTO GROUPS (chat_id, summary_total, summary_24h, name, username, last_summary_update)\
		 VALUES ({chat.id}, NULL, NULL, '{chat.title}', '{chat.username}', {time.time()});"	
		self.db_conn.execute(query)
		self.db_conn.commit()
		# self.groups.to_sql(name='GROUPS', con=self.db_conn)

	def get_all_group_ids(self):
		return self.groups.index

	def get_last_summary_update(self, group_id):
		return self.groups.loc[group_id, 'last_summary_update']

	def get_user_groups(self, user_id):
		return self.users.loc[user_id, 'chat_id_list']

	def get_user_ids(self):
		return self.users.index

	def add_user(self, user):
		new_user = pd.DataFrame({
			'user_id': [user.id],
			'chat_id_list': [[]],
			'username': [user.username],
			# 'dm_chat_id': user,
			'current_group_id': [None]
		}).set_index('user_id')
		self.users = self.users.append(new_user)
		self.db_conn.execute(f"INSERT INTO USERS (user_id, chat_id_list, username, dm_chat_id, current_group_id) VALUES ({user.id}, '{[]}', '{user.username}', NULL, NULL)")
		self.db_conn.commit()
		# self.users.to_sql(name='USERS', con=self.db_conn)

	def history_to_csv(self):
		self.history.to_csv('history.csv', encoding="utf-8")


