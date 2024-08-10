# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
import hydra
from omegaconf import DictConfig, OmegaConf
from summarize_module import get_rag_answer, get_summarize
import pandas as pd
import logger_logic
from rag_module import Rag, ENCODDER


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
        timestamp = pd.to_datetime(
            row['timestamp'], unit='s').strftime('%d.%m.%Y %H:%M')
        if pd.isna(replying_to_id):
            formatted_msg = f"{index}; от: {
                username}; кому: ; дата: [{timestamp}]\n{text}\n"
        else:
            reply_msg_id = replying_to_id.split()[0]
            formatted_msg = f"{index}; от: {username}; кому: #{
                df[df['replying_to_id'] == replying_to_id].index[0]-1}; [{timestamp}]\n{text}\n"

        formatted_messages.append(formatted_msg)
    return '\n'.join(formatted_messages)


@hydra.main(version_base=None, config_path="conf")
def main(cfg: DictConfig) -> None:
    if not (len(cfg)):
        logger.error('Config is empty')
        return 0
    print(OmegaConf.to_yaml(cfg))
    logger.info(f'Config is loaded: {OmegaConf.to_yaml(cfg)}')
    app = Flask(__name__)
    app.run(host='0.0.0.0', port=8000)
    logger = logger_logic(__name__)
    logger.info('Server is running')
    model_global = None

    if cfg['use_one_model']:
        model_global = ENCODDER(cfg['MODEL_NAME_LLM'])

    rag = Rag(cfg['MODEL_NAME_LLM'],
              cfg['DEFAULT_SYSTEM_RAG_PROMPT'],
              cfg['MODEL_NAME_RETRIEVER'],
              cfg['dim_retriever'],
              model_global)

    @app.route('/rag-answer', methods=['POST'])
    def rag_answer():
        data = request.json
        try:
            context = parse_to_prompt(data['table'])
            query = data['query']
        except Exception as err:
            logger.exception('Error during parsing args for RAG')
            return jsonify({"answer": "Error during parsing args for RAG: \n" + str(err)})

        try:
            answer = rag.get_rag_answer(context, query)
        except Exception as err:
            logger.exception('Error during generating answer for RAG')
            return jsonify({"answer": "Error during generating answer for RAG: \n" + str(err)})

        return jsonify({"answer": answer})

    @app.route('/summarize', methods=['POST'])
    def summarize():
        try:
            dialog = parse_to_prompt(request.json['table'])
        except Exception as err:
            logger.exception('Error during parsing args for summarize')
            return jsonify({"answer": "Error during parsing args for summarize: \n" + str(err)})

        try:
            answer = get_summarize(dialog)
        except Exception as err:
            logger.exception('Error during generating answer for summarize')
            return jsonify({"answer": "Error during generating answer for summarize: \n" + str(err)})

        return jsonify({"summary": answer})


if __name__ == '__main__':
    main()
