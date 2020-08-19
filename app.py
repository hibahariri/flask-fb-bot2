import random
import json
import requests
from flask import Flask, request
from pymessenger.bot import Bot
import apiai
import mysql.connector

app = Flask(__name__)  # Initializing our Flask application
ACCESS_TOKEN = 'EAAjWhObmBKgBAK3U2gBhclZB1fEZBPKZBEWbbJNksbzC9dthq8pPWnZBAFj6K8CZAifTm2jnYvwKFiZBh8C2SyfbscCWiYeUlCQ5PXzO8kwu7xZAer00rRdbgWVQFoFoPxYnXxWYkehZBMLhApJitqbKixaUNAtoq1c9jpik8SyZBOpgDxDUhpJPysuciGyxcsfAZD'
VERIFY_TOKEN = 'abcVerTok'
bot = Bot(ACCESS_TOKEN)


@app.route('/', methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    else:
        output = request.get_json()
        for event in output['entry']:
            messaging = event['messaging']
            for message in messaging:
                if message.get('message'):
                    recipient_id = message['sender']['id']
                    r = requests.get(
                        'https://graph.facebook.com/{}?fields=first_name,last_name,profile_pic&access_token={}'.format(
                            recipient_id, ACCESS_TOKEN)).json()
                    f_name = r['first_name']
                    l_name = r['last_name']
                    if message['message'].get('text'):
                        messaging_text = message['message']['text']  # take message
                        response_sent_text = get_message(messaging_text)
                        send_message(recipient_id, response_sent_text)
                        store_name(f_name)
                    #  send_message(recipient_id, f_name)
                    # if user send us a GIF, photo, video or any other non-text item
                    if message['message'].get('attachments'):
                        messaging_text = 'None'
                        response_sent_text = get_message(messaging_text)
                        send_message(recipient_id, response_sent_text)
    return "Message Processed"


def verify_fb_token(token_sent):
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


def get_message(message_sent):
    ai = apiai.ApiAI("5c09984323f1437682ce9c679eb5828f")
    request_api = ai.text_request()
    request_api.query = message_sent
    response = request_api.getresponse()
    json_response = json.loads(response.read().decode('utf-8'))
    user_response = json_response['result']['fulfillment']['speech']
    return user_response


def store_name(name):
    try:
        db_con = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="kee2seekwel",
            db="testdb")
    except mysql.connector.Error as error:
        print("Failed to create table in MySQL: {}".format(error))
    cur = db_con.cursor()
    cur.execute("INSERT INTO Users (userName) values (%s)", name)
    db_con.commit()
    db_con.close()
    return "done"


def send_message(recipient_id, response):
    # sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"


if __name__ == "__main__":
    app.run()
