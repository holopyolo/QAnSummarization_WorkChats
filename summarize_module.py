import os
import json
import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer, AutoModel
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
import time
import rag_module


with open('config_models.json', 'r', encoding='utf-8') as fl:
    config_js = json.loads(fl.read())
    MODEL_NAME_LLM=config_js['MODEL_NAME_LLM']
    DEFAULT_SYSTEM_RAG_PROMPT=config_js['DEFAULT_SYSTEM_RAG_PROMPT']
    prompt_inital=config_js['prompt_inital']
    MODEL_NAME_RETRIEVER=config_js['MODEL_NAME_RETRIEVER']
    DEFAULT_SYSTEM_PROMPT=config_js['DEFAULT_SYSTEM_PROMPT']

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME_LLM,
    load_in_8bit=True,
    torch_dtype=torch.float16,
    device_map="auto",
    attn_implementation="flash_attention_2" #(vllm requires >16 gb, so we use flash_attention2) 
)
model.eval()
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME_LLM)
generation_config = GenerationConfig.from_pretrained(MODEL_NAME_LLM)

def prepare(model, tokenizer, query, prompt) -> dict:
    '''
    
    Preproccessing query+prompt.
    
    '''
    prompt = tokenizer.apply_chat_template([{
        "role": "system",
        "content": prompt
    }, {
        "role": "user",
        "content": query
    }], tokenize=False, add_generation_prompt=True)
    data = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
    data = {k: v.to(model.device) for k, v in data.items()}
    return data

def get_ans(model, tokenizer, data, custom_config=None) -> str:
    '''
    
    General method to get model's output
    
    '''
    if custom_config:
      output_ids = model.generate(**data, generation_config=custom_config)[0]
    else:
      output_ids = model.generate(**data, generation_config=generation_config)[0]
    output_ids = output_ids[len(data["input_ids"][0]):]
    output = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
    return output

def get_summarize(dialog: str) -> str:
    '''
    
    Summarize your plain text
    
    '''
    prep_text = prepare(model, tokenizer, dialog, DEFAULT_SYSTEM_PROMPT)
    answer = get_ans(model, tokenizer, prep_text)
    return answer

def get_rag_answer(context: str, query: str) -> str:
    '''
    
    QA system: get your answer based context, query
    
    '''
    context_prompt = rag_module.get_query(context, query)
    prep_text = prepare(model, tokenizer, query, context_prompt)
    answer = get_ans(model, tokenizer, prep_text)
    return answer