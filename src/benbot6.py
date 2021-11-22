from functools import partial, reduce
import logging
from pprint import PrettyPrinter
import sys
from typing import Callable

from quart import Quart, request

from src import CONFIG

BASE_URI = f"https://auroraphq.cafebonappetit.com/cafe/{CONFIG['cafe_name']}"

logging.basicConfig(stream=sys.stdout, format='%(name)s - %(levelname)s - %(message)s')
pp = PrettyPrinter(indent=4)

app = Quart(__name__)


@app.route("/mention", methods=["POST"])
def mentioned():
    print(request.json)
    text = request.json['data']['text']
    result = route(text)
    logging.info(result)


def route(text: str) -> Callable:
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
    }
    dict_match = reduce(lambda x, y: y if y in routing_dict else x, reversed(text.split(" ")), "")
    if dict_match:
        return routing_dict[dict_match]


def main():
    pass
    # try:
    #     start_slack()
    # except KeyboardInterrupt:
    #     sys.exit()
    # except Exception as e:
    #     logging.warning(f'exception!!! {e}')
    #     sleep(10)
    #     main()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
