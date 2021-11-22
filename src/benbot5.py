#!/usr/bin/env python3
#
# Uber, Inc. 2019
#
"""
Slack bot that posts the lunch menu when called. This text should be expanded upon.
"""

from datetime import datetime, timedelta
from dateutil import parser
from functools import partial, reduce
import logging
import sqlite3
import os
from random import choice
import re
import sys
from time import sleep
import traceback
from typing import List, Tuple

import calendar
import pygsheets
from slack import RTMClient, WebClient
import yaml

from benbot import get_root

with open(os.path.join(get_root(), 'config', 'config.yml')) as yml:
    CONFIG = yaml.safe_load(yml)
SERVICE_ACCOUNT_FILE = os.path.join(get_root(), 'config', 'service_account.json')
WEEK_DAYS = ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY')

logging.basicConfig(stream=sys.stdout, format='%(name)s - %(levelname)s - %(message)s')

sheets = pygsheets.authorize(service_account_file=SERVICE_ACCOUNT_FILE)

# creates a new sqlite db in memory, creates tables for lunch and dinner with a set structure mirroring the Sheet
con = sqlite3.connect(":memory:", check_same_thread=False)
con.isolation_level = None
cursor = con.cursor()
for table in ('lunch', 'dinner'):
    cursor.execute(f'CREATE TABLE {table} (year, week, monday, tuesday, wednesday, thursday, friday)')
con.commit()


def inticize(string: str) -> int:
    """
    Attempts to convert a string to an int, returns zero if unsuccessful.
    :param string: string (ideally numeric)
    :return: int version of the string arg, or 0
    """
    try:
        output = int(float(string))
    except ValueError:
        output = 0
    return output


def sync_db(**_):
    for table_name in ('lunch', 'dinner'):
        cursor.execute(f'DROP TABLE {table_name}')
        cursor.execute(f'CREATE TABLE {table_name} (year, week, monday, tuesday, wednesday, thursday, friday)')
        con.commit()
        wks = sheets.open_by_key(CONFIG['sheet_key']).worksheet_by_title(table_name)
        values = wks.get_all_values(include_tailing_empty=False, include_tailing_empty_rows=False)
        formatted_values = map(lambda x: (inticize(x[0]), inticize(x[1]), x[2], x[3], x[4], x[5], x[6]), values)
        cursor.executemany(f'INSERT INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?)', formatted_values)
        con.commit()
    logging.info('db sync')


def append_menu_to_g_sheet(menu: list, meal_type: str, week_number: int, year_number: int) -> None:
    """
    Appends the menu list to the Google Sheet, and then syncs the local sqlite db with the new info
    :param menu: List of the menu by the days, Monday - Friday
    :param meal_type: 'lunch' or 'dinner'
    :param week_number: number for the week of the year
    :param year_number: four-digit int of year number (e.g. 2019, 2020)
    """
    wks = sheets.open_by_key(CONFIG['sheet_key']).worksheet_by_title(meal_type)
    values = [year_number, week_number] + menu
    wks.append_table(values)
    sync_db()


def route(text: str):
    """
    Attempts to match a routable phrase with one used in the message received.
    :param text: The message text
    :return: A function for the routing if a match is found, else None
    """
    routing_dict = {
        'add-lunch': partial(add_meal, meal_type='lunch'),
        'add-dinner': partial(add_meal, meal_type='dinner'),
        'lunch': partial(post_meal, meal_type='lunch'),
        'dinner': partial(post_meal, meal_type='dinner'),
        'sync-db': sync_db
    }
    dict_match = reduce(lambda x, y: y if y in routing_dict else x, reversed(text.split(" ")), "")
    if dict_match:
        return routing_dict[dict_match]


@RTMClient.run_on(event='message')
def listen_for_lunch(**message):
    """
    Monitors Slack, listening for messages with a specific syntax (includes text, is sent either in a DM or in a
    whitelisted channel, includes a mention of the bot (either explicitly, or because it's a DM), and is not sent
    from the bot itself.
    :param message: The message object received.
    :return: Calls the function received if the message matches the syntax and includes a routable phrase, else None
    """
    logging.info(message)
    try:
        text = message['data']['text']
        channel = message['data']['channel']
        bot_users = CONFIG['bot_user'].values()
        if (
             text
             and (any(x in text for x in bot_users) or channel.startswith('D'))
             and message['data']['user'] not in bot_users
             and (channel.startswith('D') or channel in CONFIG['whitelist_channels'])
        ):
            result = route(text)
            if result:
                result(channel=message['data']['channel'], text=text, web_client=message['web_client'])
    except KeyError:
        return


def parse_lines_for_dates(text_list: List[str]) -> List[datetime]:
    """
    Parses the a list of strings, attempting to extract dates from them.
    :param text_list: List of strings, typically the splitlines of a week's lunch/dinner menu
    :return: List of datetime objects pulled from the list of strings
    """
    translation_table = str.maketrans({x: None for x in "(){}<>"})

    def parse_with_none(string):
        try:
            to_parse = string.translate(translation_table)
            output = parser.parse(to_parse)
        except ValueError:
            output = None
        return output

    numerics = filter(lambda x: any(y.isnumeric() for y in x), text_list)
    dates = {parse_with_none(x) for x in numerics}
    return [x for x in dates if x]


def parse_meal(meal_text: str) -> Tuple[dict, List[datetime]]:
    """
    Reads the text of a menu, returns a tuple[dict, list] of the menu broken up into days, and the extracted dates
    :param meal_text: The raw text from a weekly lunch/dinner menu
    :return: ({day_name:day_menu}, [datetime objects of extracted dates])
    """
    processed_text = strip_extra_newlines(meal_text)
    dates = parse_lines_for_dates(processed_text)
    meal_dict = parse_text_for_all_weekdays(processed_text)
    return meal_dict, dates


def parse_for_day(meal_text: str, day: str) -> str:
    """
    deprecated:: 5.2.0
    Use :func: parse_text_for_all_weekdays with already-split list instead
    Parses a full lunch menu for a specified day, returns the menu for just that day.
    :param meal_text: Full lunch menu
    :param day: Day of the week (MONDAY - FRIDAY)
    :return: The day's menu for the day specified.
    """
    day_menu = ""
    parsing = False
    for line in meal_text.splitlines():
        if day in line.upper():
            parsing = True
        elif any(weekday in line.upper() for weekday in WEEK_DAYS):
            parsing = False
        if parsing:
            if not any(weekday in line.upper() for weekday in WEEK_DAYS):
                day_menu += f'{line.strip()}\n'
    return day_menu


def parse_text_for_all_weekdays(text_list: List[str]) -> dict:
    """
    Parses a list of strings, returning a dict mapping each day's menu to its respective weekday
    :param text_list: Week menu splitlines, should not include empty items.
    :return:
    """
    def line_reduction(x: tuple, y: str):
        upper_y = y.upper()
        if any(z in upper_y for z in WEEK_DAYS):
            tracking_day = re.search(r'(MON|TUES|WEDNES|THURS|FRI)DAY', upper_y).group()
            update = {tracking_day: f"*{tracking_day}*\n"}
        else:
            tracking_day = x[0] or "MONDAY"
            update = {tracking_day: x[1].get(tracking_day) + y + "\n"}
        return tracking_day, {**x[1], **update}

    return reduce(line_reduction, text_list, ('', {z: "" for z in WEEK_DAYS}))[1]


def strip_extra_newlines(text: str) -> List[str]:
    """
    Strips any extra newlines, as well as any other unnecessary characters.
    :param text: multi-line text to strip
    :return: new-line-joined text with the excess newlines removed
    """
    return [y for y in (x.rstrip() for x in text.splitlines()) if y]


def parse_message_for_day(text: str) -> str:
    today = datetime.now().date()
    non_weekday_mappings = {
        'TODAY': calendar.day_name[today.weekday()].upper(),
        'TOMORROW': calendar.day_name[(today + timedelta(days=1)).weekday()].upper(),
        'WEEK': 'WEEK'
    }
    days = {**non_weekday_mappings, **{x: x for x in WEEK_DAYS}}
    upper_text = text.upper()
    day = reduce(lambda x, y: y if y in upper_text else x, days.keys(), '')
    if day:
        when = days[day]
    elif len(upper_text.split()) < 3:
        when = days['TODAY']
    else:
        when = ''
    return when


def post_meal(meal_type: str, channel: str, text: str, web_client: WebClient) -> None:
    date_dict = {**{"WEEK": '*'}, **{x: x.lower() for x in WEEK_DAYS}}
    when = parse_message_for_day(text)
    year, week, _ = datetime.now().isocalendar()
    cursor.execute(f'SELECT {date_dict[when]} FROM {meal_type} WHERE (week = ? AND year = ?)', (week, year))
    data = cursor.fetchone()
    if not data:
        output = ("Might be a hit or might be a miss, but I've got no idea what's for "
                  f"{meal_type}{text.lower().split(meal_type)[1] or ''}")
        icon_url = 'https://66.media.tumblr.com/601c897fb5e3dd47f5c6677d64203b2b/tumblr_ph4tw8HK1f1qiz4ulo1_400.png'
        username = 'NyanNyanBot'
    else:
        icon_url = choice(CONFIG['guy_fieri_images'])
        username = 'Flavorbot'
        if when == 'WEEK':
            data_iter = iter(data[2:])
            output = f'{meal_type} for week {week}:\n' + "\n".join(
                format_meal_output(x, next(data_iter)) for x in WEEK_DAYS)
        else:
            output = f"{meal_type} for {when}:\n{format_meal_output(when, data[0])}"
    web_client.chat_postMessage(
        channel=channel,
        text=output,
        as_user=False,
        icon_url=icon_url,
        username=username
    )


def add_meal(meal_type: str, channel: str, text: str, web_client: WebClient) -> None:
    parsed, dates = parse_meal(text)
    year, week, _ = datetime.now().isocalendar()
    append_menu_to_g_sheet(list(parsed.values()), meal_type, week, year)
    cursor.execute(f'SELECT * FROM {meal_type} WHERE (week = ? AND year = ?)', (week, year))
    try:
        data = cursor.fetchone()
        data_iter = iter(data[2:])
        header = f'{meal_type} for week {week}:\n'
        output = header + "\n".join(format_meal_output(x, next(data_iter)) for x in WEEK_DAYS)
    except (IndexError, TypeError):
        output = "Menu Update Error"
    web_client.chat_postMessage(
        channel=channel,
        text=output,
        as_user=True
    )


def format_meal_output(key, value):
    return f'*{key}*\n{value}'


def start_slack():
    slack_client = RTMClient(token=CONFIG['tokens']['slack_token'])
    logging.info('starting')
    slack_client.start()


def main():
    try:
        sync_db()
        start_slack()
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        logging.warning(f'exception!!! {e}')
        logging.warning(traceback.print_tb(e.__traceback__))
        sleep(10)
        main()


if __name__ == '__main__':
    main()
