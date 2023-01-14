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

# Telegram bot
telegram_token = os.getenv("TELEGRAM_API_KEY")

bot = telebot.TeleBot(telegram_token, parse_mode=None) # You can set parse_mode by default. HTML or MARKDOWN


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, msgs.welcome_msg)

@bot.message_handler(commands=['creator'])
def send_creator_info(message):
    bot.reply_to(message, msgs.creator_info)

@bot.message_handler(commands=['query'])
def send_query(message):
    prompt = message.text
    response = openai.Completion.create(model="text-davinci-003", prompt=prompt, temperature=0.5, max_tokens=100)
    bot.reply_to(message, response.choices[0].text)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    user_input = message.text
    base_prompt = f"User comes and says: {user_input} \n You want to say something nice to user, support him. Want to make he or she happy and reply with:"
    response = openai.Completion.create(model="text-davinci-003", prompt=base_prompt, temperature=0.5, max_tokens=100)
    bot.reply_to(message, response.choices[0].text)
    
bot.infinity_polling()