from openai import OpenAI
from flask import Flask, request
import json
import time
import os
import requests
from dotenv import load_dotenv, find_dotenv

app = Flask(__name__)

# Load environment variables
_ = load_dotenv(find_dotenv())

# Load your OpenAI API key
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Dictionary to store user-thread mappings
user_thread_mapping = {}

def verify_fb_token(token_sent):
    if token_sent == "BNL_1234!":
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

def read_user():
    try:
        with open('D:/bnl/meta/user/responses.txt', 'r', encoding='UTF-8') as file:
            data = file.read()
            txt = '{' + data[:-2] + '}'
            db = json.loads(txt)
            return db
    except Exception as e:
        print(e)
        return {}

def write_to_file(text, thread_id):
    try:
        with open(f'D:/bnl/meta/user/responses.txt', 'a', encoding='UTF-8') as file:
            file.write(f"{text:{text},thread_id:{thread_id}}"+'\n')
    except Exception as e:
        print(e)

def get_or_create_thread(user_id):
    if user_id in user_thread_mapping:
        return user_thread_mapping[user_id]
    thread = client.beta.threads.create()
    thread_id = thread.id
    print(thread_id)
    user_thread_mapping[user_id] = thread_id
    return thread_id

def get_assistant_responses(msg, user_id):
    thread_id = get_or_create_thread(user_id)
    # if not thread_id:
    #             # Create a new thread for the user
    #             thread = client.beta.threads.create()
    #             thread_id = thread.id
    #             # with open('user.txt', 'a') as file:
    #             #     file.write(f'"{user}":"{thread_id}",\n')
    #             print(f"Thread ID: {thread_id}")

    #         # Send message to the assistant
    print(thread_id)
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
                # write_to_file(answer,thread_id)
                return answer
    return "Response for user " + str(user_id)

def send_message(recipient_id, response):
    bot_message = {
        "recipient": {"id": recipient_id},
        "message": {"text": response}
    }
    response = requests.post("https://graph.facebook.com/v2.6/me/messages",
                             params={"access_token": "EAAPAoW5DI7UBOZBSqDadgYuhliZCDw6bkZB0aaq9jhpZC7Ir0wtgzgezFFYpZA6vznsm35NTKaqpd0CPqjuVTmkBwAyclIHzslZC2CyZCDQMlZBMv27Er65gWCDHxIogwrrSmfBY4vI9X7uZBHljFsDOiZBZBZAQkwVuIuFpKnjIz21H5GaOjRdDQcjXBb3ft036lenT"},
                             json=bot_message)
    return response.json()

processed_message_ids = set()

@app.route("/", methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    else:
        output = request.get_json()
        for event in output['entry']:
            messaging = event['messaging']
            print(messaging)
            for message in messaging:
                if message.get('message'):
                    recipient_id = message['sender']['id']
                    message_id = message['message'].get('mid')
                    if message_id and message_id not in processed_message_ids:
                        processed_message_ids.add(message_id)
                        if message['message'].get('text'):
                            message_text = message['message']['text']
                            if message_text.strip() != "":
                                response_text = get_assistant_responses(message_text, recipient_id)
                                send_message(recipient_id, response_text)
        return "Message Processed"

if __name__ == "__main__":
    app.run(port=5000, debug=True)
