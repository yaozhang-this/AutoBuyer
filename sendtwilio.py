import os
from twilio.rest import Client


def send_simple_sms(message):
    # Your Account SID from twilio.com/console
    account_sid = "ACfe658f2f84d925ae798aa4969f876a81"
    # Your Auth Token from twilio.com/console
    auth_token = "43555cf2643bdde7eca018d853220a45"
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        to="+12022356153",
        from_="+14435122758",
        body=message)

    print(f"Twilio sid: {message.sid}")
