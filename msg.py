from flask import Flask, request
import requests
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
import time
_ = load_dotenv(find_dotenv()) # read local .env file


app = Flask(__name__)
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# file = client.files.create(
#         file=open("data/แสนดี(shortest)(1).pdf", "rb"),
#         purpose='assistants'
#     )
# file_id = file.id

assistant = client.beta.assistants.retrieve(" ")
assistant_id = assistant.id

def verify_fb_token(token_sent):
    if token_sent == "BNL_1234!":
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

def process_with_openai(text):
    # Create Thread
    thread = client.beta.threads.create(
        messages=[{"role": "user", "content": text}]
    )
    thread_id = thread.id

    # Create Run
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=" ",
        # file_ids=file_id
    )
    run_id = run.id

    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        print("------------------------")
        if run.status == 'completed':
            thread_messages = client.beta.threads.messages.list(thread_id)
            if thread_messages:
                print("sucess")
                return str(thread_messages.data[0].content[0].text.value)
            break
        print('>> Waiting 5 seconds before checking again...')
        time.sleep(5)
    return "error"

def send_message(recipient_id, response):
    bot_message = {
        "recipient": {"id": recipient_id},
        "message": {"text": response}
    }
    response = requests.post("https://graph.facebook.com/v2.6/me/messages",
                             params={"access_token": " "},
                             json=bot_message)
    return response.json()

processed_message_ids = set()
@app.route("/", methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Extract the token sent by Facebook
        token_sent = request.args.get("hub.verify_token")
        # Call the verify function with the token
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
                                    response_text = process_with_openai(message_text)
                                    send_message(recipient_id, response_text)
        return "Message Processed"

if __name__ == "__main__":
    app.run(port=5000, debug=True)
