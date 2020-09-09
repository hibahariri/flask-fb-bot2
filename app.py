import random
import json
import requests
from flask import Flask, request
from pymessenger.bot import Bot
import apiai
import mysql.connector

app = Flask(__name__)  # Initializing our Flask application
ACCESS_TOKEN = 'EAAjWhObmBKgBANob0vUZBCjzaokbhx60vOQ7s2VmfWMi1G1vmIjSTZAY3ZAxk8V1fyoa4pFBHP8p4qZBsinyFEiCnvUVbSgi60YgNORoGajzCWfFrWfwZC2m0MIZBBcgXZBM4J5jfPpnIxyed6RLR13NkpZBc8IO6xPZAJXkkfbT1g77Tb9jl0BaghpJtP6YHBGIZD'
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
                    #  r = requests.get(
                    #     'https://graph.facebook.com/{}?fields=first_name,last_name,profile_pic&access_token={}'.format(
                    #          recipient_id, ACCESS_TOKEN)).json()
                    #  f_name = r['first_name']
                    # l_name = r['last_name']
                    if message['message'].get('text'):
                        messaging_text = message['message']['text']  # take message
                        response_sent_text = get_message(messaging_text)
                        send_message(recipient_id, response_sent_text)
                        store_name()
                    #  send_message(recipient_id, f_name)
                    if message['message'].get('attachments'):
                        messaging_text = 'None'
                        response_sent_text = get_message(messaging_text)
                        send_message(recipient_id, response_sent_text)
                if message.get('postback'):
                    recipient_id = message['sender']['id']
                    print(recipient_id)
                    messaging_text = message['postback']['payload']
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


def store_name():
    try:
        db_con = mysql.connector.connect(
            host="us-cdbr-east-02.cleardb.com",
            user="b3b214d3762ef4",
            passwd="4a2970a9",
            db="heroku_ff6cdbed3d2eb70")
    except mysql.connector.Error as error:
        print("Failed to connect to database in MySQL: {}".format(error))
    finally:
        if db_con.is_connected():
            name = 'hiba'
            cur = db_con.cursor()
            cur.execute("INSERT INTO user (username) values (%s)", (name,))
            db_con.commit()
            cur.close()
            db_con.close()
            print("MySQL connection is closed")
    return "done"


def send_message(recipient_id, response):
    bot.send_text_message(recipient_id, response)
    # image_url = "https://uploads.tapatalk-cdn.com/20180925/22c15c7ccc0fc977d07fd67fd424ff8d.jpg"
    # bot.send_image_url(recipient_id, image_url)
    buttons = [
        {
            "type": "postback",
            "title": "Plain shirts",
            "payload": "Plain shirts"
        },
        {
            "type": "postback",
            "title": "tie-die shirts",
            "payload": "tie-die"
        }
    ]
    bot.send_button_message(recipient_id, "choose your favourite type", buttons)
    reply_message = "Choose any number"
    reply_options = (["one", "shirts"], ["two", "shirts"])
    bot.send_quickreply(recipient_id, reply_message, reply_options)
    return "success"


if __name__ == "__main__":
    app.run()
