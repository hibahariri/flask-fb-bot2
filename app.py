import json
import requests
from flask import Flask, request, render_template, url_for, flash, redirect
from pymessenger.bot import Bot
import apiai
import DatabaseResponse
import os
from datetime import date
import math
import numpy as np

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = 'akbocTVre'
ACCESS_TOKEN = 'EAAjWhObmBKgBANob0vUZBCjzaokbhx60vOQ7s2VmfWMi1G1vmIjSTZAY3ZAxk8V1fyoa4pFBHP8p4qZBsinyFEiCnvUVbSgi60YgNORoGajzCWfFrWfwZC2m0MIZBBcgXZBM4J5jfPpnIxyed6RLR13NkpZBc8IO6xPZAJXkkfbT1g77Tb9jl0BaghpJtP6YHBGIZD'
VERIFY_TOKEN = 'abcVerTok'
bot = Bot(ACCESS_TOKEN)
Images = 'static/images/'
app.config['Images'] = Images

fb_url = "https://graph.facebook.com/v2.6/me/messenger_profile?access_token={}".format(ACCESS_TOKEN)
data = {
    "get_started": {
        "payload": "Get-Started"
    }
}
headers = {
    'content-type': 'application/json'
}

# Add get started button
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
                    "title": "Our Categories",
                    "payload": "what do you sell"
                },
                {
                    "type": "postback",
                    "title": "Opening Hours",
                    "payload": "Opening Hours"
                },
                {
                    "type": "postback",
                    "title": "My Profile",
                    "payload": "My Profile"
                }
            ]
        },
        {
            "locale": "en_us",
            "composer_input_disabled": "false",
            "call_to_actions": [
                {
                    "type": "postback",
                    "title": "Our Categories",
                    "payload": "what do you sell"
                },
                {
                    "type": "postback",
                    "title": "Opening Hours",
                    "payload": "Opening Hours"
                },
                {
                    "type": "postback",
                    "title": "My Profile",
                    "payload": "My Profile"
                }
            ]
        }
    ]
}

# Add persistent menu
pmresp = requests.post(fb_url, headers=headers, data=json.dumps(data2)).json()


# Receive requests from facebook
@app.route('/', methods=['GET', 'POST'])
def receive_message():
    global recipient_id
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
                    if message['message'].get('quick_reply'):
                        messaging_text = message['message']['quick_reply']['payload']
                        print(messaging_text)
                    elif message['message'].get('text'):
                        messaging_text = message['message']['text']
                    elif message['message'].get('attachments'):
                        messaging_text = 'None'
                if message.get('postback'):
                    messaging_text = message['postback']['payload']
            if messaging_text == 'Get-Started':
                # send request to facebook to return user information
                r = requests.get(
                    'https://graph.facebook.com/{}?fields=first_name,last_name,profile_pic&access_token={}'.format(
                        recipient_id, ACCESS_TOKEN)).json()
                f_name = r['first_name']
                greeting_text1 = "Welcome " + f_name + " to Mom's Mart, please type what you want or choose an option from the menu"
                response_message = [greeting_text1, "text"]
                DatabaseResponse.store_name(f_name, recipient_id)
            elif messaging_text[0:9] == "Products:":
                response_message = get_response("get_products", messaging_text[9:])
            elif messaging_text[0:7] == "Brands(":
                response_message = get_response("get_brands", messaging_text[7:-1])
            elif messaging_text[0:6] == "Items(":
                response_message = get_response("get_Items", messaging_text[6:-1])
            elif messaging_text[0:12] == "Add-to-cart(":
                response_message = get_response("Add_ToCart", messaging_text[12:-1])
            elif messaging_text == 'My Profile':
                records = []
                response_message = [records, "Button"]
            else:
                response_message = get_message(messaging_text)
            send_message(recipient_id, response_message)
    return "Message Processed"


# handles Order details web view
@app.route('/OrderDetails/<recid>/<ordid>', methods=['GET'])
def openOrder(recid, ordid):
    items = DatabaseResponse.get_orderitems(ordid)
    Totals = DatabaseResponse.get_orderAmount(ordid)
    Adr = DatabaseResponse.get_orderAddress(ordid)
    return render_template('OrderDetails.html', recid=recid, items=items, Totals=Totals, Adr=Adr, ordid=ordid)


# handles Orders web view
@app.route('/Order/<recid>', methods=['GET', 'POST'])
def ShowOrders(recid):
    if request.method == 'GET':
        Orders = DatabaseResponse.get_Orders(recid)
        pages = math.ceil(len(Orders) / 15)
        chunks = np.array_split(Orders, pages)
        return render_template('Order.html', Orders=Orders, recid=recid, chunks=chunks)
    else:
        print(request.form['fname'])
        return "submitted"


# handles Shipping Address web view
@app.route('/ShippingAddress/<recid>/<rec>', methods=['GET', 'POST'])
def fillAddress(recid, rec):
    if request.method == 'GET':
        return render_template('ShippingAddress.html', recid=recid, rec=rec)
    else:
        adr = [request.form['Fullname'], request.form['Address1'], request.form['Address2'], request.form['Phone']]
        ret = DatabaseResponse.fill_Address(recid, adr, rec)
        return render_template('OrderConfirmed.html', rec=rec)


@app.route('/OrderPlacement/<recid>', methods=['GET', 'POST'])
def PlaceOrder(recid):
    if request.method == 'GET':
        r = DatabaseResponse.get_orderpreview(recid)
        if r[0][0] is None:
            r.append(0)
            r.append(0)
        else:
            if r[0][0] > 49000:
                r.append("Free shipping")
                r.append(r[0][0])
            else:
                r.append(5000)
                r.append(r[0][0] + 5000)
        return render_template('OrderPlacement.html', recid=recid, Totals=r)
    else:
        rec = DatabaseResponse.create_order(recid)
        return redirect(url_for('fillAddress', recid=recid, rec=rec[0][0]))


# Handles myCart web view
@app.route('/Carts/<recid>', methods=['GET', 'POST'])
def get_cart(recid):
    if request.method == 'GET':
        items = DatabaseResponse.get_CartItem(recid)
        if not items:
            filename = os.path.join(app.config['Images'], 'favpng_shopping-cart-shiva-lingam.png')
            return render_template('NoCart.html', filename=filename, recid=recid)
        else:
            print(items)
            return render_template('Carts.html', items=items, recid=recid)

    else:
        qtyid = request.form.getlist('quantity')
        itemid = request.form.getlist('itemid')
        r = DatabaseResponse.Update_Cart(itemid, qtyid)
        # return redirect("PaymentDetails")
        return redirect(url_for('PlaceOrder', recid=recid))


def verify_fb_token(token_sent):
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


# handles non-text requests from user
def get_response(action, parameters):
    if action == "get-categories":
        records = DatabaseResponse.get_categories()
        user_response = [records, "Generic template", "Categories"]
    elif action == "Get_subcat":
        records = DatabaseResponse.get_subcat()
        user_response = [records, "Button"]
    elif action == "get_products":
        records = DatabaseResponse.get_products(parameters)
        user_response = [records, "quick replies", "Brands(", ""]
    elif action == "get_brands":
        records = DatabaseResponse.get_brands(parameters)
        user_response = [records, "quick replies", "Items(", parameters]
    elif action == "get-brand":
        parameters = parameters.get('products')
        if parameters == '':
            records = "Sorry we couldn't find what you're looking for"
            user_response = [records, "text"]
        else:
            records = DatabaseResponse.get_brands(parameters)
            user_response = [records, "quick replies", "Items(", parameters]
    elif action == "get_Items":
        print(parameters)
        records = DatabaseResponse.get_items(parameters)
        user_response = [records, "Generic template", "Items"]
    elif action == "get-Items":
        parameters = parameters.get('product-brand') + "," + parameters.get('products')
        print(parameters)
        records = DatabaseResponse.get_items(parameters)
        if not records:
            records = "Sorry we couldn't find what you're looking for"
            user_response = [records, "text"]
        else:
            user_response = [records, "Generic template", "Items"]
    elif action == "Add_ToCart":
        records = DatabaseResponse.Add_ToCart(parameters)
        user_response = [records, "text"]
    elif action == "get-category":
        parameters = parameters.get('product-type')
        if parameters == '':
            records = "Sorry I didn't understand what do you want"
            user_response = [records, "text"]
        else:
            records = DatabaseResponse.get_category(parameters)
            user_response = [records, "Generic template", "Categories"]
    elif action == "Send-location":
        print("location")
        record = DatabaseResponse.locationparam()
        records = [
            "https://maps.googleapis.com/maps/api/staticmap?size=764x400&center=33.877250,35.516510&zoom=25&markers=33.877250,35.516510",
            "http:\/\/maps.apple.com\/maps?q=33.877250,35.516510&z=16"]
        user_response = [records, "Generic template", "Location"]
    else:
        user_response = ["Test", "text"]
    return user_response


# handles text messages sent by user
# retrieve response from Dialog flow
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
        parameters = result.get('parameters')
        print(parameters)
        print(action)
        user_response = get_response(action, parameters)
    else:
        messages = json_response['result']['fulfillment']['messages']
        if messages is not None:
            messages_list = {k: v for d in messages for k, v in d.items()}
            if messages_list['payload'] is not None:
                custom_payload: dict = messages_list['payload']
        user_response = [custom_payload, "quick replies"]
    return user_response


# send message back to messenger
def send_message(recipient_id, response):
    if response[1] == "text":
        bot.send_text_message(recipient_id, response[0])
    elif response[1] == "quick replies":
        quick_replies = []
        records = response[0]
        for row in records:
            if not response[3]:
                payload = response[2] + row[0] + ")"
            else:
                payload = response[2] + row[0] + "," + response[3] + ")"
            quick_replies.append({"content_type": "text", "title": row[0], "payload": payload, })
        if response[2] == "Items(":
            text = "Brands"
        else:
            text = "Products"
        bot.send_message(recipient_id, {
            "text": "Choose from our availbale " + text,
            "quick_replies": quick_replies
        })
    elif response[1] == "Generic template":
        if response[2] == "Items":
            Generic_replies = []
            records = response[0]
            for row in records:
                Generic_replies.append({
                    "title": row[0],
                    "image_url": row[1],
                    "subtitle": row[2] + "     " + row[3],
                    "buttons":
                        [
                            {
                                "type": "postback",
                                "title": "Add to cart",
                                "payload": "Add-to-cart(" + row[0] + "," + recipient_id + ")",
                            },
                        ]})
        elif response[2] == "Location":
            Generic_replies = []
            records = response[0]
            for row in records:
                Generic_replies.append({
                    "title": "Location",
                    "image_url": "https://res-2.cloudinary.com/spinneys/image/upload/c_limit,dpr_2.0,f_auto,h_1800,q_auto,w_1800/v1/media/catalog/product/5/0/502927-v001-1_2.jpg",
                    "buttons":
                        [
                            {
                                "type": "postback",
                                "title": "show more",
                                "webview_height_ratio": "tall",
                                "url": "http:\/\/maps.apple.com\/maps?q=33.877250,35.516510&z=16",
                                "messenger_extensions": True
                            },
                        ]})
        else:
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
        records = recipient_id
        button = [{
            "type": "web_url",
            "title": "My Cart",
            "webview_height_ratio": "tall",
            "url": "https://fb-botapp2.herokuapp.com/Carts/" + records,
            "messenger_extensions": True
        },
            {
                "type": "web_url",
                "title": "My Orders",
                "webview_height_ratio": "tall",
                "url": "https://fb-botapp2.herokuapp.com/Order/" + records,
                "messenger_extensions": True
            },
        ]
        bot.send_button_message(recipient_id, " My Profile ", button)
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
