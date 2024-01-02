from openai import OpenAI
from flask import Flask, request
import json
import time
import os
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())  # read local .env file

app = Flask(__name__)
# Load your OpenAI API key
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def verify_fb_token(token_sent):
    if token_sent == "BNL_1234!":
        return request.args.get("hub.challenge")
    return 'Invalid verification token'
# Read user data from file
def read_user():
    try:
        with open('D:/bnl/meta/user/responses.txt', 'r') as file:
            data = file.read()
            txt = '{' + data[:-2] + '}'
            db = json.loads(txt)
            return db
    except Exception as e:
        print(e)
        return {}

def write_to_file(user, text,thread_id):
    try:
        with open(f'D:/bnl/meta/user/responses.txt', 'a',encoding='UTF-8') as file:
            file.write(f"user:{user},text:{text},thread_id:{thread_id} "+'\n')
    except Exception as e:
        print(e)

# Get assistant response for 10 rounds of messaging
def get_assistant_responses(user):
    db = read_user()
    for i in range(10):
        msg = input(f"Round {i+1}, enter your message: ")
        answer = 'Please ask again.'
        if user and msg:
            thread_id = db.get(user)
            if not thread_id:
                # Create a new thread for the user
                thread = client.beta.threads.create()
                thread_id = thread.id
                db[user] = thread_id
                # with open('user.txt', 'a') as file:
                #     file.write(f'"{user}":"{thread_id}",\n')
                print(f"New user: {user}, Thread ID: {thread_id}")

            # Send message to the assistant
            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=msg
            )

            # Run the assistant
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id="asst_wpegT5qk3IecHfYgAb31PIQh"  # Specify your assistant ID
            )
            run_id = run.id
            # Wait for the run to complete
            while True:
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
                if run.status in ['completed', 'expired', 'failed', 'cancelled']:
                    break
                time.sleep(3)

            # Process completed response
            if run.status == 'completed':
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                answer = messages.data[0].content[0].text.value
                print(answer)
                write_to_file(user, answer,thread_id)

# Get user ID and call the function
user = input("User ID: ")
get_assistant_responses(user)
