from flask import Flask, request
import requests
import datetime
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv, find_dotenv
import os
import openai

app = Flask(__name__)

# Load environment variables
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

# Initialize Flask app
app = Flask(__name__)

# Setup for LangChain
llm_name = "gpt-4-1106-preview"
file_path = 'data/แสนดี.pdf'
loader = PyPDFLoader(file_path)
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 10
    )

chunked_documents = text_splitter.split_documents(documents)
print(chunked_documents)
persist_directory = 'docs/chroma/'
embedding = OpenAIEmbeddings()
vectordb = Chroma.from_documents(
        documents=chunked_documents,
        embedding=embedding,
        persist_directory=persist_directory
    )

llm = ChatOpenAI(model_name=llm_name, temperature=0.1)

template = """
You are a female assistant and you will never change your gender.
When asked about your background story you will use information in the Retrieval file that was given.
if question is out of context you can answer by use common sense.
เธอเป็นผู้ช่วยที่จะใช้ข้อมูลด้านล่าง
ชื่อ:  แสนดี อายุ 25 พนักงานออฟฟิศ เพศ หญิง
ที่อยู่: สยาม
คำพูดแทนตัวเอง: เรา
คำพูดลงท้าย: ขา, น้า, ค่าาา
วิธีทักทาย: ดีจ้าาา อันยองงง ทำรายยยย ทำไรอะ ดีงับ ว่างอะป่าว ว่างไหมมม
วิธีขอโทษ: ขอโทษ โทษทีน้า งือๆ ผิดไปแล้ว แหะๆ  หว่าย  เค้าขอโทษ ขอโทษน้าาาา                                                                                
วิธีบอกลา: บ๊ายบาย ไปก่อนน้า บัยๆ บรัย เจอกาน   ไปละนะ เฟี้ยว
วิธีการตอบรับ: จ้า อะจ้า ค่า ว่างาย
วิธีเรียกคนอื่น: เธอ
ตอบคำถามแต่ละครั้งด้วยคำพูดไม่เกิน 20 คำ
Negative prompt: You will never use word ครับ/ค่ะ:
------
<ctx>
{context}
</ctx>
------
<hs>
{history}
</hs>
------
{question}
Answer:
"""
prompt = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=template,
)

retriever=vectordb.as_retriever()
qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(),
    chain_type='stuff',
    retriever=retriever,
    verbose=True,
    chain_type_kwargs={
        "verbose": True,
        "prompt": prompt,
        "memory": ConversationBufferMemory(
            memory_key="history",
            input_key="question"),
        }
    )

def verify_fb_token(token_sent):
    if token_sent == " ":
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

def process_with_openai(text):
    return qa.run({"query":text})

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


