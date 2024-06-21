import os
from dotenv import load_dotenv
import requests
import discord
from discord.ext import commands
from bot_llama import Bot_Llama

intents = discord.Intents.default()
intents.messages = True 
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

load_dotenv()

ai = Bot_Llama(host=os.getenv('OLLAMA_HOST'),
               ollama_port=int(os.getenv('OLLAMA_PORT')),
               redis_db=os.getenv('REDIS_HOST'),
               redis_port=int(os.getenv('REDIS_PORT')))

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
    ai.set_context()

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
        

bot.run(os.getenv('DISCORD_TOKEN'))



