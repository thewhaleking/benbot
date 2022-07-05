import asyncio
from datetime import datetime, timedelta, date, timezone
import json
import logging
from random import choice
import sys
from typing import Optional, Tuple, List

from slack_sdk import WebClient
from quart import Quart, request

from src import CONFIG
from src.get_menu import Cafe

WEEK_DAYS = ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY')
MEAL_TYPES = ("LUNCH", "DINNER")

logging.basicConfig(stream=sys.stdout, format='%(name)s - %(levelname)s - %(message)s')

app = Quart(__name__)
web_client = WebClient(CONFIG["tokens"]["slack_token"])
cafes = {
    x: Cafe(y["company"], y["name"]) for (x, y) in CONFIG["cafes"].items()
}


@app.route("/mention", methods=["POST"])
async def mentioned():
    data = json.loads(await request.data)
    event = data["event"]
    channel = event["channel"]
    event_text = str(event["text"]).lower()
    if "lunch" in event_text:
        # Slack requires a response within 3000ms, so this is done asynchronously while a response is sent immediately
        # to avoid multiple requests coming through for longer-running tasks (such as the full week's menu)
        asyncio.create_task(post_meal("lunch", channel, event["text"]))
    elif "help" in event_text:
        asyncio.create_task(help_text(channel))
    return "ok"


@app.before_serving
async def preload():
    """
    Executed at app startup
    """
    # asyncio.create_task(catia.get_part_number("prd"))
    for cafe in cafes.values():
        await cafe.initialize_session()


@app.after_serving
async def shutdown():
    """
    Executed at app shutdown
    """
    for cafe in cafes.values():
        await cafe.req.close()


async def help_text(channel: str):
    output = "\n".join(
        [
            "Flavorbot Usage Guide:",
            "Construct your message in the following format: ",
            "'@Benbot {cafe (optional)} lunch {day (optional)}.'",
            "For example, to get the default cafe's menu for today, you can simply type:",
            "'@Benbot lunch'",
            "To get the menu for HQ on Friday, you can type:",
            "'@Benbot hq lunch Friday'",
            "The following are valid cafes:",
            " - " + ", ".join(CONFIG["cafes"].keys()),
            "The following are valid days:",
            " - Today, Tomorrow, Yesterday, Monday, Tuesday, Wednesday, Thursday, Friday, Week"
        ]
    )
    return web_client.chat_postMessage(
        channel=channel,
        text=output,
        icon_url=choice(CONFIG['guy_fieri_images']),
        username='Flavorbot'
    )


def parse_message_for_day(text: str, utc_offset: int = 0) -> Optional[List[date]]:
    """
    Attempts to determine the date for the meal requested, based on the Slack message. If no date can be determined,
    today's date is returned.
    :param text: the Slack message to parse
    :param utc_offset: UTC offset for the time zone of the café in question
    """
    today = (datetime.now(timezone.utc) + timedelta(hours=utc_offset)).date()
    week_start = today - timedelta(today.weekday())
    day_mappings = {
        'TODAY': [today],
        'TOMORROW': [today + timedelta(days=1)],
        'YESTERDAY': [today - timedelta(days=1)],
        'MONDAY': [week_start],
        'TUESDAY': [week_start + timedelta(days=1)],
        'WEDNESDAY': [week_start + timedelta(days=2)],
        'THURSDAY': [week_start + timedelta(days=3)],
        'FRIDAY': [week_start + timedelta(days=4)],
        'WEEK': [
            week_start,
            week_start+timedelta(days=1),
            week_start + timedelta(days=2),
            week_start + timedelta(days=3),
            week_start + timedelta(days=4),
        ]
    }
    upper_text = text.upper()
    if any(upper_text.split()[-1] == x for x in MEAL_TYPES):
        return [today]
    for day, date_ in day_mappings.items():
        if day in upper_text:
            return date_


def get_cafe(text) -> Tuple[Cafe, int]:
    """
    Determines the café to post from, based on the message. Returns the default café if the message doesn't contain
    a café nickname (as specified in the config.yml file)
    :param text: the message posted to Slack requesting the message
    """
    u_text = text.upper()
    for (cafe_name, cafe_) in cafes.items():
        if cafe_name.upper() in u_text:
            return cafe_, CONFIG["cafes"][cafe_name]["utc_offset"]
    else:
        return cafes["default"], CONFIG["cafes"]["default"]["utc_offset"]


async def post_meal(meal_type: str, channel: str, text: str) -> None:
    """
    Determines the meal text, and posts it to the Slack channel the original message was posted in.
    :param meal_type: 'lunch' or 'dinner'
    :param channel: the Slack channel ID that the message was posted in
    :param text: the text of the original message
    """
    def post_message(post_text: str, timestamp=None):
        return web_client.chat_postMessage(
            channel=channel,
            text=post_text,
            icon_url=choice(CONFIG['guy_fieri_images']),
            username='Flavorbot',
            thread_ts=timestamp
        )

    async def get_data(date_: date) -> Tuple[str, str, str, str]:
        try:
            items = await cafe.menu_items(date_.strftime("%Y-%m-%d"))
        except LookupError:
            items = f"Unable to retrieve menu items."
        return (
            meal_type,
            cafe.cafe_name,
            date_.strftime('%m/%d/%Y'),
            items
        )

    cafe, utc_offset = get_cafe(text)
    when = parse_message_for_day(text, utc_offset)
    if not when:
        post_message(
            f"I'm sure it'll be {choice(CONFIG['guy_fieri_phrases'])}, but I've got no idea what's for "
            f"{meal_type}{text.lower().split(meal_type)[1] or ''}"
            "\nFor a usage guide, type '@Benbot help'"
        )
    else:
        data = await asyncio.gather(*[get_data(date_) for date_ in when])
        for (meal, cafe_name, meal_date, output) in data:
            ts = post_message(f"{meal} for {cafe_name} on {meal_date}")["ts"]
            post_message(output, timestamp=ts)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
