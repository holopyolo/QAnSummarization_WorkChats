from sentence_transformers import SentenceTransformer
import json
import os
import faiss
import numpy as np


def ENCODDER(name_model):
    model = SentenceTransformer(name_model)

    def f(texts):
        return model.encode(texts)
    return f


class Rag:
    def __init__(self,
                 MODEL_NAME_LLM,
                 DEFAULT_SYSTEM_RAG_PROMPT,
                 MODEL_NAME_RETRIEVER,
                 dim_retriever,
                 model=None):
        if model is not None:
            self.model = ENCODDER(MODEL_NAME_LLM)
        self.context = None
        self.index = faiss.IndexFlatL2(dim_retriever)
        self.embed_message = ENCODDER(MODEL_NAME_RETRIEVER)

    def add_messages_to_index(self, messages):
        '''

        add embeddings of messages to your DB

        '''
        index = faiss.IndexFlatL2(dim_retriever)
        embeddings = self.embed_message(messages)
        index.add(embeddings)

    def split_to_chunks(self, data, k=10):
        '''

        Use k to groupy sequences of messsages of size k

        '''

        db = data.split('\n\n')
        return ['\n'.join(db[k*i:k*(i+1)]) for i in range(len(db)//k+1)]

    def find_top_k_similar_messages(self, query: str, k: int = 5):
        '''

        Find the top k similar messages to the query

        '''

        query_embedding = self.embed_message(query)
        distances, indices = self.index.search(np.array([query_embedding]), k)
        return indices[0]

    def get_right_context(self, query: str, top_k_indices: int, chuncks: list) -> str:
        '''

        Get the right context for the query

        '''
        similar_messages = [chuncks[i] for i in top_k_indices]
        for pp in similar_messages:
            print(pp)
        context = "\n".join(similar_messages)
        context_rag = self.DEFAULT_SYSTEM_RAG_PROMPT.format(rag_con=context)
        return context_rag

    def get_query(self, context: str, query: str) -> str:
        '''

        get context formatted

        '''
        splitted_chunks_q = self.split_to_chunks(context)
        embed_chunks = self.embed_message(splitted_chunks_q)
        self.add_messages_to_index(splitted_chunks_q)
        top_k_indices = self.find_top_k_similar_messages(query, k=3)
        context_final = self.get_right_context(
            query, top_k_indices, splitted_chunks_q)
        return context_final, query
