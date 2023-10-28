from telegram.ext import *
from telegram import *
import logging
import os
from dotenv import load_dotenv
import requests
from states import *
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
import json

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
llm = OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.9)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

token = os.getenv('BOT_TOKEN')
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

current_user = {}


ZONES = ["Manhattan 🏙", "Brooklyn 🌉", "Queens 👑", "Staten Island 🛥️", "The Bronx 🦁"]

def initialize_user(update):
    global current_user
    if current_user.get(update.effective_chat.id) is None:
        current_user[update.effective_chat.id] = {}

def start(update, context):
    initialize_user(update)
    response = "Hello! 🌟 Could you please share any common problems you're facing in New York City that you would like to see resolved? Your voice matters! \n\nUse /feedback to share your thoughts. 🗽 Otherwise, we wish you a wonderful day ahead! ☀️"
    context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def feedback(update, context):
    initialize_user(update)
    buttons = []
    response = "We're on a mission to make New York City even better, and we'd love your insight! 🌆 First off, could you share where you're joining us from?"
    for zone in ZONES:
        zone_callback = zone[:-2]
        buttons.append([InlineKeyboardButton(zone, callback_data=zone_callback)])
    current_user[update.effective_chat.id]["state"] = PROVIDING_FEEDBACK_ZONE
    context.bot.send_message(chat_id=update.effective_chat.id, text=response,
                             reply_markup=InlineKeyboardMarkup(buttons))

def submit_feedback(feedback):
    # feedback uploaded to blockchain
    data = { "text": feedback }
    resp = requests.post("http://10.0.0.202:5001/feedback", json=data)

def generate_policy_with_location(all_feedback, target_location):
    context = "You are a policymaking advisor in " + target_location
    prompt = """The following are all the suggestions I have received. Look through all of them, understand the most common issues that people in your area are facing. Ignore the suggestions from other areas. Based on the main problems in your area, give me suggestions for policies that I, as a policymaker, need to urgently enact.

    In the response, use the following format EXACTLY, especially where line breaks are shown. Add an empty line between every section.
*Policy name:*
{insert policy name} (borough)

*Problem to solve:*
{insert problem to solve}

*Policy details:*
{insert policy details}    

I just need one policy to be suggested.
E.g.
*Policy name:*
Rent Stabilization for All

*Problem to solve:*
Increase access to affordable housing.

*Policy details:*
{insert policy details}  

    I just need one policy to be suggested.
    Here are the suggestions received:
    """
    for feedback in all_feedback:
        to_add = "\n" + feedback
        prompt += to_add

    resp = llm(context + prompt)
    print(resp)
    return resp

def generate_policy(all_feedback):
    prompt = """The following are all the suggestions I have received. As a policymaking advisor in New York City, look through all of them, understand the most common issues that people are facing, and give me suggestions for policies that I, as a policymaker, need to urgently enact.
    
    In the response, use the following format EXACTLY, especially where line breaks are shown. Add an empty line between every section.
*Policy name:*
{insert policy name} (borough)

*Problem to solve:*
{insert problem to solve}

*Policy details:*
{insert policy details}    

I just need one policy to be suggested.
E.g.
*Policy name:*
Rent Stabilization for All (Manhattan)

*Problem to solve:*
Increase access to affordable housing.

*Policy details:*
{insert policy details}  

Here are the suggestions received:
"""
    for feedback in all_feedback:
        to_add = "\n" + feedback
        prompt += to_add

    resp = llm(prompt)
    print(resp)
    return resp

def suggest(update, context):
    buttons = []
    for zone in ZONES:
        zone_callback = zone[:-2]
        buttons.append([InlineKeyboardButton(zone_callback, callback_data="suggest"+zone_callback)])
    buttons.append([InlineKeyboardButton("General", callback_data="suggestgeneral")])
    context.bot.send_message(chat_id=update.effective_chat.id, text="I can create a policy for you! Which area would you like it for?",
                             reply_markup=InlineKeyboardMarkup(buttons))
def retrieve_all_feedback():
    print("feedback retrieved")
    resp = requests.get("http://10.0.0.202:5001/feedback")
    resp_split = resp.text.split("get_messages()")[1]
    corrected_text = resp_split.replace("{ text:", '{ "text":').replace("'", '"')
    json_feedback = json.loads(corrected_text)
    feedback = []
    for k in json_feedback:
        print(k['text'])
    return feedback

def inline_query(update, context):
    initialize_user(update)
    query = update.callback_query.data
    update.callback_query.answer()
    context.bot.edit_message_reply_markup(
        message_id = update.callback_query.message.message_id,
        chat_id = update.callback_query.message.chat.id,
        reply_markup=None)
    state = current_user[update.effective_chat.id].get("state")
    if state == PROVIDING_FEEDBACK_ZONE:
        current_user[update.effective_chat.id]["zone"] = query
        context.bot.send_message(chat_id=update.effective_chat.id, text="Excellent! Could you please share any problems or areas of improvement that you have identified in " + query + "?")
        current_user[update.effective_chat.id]["state"] = PROVIDING_FEEDBACK
    elif query.startswith("suggest"):
        location = query[7:]
        all_feedback = retrieve_all_feedback()
        if "general" in query:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="General selected. Generating policy based on suggestions...")
            policy = generate_policy(all_feedback)
            context.bot.send_message(chat_id=update.effective_chat.id, text=policy, parse_mode= 'Markdown')

        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=location + " selected. Generating policy based on suggestions...")
            policy = generate_policy_with_location(all_feedback, location)
            context.bot.send_message(chat_id=update.effective_chat.id, text=policy, parse_mode= 'Markdown')

def message_handler(update, context):
    initialize_user(update)
    global current_user
    msg = update.message.text
    state = current_user[update.effective_chat.id].get("state")
    if state == PROVIDING_FEEDBACK:
        current_user[update.effective_chat.id]["suggestion"] = msg
        submit_feedback(current_user[update.effective_chat.id]["zone"] + ": " + msg)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for your valuable input! Your feedback is instrumental and will be considered in shaping policies to better serve the community here at " + current_user[update.effective_chat.id]["zone"] + ".")
        context.bot.send_message(chat_id=update.effective_chat.id, text="Have a great day! Run /feedback again if you would like to provide more feedback 😄")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm here seeking your help to improve policy-making in New York City. Run /start to get started.")


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

feedback_handler = CommandHandler('feedback', feedback)
dispatcher.add_handler(feedback_handler)

suggest_policies = CommandHandler('suggest', suggest)
dispatcher.add_handler(suggest_policies)

query_handler = CallbackQueryHandler(inline_query)
dispatcher.add_handler(query_handler)

catchall_handler = MessageHandler(Filters.text, message_handler)
dispatcher.add_handler(catchall_handler)

updater.start_polling()
updater.idle()