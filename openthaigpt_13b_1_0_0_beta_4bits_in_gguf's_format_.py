# -*- coding: utf-8 -*-
model_url = "https://huggingface.co/openthaigpt/openthaigpt-1.0.0-beta-13b-chat-gguf/resolve/main/ggml-model-q4_0.gguf"

from llama_index import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    ServiceContext,
)
from llama_index.llms import LlamaCPP
from llama_index.llms.llama_utils import (
    messages_to_prompt,
    completion_to_prompt,
)
from flask import Flask, request
import requests

app = Flask(__name__)

llm = LlamaCPP(
    # You can pass in the URL to a GGML model to download it automatically
    model_url=model_url,
    # optionally, you can set the path to a pre-downloaded model instead of model_url
    model_path=None,
    temperature=0.1,
    max_new_tokens=256,
    # llama2 has a context window of 4096 tokens, but we set it lower to allow for some wiggle room
    context_window=3900,
    # kwargs to pass to __call__()
    generate_kwargs={},
    # kwargs to pass to __init__()
    # set to at least 1 to use GPU
    model_kwargs={"n_gpu_layers": 43},
    # transform inputs into Llama2 format
    messages_to_prompt=messages_to_prompt,
    completion_to_prompt=completion_to_prompt,
    verbose=False,
)

def verify_fb_token(token_sent):
    if token_sent == " ":
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

def process_with_openai(text):
    response = llm.complete(text)
    print(response.text)
    return response.text

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
    print("process webhook")
    if request.method == 'GET':
        # Extract the token sent by Facebook
        token_sent = request.args.get("hub.verify_token")
        print("done")
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
                                    print(response_text)
                                    send_message(recipient_id, response_text)
        return "Message Processed"

if __name__ == "__main__":
    app.run(port=5000, debug=True)

# response = llm.complete("แปลภาษาไทยเป็นอังกฤษ: กรุงเทพมหานคร เป็นเมืองหลวงและนครที่มีประชากรมากที่สุดของประเทศไทย เป็นศูนย์กลางการปกครอง การศึกษา การคมนาคมขนส่ง การเงินการธนาคาร การพาณิชย์ การสื่อสาร และความเจริญของประเทศ")
# print(response.text)

# response = llm.complete("วางแผนเที่ยวในภูเก็ต แบบบริษัททัวร์: ภูเก็ต เป็นจังหวัดหนึ่งทางภาคใต้ของประเทศไทย และเป็นเกาะขนาดใหญ่ที่สุดในประเทศไทย อยู่ในทะเลอันดามัน จังหวัดที่ใกล้เคียงทางทิศเหนือ คือ จังหวัดพังงา ทางทิศตะวันออก คือ จังหวัดพังงา ทั้งเกาะล้อมรอบด้วยมหาสมุทรอินเดีย และยังมีเกาะที่อยู่ในอาณาเขตของจังหวัดภูเก็ตทางทิศใต้และตะวันออก การเดินทางเข้าสู่ภูเก็ตนอกจากทางเรือแล้ว สามารถเดินทางโดยรถยนต์ซึ่งมีเพียงเส้นทางเดียวผ่านทางจังหวัดพังงา โดยข้ามสะพานสารสินและสะพานคู่ขนาน คือ สะพานท้าวเทพกระษัตรีและสะพานท้าวศรีสุนทร เพื่อเข้าสู่ตัวจังหวัด และทางอากาศโดยมีท่าอากาศยานนานาชาติภูเก็ตรองรับ ท่าอากาศยานนี้ตั้งอยู่ทางทิศตะวันตกเฉียงเหนือของเกาะ")
# print(response.text)

# response = llm.complete("เขียนบทความเกี่ยวกับ 'ประโยชน์ของโกจิเบอร์รี่'")
# print(response.text)

# response = llm.complete("เขียนโค้ด python pandas csv export")
# print(response.text)

# response = llm.complete("x+30=100 x=?")
# print(response.text)

# response = llm.complete("จงอธิบายวิธีแก้สมการดังต่อไปนี้ x*2+30=100 x=?")
# print(response.text)

# """## Stream Response"""

# response_iter = llm.stream_complete("วิธีการลดความอ้วน")
# for response in response_iter:
#     print(response)
    # print(response.delta, end="", flush=True)

