import logging
import os
from twilio.rest import Client


def send_simple_sms(message):

    """
    send_simple_sms sends SMS messages to its recipient(s)

    :param message: string message to be sent

    :return None
    """

    ACCOUNT_SID = os.getenv("ACCOUNT_SID")
    AUTH_TOKEN = os.getenv("AUTH_TOKEN")
    RECIPIENT = os.getenv("RECIPIENT")
    SENDER = os.getenv("SENDER")
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    message = client.messages.create(
     to=RECIPIENT,
     from_=SENDER,
     body=message)

    logging.info(f"Twilio sid: {message.sid}")
