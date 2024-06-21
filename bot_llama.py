import os
import ollama
from ollama import *
import base64
import jsonlines
import json
import requests
import redis
import asyncio

class Bot_Llama:
    def __init__(self, host: str = '127.0.0.1', ollama_port: int = 11434, redis_db: str = '127.0.0.1', redis_port: int = 6379):
        self.host = host
        self.ollama_port = ollama_port
        self.redis_db = redis_db
        self.redis_port = redis_port

    context = None
    default_llama = "llama3:instruct"
    default_llava = "llava"
    llama_model = default_llama
    visual_model = default_llava

    def query_model(self, query, system, user):

        url = f"http://{self.host}:{int(self.ollama_port)}/api/generate"
        headers = {"Content-Type": "application/json"}

        if system != None:
            query = f"[username:{user}] [system: {system}] message:{query}"
        else:
            query = f"[username:{user}] message:{query}"

        if self.context == None:
            data = {"model": self.llama_model, "prompt": query}
        else:
            data = {"model": self.llama_model, "prompt": query, "context": self.context}

        response = requests.post(url, headers=headers, json=data)
        answer = ""

        with response as f:
            with jsonlines.Reader(f.iter_lines()) as reader:
                for obj in reader:
                    if obj != None:
                        answer += obj.get('response')

                    if 'context' in obj:
                        cont_temp = obj['context']

                        if cont_temp != None:
                            self.context = cont_temp

        return answer

    def query_visual_model(self, query, user, image):

        with open(image, "rb") as img_file:
            base64_string = base64.b64encode(img_file.read()).decode('utf-8')

        query = f"[username:{user}] message:{query}"

        response = ollama.generate(self.default_llava, query, images=[base64_string])

        return response['response']
    
    def embed(self, embedding):
        ollama.embeddings(model=self.llama_model, prompt=embedding)

    def reset_model(self):
        self.context = None
        self.llama_model = self.default_llama
        self.llama_model = self.default_llava

    def create_model(self, parent_model, system_prompt, name):
        modelfile = f'''FROM {parent_model}:instruct\nSYSTEM {system_prompt}'''

        desc_name = f"{parent_model}-{name}"

        ollama.create(model=desc_name, modelfile=modelfile)

        self.change_model(desc_name)

    def connect_redis(self):
        try:
            r = redis.Redis(host='100.109.17.11', port=6379, decode_responses=True)
        except redis.exceptions.RedisError as e:
            raise RuntimeError('Failed to make Redis connection') from e

    def store_context(self):
        try:
            r = self.connect_redis()
        except RuntimeError as e:
            print(e)
            return

        for item in self.context:
            r.rpush("context", item)

    def set_context(self):
        try:
            r = self.connect_redis()
        except RuntimeError as e:
            print(e)
            return    
            
        elements = r.lrange("context", 1, -1)

        elements = [int(element) for element in elements]
            
        self.context = elements

    def clear_context(self):
        try:
            r = self.connect_redis()
        except RuntimeError as e:
            print(e)
            return
        
        r.delete("context")
        self.context = None

    def pull_model(self, model_name):
        return ollama.pull(model_name)['status']
    
    def delete_model(self, models):
        for model in models:
            ollama.delete(model)
        return
    
    def list_models(self):
        p = ollama.list()['models']
        models = []
        for i in p:
            i = i['model']
            i = i.split(":", 1)[0]
            models.append(i)
        

        print(models)
        return models

    def change_model(self, new_model):
        models = self.list_models()
        if new_model in models:
            self.llama_model = new_model
        else:
            return 1
        self.context = None
        return 0
    
    def current_model(self):
        return self.llama_model
    