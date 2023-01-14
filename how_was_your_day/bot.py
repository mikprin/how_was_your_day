# File with code for the telegram bot


# Importing libraries
import logging, dotenv, os, sys
import telebot
import openai

# Local imports
import msgs

# Logging

import logging.handlers
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


# Importing settings and environment variables

script_dir_full = os.path.dirname(os.path.realpath(__file__))

try:
    dotenv.load_dotenv(os.path.join(script_dir_full, ".." ,'.env'))
    logging.info("Loaded .env file")
except Exception as e:
    logging.error("Error loading .env file: ", e)
    sys.exit(1)

# OpenAI API:
openai.api_key = os.getenv("OPENAI_API_KEY")
try:
    max_tokens = int(os.getenv("MAX_TOKENS"))
except Exception as e:
    logging.error("Error loading max tokens: ", e)
    sys.exit(1)
logging.info(f"OpenAI API key loaded. Max tokens: {max_tokens}")

# Telegram bot
telegram_token = os.getenv("TELEGRAM_API_KEY")

bot = telebot.TeleBot(telegram_token, parse_mode=None) # You can set parse_mode by default. HTML or MARKDOWN


def get_user_info(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    last_name = message.from_user.last_name
    user_username = message.from_user.username
    user_info = {
        "user_id": user_id,
        "user_name": user_name,
        "user_username": user_username,
        "user_last_name": last_name
    }
    return user_info

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_info = get_user_info(message)
    logging.info(f"User with nickname {user_info['user_username']} started the bot.")
    bot.reply_to(message, msgs.welcome_msg)

@bot.message_handler(commands=['creator'])
def send_creator_info(message):
    user_info = get_user_info(message)
    logging.info(f"User with nickname {user_info['user_username']} requested info about creator.")
    bot.reply_to(message, msgs.creator_info)

@bot.message_handler(commands=['query'])
def send_query(message):
    prompt = message.text
    user_info = get_user_info(message)
    logging.info(f"User with nickname {user_info['user_username']} query input: {prompt} with command: query")
    response = openai.Completion.create(model="text-davinci-003", prompt=prompt, temperature=0.5, max_tokens=max_tokens)
    logging.info(f"Bot response: {response.choices[0].text}")
    bot.reply_to(message, response.choices[0].text)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    user_input = message.text
    user_info = get_user_info(message)
    logging.info(f"User with nickname {user_info['user_username']} query input: {user_input}.")
    base_prompt = f"Person with name {user_info['user_name']} comes and says: {user_input} \n You want to say something nice to user, support him. Want to make he or she happy and reply with:"
    response = openai.Completion.create(model="text-davinci-003", prompt=base_prompt, temperature=0.5, max_tokens=max_tokens)
    logging.info(f"Bot response: {response.choices[0].text}")
    bot.reply_to(message, response.choices[0].text)
    
bot.infinity_polling()