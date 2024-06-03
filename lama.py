import os
import ollama
from ollama import *
import base64
import jsonlines
import json
import requests
import discord
from discord.ext import commands
import redis
import asyncio

intents = discord.Intents.default()
intents.messages = True 
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

class glorpai:

    context = None
    default_llama = "llama3:latest"
    default_llava = "llava"
    llama_model = default_llama
    visual_model = default_llava

    def query_model(self, query, system, user):

        url = "http://localhost:11434/api/generate"
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

        print(data)

        with response as f:
            with jsonlines.Reader(f.iter_lines()) as reader:
                for obj in reader:
                    if obj != None:
                        answer += obj.get('response')

                    if 'context' in obj:
                        cont_temp = obj['context']

                        if cont_temp != None:
                            self.context = cont_temp

        #self.store_context()

        return answer

    def query_visual_model(self, query, user, image):

        with open(image, "rb") as img_file:
            base64_string = base64.b64encode(img_file.read()).decode('utf-8')

        query = f"[username:{user}] message:{query}"

        response = ollama.generate(self.default_llava, query, images=[base64_string])
        print(response['response'])

        return response['response']
    
    def embed(self, embedding):
        ollama.embeddings(model=self.llama_model, prompt=embedding)

    def reset_model(self):
        self.context = None
        self.llama_model = self.default_llama
        self.llama_model = self.default_llava

    def create_model(self, parent_model, system_prompt, name):
        modelfile = f'''FROM {parent_model}\nSYSTEM {system_prompt}'''

        desc_name = f"{parent_model}-{name}"

        ollama.create(model=desc_name, modelfile=modelfile)

        self.change_model(desc_name)

    def store_context(self):
        r = redis.Redis(host='100.109.17.11', port=6379, decode_responses=True)
        for item in self.context:
            r.rpush("context", item)

    def set_context(self):
        r = redis.Redis(host='100.109.17.11', port=6379, decode_responses=True)
        
        elements = r.lrange("context", 1, -1)

        elements = [int(element) for element in elements]
            
        self.context = elements

    def clear_context(self):
        r = redis.Redis(host='100.109.17.11', port=6379, decode_responses=True)
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
    
# ----------------------------------------------------------------------------

ai = glorpai()

@bot.command()
async def remember(ctx):
    channel = bot.get_channel(1232887292960440363)

    async for message in channel.history(limit=200):
        print("lol")
        print(message.content)
            
@bot.command()
async def store(ctx):
    ai.store_context()

@bot.command(brief="Create a model")
async def create(ctx, arg1, arg2, arg3):
    ai.create_model(arg1, arg2, arg3)

    print("Created model " + (arg1 + arg3))
    await ctx.send("[SYSTEM] Created model " + (arg1+"-"+arg3))

@bot.command()
async def current(ctx):
    await ctx.send("[SYSTEM] The current model is: " + ai.current_model())
    print("The current model is: " + ai.current_model())

@bot.command()
async def set_context(ctx):
    ai.set_context()
    await ctx.send("[SYSTEM] Set the context from DB")

@bot.command()
async def reset(ctx):
    ai.reset_model()

    print("reset model")
    await ctx.send("[SYSTEM] Reset model")

@bot.command()
async def delete(ctx, *arg):
    ai.delete_model(arg)

    print("deleted model(s)")
    await ctx.send("[SYSTEM] Deleted model(s)")

@bot.command()
async def clear(ctx):
    ai.clear_context()
    await ctx.send("[SYSTEM] Cleared DB and local context")

@bot.command()
async def pull(ctx, arg):
    if ai.pull_model(arg) == 'success':
        await ctx.send("[SYSTEM] Successfully pulled " + arg)
    
@bot.command()
async def list(ctx):
    models = ai.list_models()
    mes = ""
    for model in models:
        mes += model + "\n"
    
    await ctx.send(mes)

@bot.command()
async def change(ctx, arg):
    if ai.change_model(arg) == 1:
        print("Error switching to model " + arg)
        await ctx.send("[SYSTEM] Error switching to model, make sure it is pulled using the '/pull <ollama-ai> or created using the /create < " + arg)
    else:    
        print("Changed to model " + arg)
        await ctx.send("[SYSTEM] Changed to model " + arg)

@bot.command()
async def embed(ctx, arg):
    ai.embed(arg)
    await ctx.send("[SYSTEM] Successfully embedded")

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    #ai.set_context()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

    if message.content.startswith(bot.command_prefix):
        return
    
    ctx = await bot.get_context(message)

    types = ("image/jpg", "image/png", "image/webp", "image/jpeg")

    if message.channel.name == "general":
        query = message.content
        system = None
        is_reply = False

        if message.reference:
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            if referenced_message.author == bot.user:
                print("This is a reply to the bot's message")
                is_reply = True
                system = f"{message.author} replied to your message, your original message's contents was: {referenced_message.content}"

        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type in types:   
                    with open("temp.png", "wb") as file:
                        await attachment.save(file)

                    image_textualized = ai.query_visual_model(message.content, message.author, "temp.png")
                    test = ai.query_model(f"[SYSTEM] This message had an image attached, the following is details about the image: {image_textualized} - - - - - {message.content}", None, message.author)
                    print(test)
                    await message.channel.send(test)
                    return
        
        async with ctx.typing():
            response = ai.query_model(query, system, message.author)

        if is_reply:
            await message.reply(response)
            return
        else:
            await message.channel.send(response)
            return
        

bot.run('MTIzMjg4NjE5ODQ4NjMwMjgwMw.GgRoKc.cWWhTieJwat_t4CGSjuKe22ZGsqyDlWRHK4XE4')



