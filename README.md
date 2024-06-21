# Ollama Discord Bot <br>
Wrapper of sorts between the Ollama HTTP/Python APIs and Discord Bot Functionality
Most Ollama functions are mapped to a Discord Bot command [[Commands](#Bot_Commands)]

#### Requirements <br>
- Redis Database
- Capable PC that is running Ollama (and you can access, we will talk about this later)
- Python 3.x, because this is not a compiled/docerized application

#### Disclaimer <br>
- This is NOT a Docker container, you are just running some simple python code

### Setup <br>

#### Redis Setup
Install Redis database and make it accessible to whatever machine you are running the discord bot on <br>
Change the `REDIS_DB` & `REDIS_PORT` variables the host and port of the Redis DB <br>

#### Ollama Setup
Install Ollama on a capable machine (one with a GPU and at least 16 GB of memory)
- ##### Windows
Go to Windows Environment Variables and set OLLAMA_HOST to 0.0.0.0. This way you will be able to connect to

- ##### Linux
```
export OLLAMA_HOST=0.0.0.0
```
<br>

1. Clone repo <br>
``` 
git clone https://github.com/Granther/ollama-bot
```
2. Create python virtual environment <br>
```
cd ollama_bot
python -m venv .venv
source .venv/bin/activate
```
3. Install Python dependencies from `requirements.txt` file <br>
```
pip install -r requirements.txt
```
4. Execute `main.py` <br>
```
python main.py
```

# Bot Commands <br>
`/remember` - Load `n` past messages into the context of the current query. Basically RAG, but unstable <br>
`/store` - Manually load the current context of the model's past interactions into the Database <br>
`/create` - Create a new profile/instance of a downloaded model but with your own system message <br>
`/current` - Print current model being used for the bot <br>
`/set_context` - Manually set the LLMs context from the DB <br>
`/reset` - Reset back to the default LLM <br>
`/delete` - Delete specific model profile by name <br>
`/clear` - Manually clear the model's context from the Database <br>
`/pull` - Pull down a model from Ollama by name <br>
`/list` - List all model profiles <br>
`/change` - Change to an existing model profile <br>
