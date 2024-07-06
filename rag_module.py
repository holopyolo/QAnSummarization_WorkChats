from sentence_transformers import SentenceTransformer
import json, os
import faiss
import numpy as np
with open('config_models.json', 'r', encoding='utf-8') as fl:
    config_js = json.loads(fl.read())
    MODEL_NAME_LLM=config_js['MODEL_NAME_LLM']
    DEFAULT_SYSTEM_RAG_PROMPT=config_js['DEFAULT_SYSTEM_RAG_PROMPT']
    prompt_inital=config_js['prompt_inital']
    MODEL_NAME_RETRIEVER=config_js['MODEL_NAME_RETRIEVER']
    dim_retriever=config_js['dim_retriever']

def ENCODDER(name_model='sentence-transformers/paraphrase-multilingual-mpnet-base-v2'):
    model = SentenceTransformer(name_model)
    def f(texts):
        return model.encode(texts)
    return f

index = faiss.IndexFlatL2(dim_retriever)
embed_message = ENCODDER(MODEL_NAME_RETRIEVER)

def add_messages_to_index(messages):
    '''
    
    add embeddings of messages to your DB
    
    '''
    index = faiss.IndexFlatL2(dim_retriever)
    embeddings = embed_message(messages)
    index.add(embeddings)

def split_to_chunks(data, k=10):
    '''
    
    Use k to groupy sequences of messsages of size k
    
    '''

    db = data.split('\n\n')
    return ['\n'.join(db[k*i:k*(i+1)]) for i in range(len(db)//k+1)]

def find_top_k_similar_messages(query, k=5):

    '''
    
    Find the top k similar messages to the query
    
    '''

    query_embedding = embed_message(query)
    distances, indices = index.search(np.array([query_embedding]), k)
    return indices[0]

def get_right_context(query, top_k_indices, chuncks, DEFAULT_SYSTEM_RAG_PROMPT=DEFAULT_SYSTEM_RAG_PROMPT):
    '''

    Get the right context for the query
    
    '''
    similar_messages = [chuncks[i] for i in top_k_indices]
    for pp in similar_messages:
        print(pp)
    context = "\n".join(similar_messages)
    context_rag = DEFAULT_SYSTEM_RAG_PROMPT.format(rag_con=context)
    return context_rag

def get_query(context: str, query: str) -> str:
    '''
    
    get context formatted

    '''
    splitted_chunks_q = split_to_chunks(context)
    embed_chunks = embed_message(splitted_chunks_q)
    add_messages_to_index(splitted_chunks_q)
    top_k_indices = find_top_k_similar_messages(query, k=3)
    context_final = get_right_context(query, top_k_indices, splitted_chunks_q)
    return context_final, query







