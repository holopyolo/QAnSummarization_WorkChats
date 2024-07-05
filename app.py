# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from summarize_module import get_rag_answer, get_summarize
import pandas as pd
app = Flask(__name__)

def parse_to_prompt(js):
    print(js)
    df = pd.read_json(js, encoding='utf-8')
    df = df.sort_values(by='timestamp')
    df = df[df['text'].notna()]
    df = df.reset_index(drop=True)
    formatted_messages = []
    for index, row in df.iterrows():
        msg_id = row['msg_chain']
        user_id = row['user_id']
        username = row['username']
        text = row['text']
        replying_to_id = row['replying_to_id']
        timestamp = pd.to_datetime(row['timestamp'], unit='s').strftime('%d.%m.%Y %H:%M')
        if pd.isna(replying_to_id):
            formatted_msg = f"{index}; от: {username}; кому: ; дата: [{timestamp}]\n{text}\n"
        else:
            reply_msg_id = replying_to_id.split()[0]
            formatted_msg = f"{index}; от: {username}; кому: #{df[df['replying_to_id']==replying_to_id].index[0]-1}; [{timestamp}]\n{text}\n"
        
        formatted_messages.append(formatted_msg)
    return '\n'.join(formatted_messages)


@app.route('/rag-answer', methods=['POST'])
def rag_answer():
    data = request.json
    context = parse_to_prompt(data['table'])
    query = data['query']
    answer = get_rag_answer(context, query)
    return jsonify({"answer": answer})

@app.route('/summarize', methods=['POST'])
def summarize():
    dialog = parse_to_prompt(request.json['table'])
    answer = get_summarize(dialog)
    print(answer)
    return jsonify({"summary": answer})

app.run(host='0.0.0.0', port=8000)