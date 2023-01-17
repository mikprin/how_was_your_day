
# Idea and realization

Telegram bot that asks you how was your day and sends results to GPT-3 API. GPT-3 generates an answer and sends it back to you.

Now bot supports memory of the last 24 hours. It means that you can ask bot how was your day yesterday and it will remember it.

Under the hood it uses GPT-3 API and Telegram API. And redis for storing user data.
# Deployment
Simplest deployment is to use docker-compose. Just run `docker-compose up -d` and you are ready to go.

Dont forget to set up your environment variables in `.env` file. Or copy example one and change it to your needs.

# Structure
Source is located in `how_was_your_day` folder