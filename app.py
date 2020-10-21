import json
import requests
from flask import Flask, request, render_template
from pymessenger.bot import Bot
import apiai
import DatabaseResponse

app = Flask(__name__, template_folder="templates")  # Initializing our Flask application
ACCESS_TOKEN = 'EAAjWhObmBKgBANob0vUZBCjzaokbhx60vOQ7s2VmfWMi1G1vmIjSTZAY3ZAxk8V1fyoa4pFBHP8p4qZBsinyFEiCnvUVbSgi60YgNORoGajzCWfFrWfwZC2m0MIZBBcgXZBM4J5jfPpnIxyed6RLR13NkpZBc8IO6xPZAJXkkfbT1g77Tb9jl0BaghpJtP6YHBGIZD'
VERIFY_TOKEN = 'abcVerTok'
bot = Bot(ACCESS_TOKEN)

fb_url = "https://graph.facebook.com/v2.6/me/messenger_profile?access_token={}".format(ACCESS_TOKEN)
data = {
    "get_started": {
        "payload": "Get-Started"
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

data2 = {
    "persistent_menu": [
        {
            "locale": "default",
            "composer_input_disabled": "false",
            "call_to_actions": [
                {
                    "type": "postback",
                    "title": "Our Departments",
                    "payload": "Categories"
                },
                {
                    "type": "postback",
                    "title": "Opening Hours",
                    "payload": "Opening Hours"
                },
                {
                    "type": "web_url",
                    "title": "My Profile",
                    "url": "https://www.originalcoastclothing.com/",
                    "webview_height_ratio": "full"
                }
            ]
        },
        {
            "locale": "en_us",
            "composer_input_disabled": "false",
            "call_to_actions": [
                {
                    "type": "postback",
                    "title": "Our Departments",
                    "payload": "Categories"
                },
                {
                    "type": "postback",
                    "title": "Opening Hours",
                    "payload": "Opening Hours"
                },
                {
                    "type": "web_url",
                    "title": "My Profile",
                    "url": "https://www.originalcoastclothing.com/",
                    "webview_height_ratio": "full"
                }
            ]
        }
    ]
}

pmresp = requests.post(fb_url, headers=headers, data=json.dumps(data2)).json()


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
                    if messaging_text == 'Get-Started':
                        print(messaging_text)
                        r = requests.get(
                            'https://graph.facebook.com/{}?fields=first_name,last_name,profile_pic&access_token={}'.format(
                                recipient_id, ACCESS_TOKEN)).json()
                        f_name = r['first_name']
                        greeting_text1 = "hello " + f_name
                        response_message = [greeting_text1, "text"]
                        send_message(recipient_id, response_message)
                        DatabaseResponse.store_name(f_name,recipient_id)
            if messaging_text[0:9] == "Products:":
                response_message = get_response("get_products", messaging_text[9:])
            else:
                response_message = get_message(messaging_text)
            send_message(recipient_id, response_message)
    return "Message Processed"


@app.route('/index', methods=['GET', 'POST'])
def success():
    if request.method == 'GET':
        print("done")
        return render_template('index.html')
    else:
        print(request.form['fname'])
        return "submitted"


@app.route('/PaymentDetails', methods=['GET'])
def openPayments():
    print("done")
    return render_template('PaymentDetails.html')


def verify_fb_token(token_sent):
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


def get_response(action, parameters):
    if action == "get-categories":
        records = DatabaseResponse.get_categories()
        user_response = [records, "Generic template"]
    elif action == "Get_subcat":
        records = DatabaseResponse.get_subcat()
        user_response = [records, "Button"]
    elif action == "get_products":
        records = DatabaseResponse.get_products(parameters)
        user_response = [records, "quick replies"]
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


def send_message(recipient_id, response):
    if response[1] == "text":
        bot.send_text_message(recipient_id, response[0])
        URL_button = [{
            "type": "web_url",
            "title": "Webview example",
            "webview_height_ratio": "tall",
            "url": "https://fb-botapp2.herokuapp.com/index",
            "messenger_extensions": True
        }, ]
        bot.send_button_message(recipient_id, "choose your favourite type", URL_button)
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
                "image_url": row[2],
                "buttons":
                    [
                        {
                            "type": "postback",
                            "title": list(row[3].split(','))[0],
                            "payload": "Products:" + list(row[3].split(','))[0],
                        },
                        {
                            "type": "postback",
                            "title": list(row[3].split(','))[1],
                            "payload": "Products:" + list(row[3].split(','))[1],
                        },
                        {
                            "type": "postback",
                            "title": list(row[3].split(','))[2],
                            "payload": "Products:" + list(row[3].split(','))[2],
                        }
                    ]})
        bot.send_generic_message(recipient_id, Generic_replies)
    elif response[1] == "Button":
        records = response[0]
        print(records)
        button = [{"type": "postback",
                   "title": " ",
                   "payload": " ",
                   }, ]
        bot.send_button_message(recipient_id, " a ", button)
    else:
        Generic_replies = []
        records = response[0]
        for row in records:
            Generic_replies.append({
                "title": row[0],
                "buttons":
                    [
                        {
                            "type": "postback",
                            "title": "show more",
                            "payload": row[0],
                        },
                    ]})
        bot.send_generic_message(recipient_id, Generic_replies)
    return "success"


if __name__ == "__main__":
    app.run()
