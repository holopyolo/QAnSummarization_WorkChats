import requests as rq



# with open('test.txt', 'r', encoding='utf-8') as f:
# 	url = "http://185.189.167.245:8000/summarize"
# data = {
# 		'dialog': f.read()
# 	}
# 	resp = rq.post(url, json=data)
# 	print(resp.status_code)
# 	if resp.status_code == 200:
# 		res = resp.json()
# 		print(res)


# @app.route('/rag-answer', methods=['POST'])



# def rag_answer():
# 	# data = request.json
# 	# context = data['context']
# 	# query = data['query']

# 	url = "http://185.189.167.245:8000/rag-answer"
# 	data = {
# 		'context': msg_history.to_json(),
# 		'query': question
# 	}
# 	answer = get_rag_answer(context, query)
# 	return jsonify({"answer": answer})



class SummaryAI:
	def __init__(self):
		pass

	def get_summary(self, msg_history):
		url = "http://185.189.167.245:8000/summarize"
		data = {
			'table': msg_history.to_json(force_ascii=False)
		}
		resp = rq.post(url, json=data).json()

		return resp['summary']


	def answer_question(self, msg_history, question = ''):
		url = "http://185.189.167.245:8000/rag-answer"
		data = {
			'table': msg_history.to_json(force_ascii=False),
			'query': question
		}

		resp = rq.post(url, json=data).json()

		return resp['answer']
