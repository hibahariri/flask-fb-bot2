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

fb_url = "https://graph.facebook.com/v2.6/me/messenger_profile?access_token={}".format(ACCESS_TOKEN)
data = {
    "get_started": {
        "payload": "help"
    }
}
headers = {
    'content-type': 'application/json'
}

gsresp = requests.post(fb_url, headers=headers, data=json.dumps(data)).json()

data4 = {
    "fields": [
        "persistent_menu"
    ]
}


# del_icbr = requests.delete(fb_url, headers=headers, data=json.dumps(data4)).json()

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
                recipient_id = message['sender']['id']
                if message.get('message'):
                    if message['message'].get('text'):
                        messaging_text = message['message']['text']
                    if message['message'].get('attachments'):
                        messaging_text = 'None'
                if message.get('postback'):
                    messaging_text = message['postback']['payload']
                    if messaging_text == 'help':
                        r = requests.get(
                            'https://graph.facebook.com/{}?fields=first_name,last_name,profile_pic&access_token={}'.format(
                                recipient_id, ACCESS_TOKEN)).json()
                        f_name = r['first_name']
                        greeting_text1 = "hello " + f_name
                        response_message = [greeting_text1, "text"]
                        send_message(recipient_id, response_message)
                        store_name(f_name)
            response_message = get_message(messaging_text)
            send_message(recipient_id, response_message)
    return "Message Processed"


def verify_fb_token(token_sent):
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


def connect_todb():
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
            conn = [db_con]
        else:
            conn = ["no connection"]
    return conn


def get_response(action, parameters):
    if action == "get-categories":
        records = get_categories()
        user_response = [records, "Generic template"]
    else:
        user_response = ["we will show yo our categories 2", "text"]
    return user_response


def get_message(message_sent):
    ai = apiai.ApiAI("5c09984323f1437682ce9c679eb5828f")
    request_api = ai.text_request()
    request_api.query = message_sent
    json_response = json.loads(request_api.getresponse().read().decode('utf-8'))
    result = json_response['result']
    action = result.get('action')
    if json_response['result']['fulfillment']['speech']:
        real_response = json_response['result']['fulfillment']['speech']
        user_response = [real_response, "text"]
    elif action is not None:
        parameters = []
        user_response = get_response(action, parameters)
    else:
        messages = json_response['result']['fulfillment']['messages']
        if messages is not None:
            messages_list = {k: v for d in messages for k, v in d.items()}
            if messages_list['payload'] is not None:
                custom_payload: dict = messages_list['payload']
                print(custom_payload)
        user_response = [custom_payload, "quick replies"]
    return user_response


def store_name(first_name):
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute("INSERT INTO user (username) values (%s)", (first_name,))
    con[0].commit()
    cur.close()
    con[0].close()
    print("MySQL connection is closed")
    return "done"


def get_categories():
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute("Select cat_name from category")
    records = cur.fetchall()
    cur.close()
    con[0].close()
    print("Total number of rows in Laptop is: ", cur.rowcount)
    return records


def send_message(recipient_id, response):
    if response[1] == "text":
        bot.send_text_message(recipient_id, response[0])
    elif response[1] == "quick replies":
        quick_replies = []
        records = response[0]
        for row in records:
            quick_replies.append({"content_type": "text", "title": row[0], "payload": row[0], })
        bot.send_message(recipient_id, {
            "text": "Pick a category:",
            "quick_replies": quick_replies
        })
    elif response[1] == "Generic template":
        Generic_replies = []
        records = response[0]
        for row in records:
            Generic_replies.append({
                "title": row[0],
                "image_url": "https://maps.googleapis.com/maps/api/staticmap?center=40.714%2c%20-73.998&zoom=12&size=100x70&key=AIzaSyB16ffMqfvPJ4cgTFyyNpllAbq3f-V1q-o",
                "buttons":
                    [
                        {
                            "type": "postback",
                            "title": "show more",
                            "payload": row[0]
                        },
                    ]})
        bot.send_generic_message(recipient_id, Generic_replies)
    else:
        bot.send_message(recipient_id, response[0])
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

    return "success"


if __name__ == "__main__":
    app.run()
