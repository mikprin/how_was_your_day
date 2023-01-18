# File with code for the telegram bot
CLEANUP_INTERVAL = 60*60

# Importing libraries
import logging, dotenv, os, sys, threading, time
import redis
import telebot
import openai

# Local imports
import msgs
import redis_tools

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

# Redis database

redis_hosts = os.getenv("REDIS_HOSTS").split(",")
redis_port = os.getenv("REDIS_PORT")


connected_to_redis = False
for host in redis_hosts:
    connection = redis.Redis(
    host=host,
    port=redis_port,
    )
    try:
        if connection.ping():
            logging.info(f"Connected to redis host {host}")
            connected_to_redis = True
            redis_connection = connection
            break
    except Exception as e:
        logging.error(f"Could not connect to redis host {host}: {e}")
if not connected_to_redis:
    logging.error("Could not connect to redis")
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

logger = telebot.logger
telebot.logger.setLevel(logging.WARNING) # Outputs debug messages to console.

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


# Create thread to clean redis database
def clean_redis():
    while True:
        logging.info(f"Cleaning redis database. Time: {time.time()}")
        redis_tools.databse_garbage_collector(redis_connection)
        time.sleep(CLEANUP_INTERVAL)

cleanup_thread = threading.Thread(target=clean_redis)
cleanup_thread.start()
logging.info(f"Cleanup thread started with interval {CLEANUP_INTERVAL} seconds")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_info = get_user_info(message)
    database_user_key = f"user_{user_info['user_id']}"
    if not redis_tools.check_if_user_exists(redis_connection, database_user_key, redis_tools.ALL_USERS):
        redis_tools.add_user_to_redis(redis_connection, database_user_key)
    logging.info(f"User with nickname {user_info['user_username']} started the bot.")
    bot.reply_to(message, msgs.welcome_msg)

@bot.message_handler(commands=['creator'])
def send_creator_info(message):
    user_info = get_user_info(message)
    logging.info(f"User with nickname {user_info['user_username']} requested info about creator.")
    bot.reply_to(message, msgs.creator_info)

@bot.message_handler(commands=['query'])
def send_query(message):
    prompt = message.text.replace("/query", "")
    user_info = get_user_info(message)
    logging.info(f"User with nickname {user_info['user_username']} query input: {prompt} with command: query")
    response = openai.Completion.create(model="text-davinci-003", prompt=prompt, temperature=0.5, max_tokens=max_tokens)
    logging.info(f"Bot response: {response.choices[0].text}")
    bot.reply_to(message, response.choices[0].text)

@bot.message_handler(commands=['delete_conversation'])
def delete_conversation(message):
    '''Deletes conversation from redis database'''
    user_info = get_user_info(message)
    logging.info(f"User with nickname {user_info['user_username']} requested to delete conversation.")
    redis_tools.delete_interactions(redis_connection, user_info['user_username'])
    bot.reply_to(message, "Conversation deleted 😎")

@bot.message_handler(func=lambda message: True)
def gpt_response(message):
    '''Main function that handles user input and sends response from GPT-3'''
    user_input = message.text
    user_info = get_user_info(message)
    logging.info(f"User with nickname {user_info['user_username']} query input: {user_input}.")
    
    # Adding user to redis database if not exists
    if not redis_tools.check_if_user_exists(redis_connection, user_info['user_username'] , redis_tools.ALL_USERS):
        redis_tools.add_user_to_redis(redis_connection, user_info['user_username'])
    
    # Understaning if user is active or not
    if redis_tools.check_if_user_exists(redis_connection, user_info['user_username'], redis_tools.ACTIVE_USERS):
        conversation = redis_tools.read_conversation(redis_connection, user_info['user_username'])
        # Concatenating user input with previous conversation
        all_conversation = f""
        for line in conversation:
            all_conversation += line.decode("utf-8")
        # starting conversation
        base_prompt = f"You have a following conversation with {user_info['user_name']}:\n{all_conversation}\nYou want to say something nice to {user_info['user_name']}, support him or her. Want to make he or she happy so reply with:"
    else: 
        user_said = f"{user_info['user_name']}: {user_input}\n"
        redis_tools.add_conversation(redis_connection, user_info['user_username'], user_said)
        base_prompt = f"{user_info['user_name']} comes and says to you: {user_input}. You want to say something nice to {user_info['user_name']}, support him or her. Want to make he or she happy and reply with:"
    
    # Generating response
    response = openai.Completion.create(model="text-davinci-003", prompt=base_prompt, temperature=0.5, max_tokens=max_tokens)
    you_said = f"You: {response.choices[0].text}\n"
    redis_tools.add_conversation(redis_connection, user_info['user_username'], you_said)
    logging.info(f"Bot response: {response.choices[0].text}")
    bot.reply_to(message, response.choices[0].text)

    
bot.infinity_polling()