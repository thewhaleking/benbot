from datetime import datetime, timedelta
from functools import reduce
import json
import logging
from pprint import PrettyPrinter
from random import choice
import sys

from slack_sdk import WebClient
from quart import Quart, request

from src import CONFIG
from src.get_menu import Cafe

WEEK_DAYS = ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY')

logging.basicConfig(stream=sys.stdout, format='%(name)s - %(levelname)s - %(message)s')
pp = PrettyPrinter(indent=4)

app = Quart(__name__)
web_client = WebClient(CONFIG["tokens"]["slack_token"])
cafes = {
    x: Cafe(y) for (x, y) in CONFIG["cafes"].items()
}


@app.route("/mention", methods=["POST"])
async def mentioned():
    data = json.loads(await request.data)
    event = data["event"]
    channel = event["channel"]
    if "lunch" in event["text"]:
        post_meal("lunch", channel, event["text"])
    return "ok"


def parse_message_for_day(text: str) -> datetime:
    """
    Attempts to determine the date for the meal requested, based on the Slack message. If no date can be determined,
    today's date is returned.
    :param text: the Slack message to parse
    """
    today = datetime.now().date()
    week_dict = {
        "MONDAY": 0,
        "TUESDAY": 1,
        "WEDNESDAY": 2,
        "THURSDAY": 3,
        "FRIDAY": 4
    }
    non_weekday_mappings = {
        'TODAY': today,
        'TOMORROW': today + timedelta(days=1),
        'YESTERDAY': today - timedelta(days=1)
    }
    days = {**non_weekday_mappings, **week_dict}
    upper_text = text.upper()
    day = reduce(lambda x, y: y if y in upper_text else x, days.keys(), '')
    if day:
        if day in non_weekday_mappings:
            when = non_weekday_mappings[day]
        else:
            when = today - timedelta(days=today.weekday()) + timedelta(days=week_dict[day])
    elif len(upper_text.split()) < 3:
        when = non_weekday_mappings['TODAY']
    else:
        when = None
    return when


def get_cafe(text) -> Cafe:
    """
    Determines the café to post from, based on the message. Returns the default café if the message doesn't contain
    a café nickname (as specified in the config.yml file)
    :param text: the message posted to Slack requesting the message
    """
    for (cafe_name, cafe_) in cafes.items():
        if cafe_name in text:
            return cafe_
    else:
        return cafes["default"]


def post_meal(meal_type: str, channel: str, text: str) -> None:
    """
    Determines the meal text, and posts it to the Slack channel the original message was posted in.
    :param meal_type: 'lunch' or 'dinner'
    :param channel: the Slack channel ID that the message was posted in
    :param text: the text of the original message
    """
    cafe = get_cafe(text)
    when = parse_message_for_day(text)
    if not when:
        data = None
    else:
        data = cafe.menu_items(when.strftime("%Y-%m-%d"))
    if not data:
        output = (
            f"I'm sure it'll be {choice(CONFIG['guy_fieri_phrases'])}, but I've got no idea what's for "
            f"{meal_type}{text.lower().split(meal_type)[1] or ''}"
        )
    else:
        output = f"{meal_type} for {when}:\n{data}"
    web_client.chat_postMessage(
        channel=channel,
        text=output,
        icon_url=choice(CONFIG['guy_fieri_images']),
        username='Flavorbot'
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
