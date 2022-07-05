import json
import aiohttp


class Cafe:
    def __init__(self, company: str, cafe_name: str):
        self.base_url = f"https://{company}.cafebonappetit.com/cafe/{cafe_name}"
        self.cafe_name = cafe_name
        self.req = None

    async def initialize_session(self):
        self.req = aiohttp.ClientSession()

    @staticmethod
    async def convert_cor_icons(item: dict):
        cor_icons = {
            "1": "[V]",
            "3": "[SW]",
            "4": "[Ve]",
            "6": "[FF]",
            "9": "[GF]"
        }
        return "".join(cor_icons.get(i, "") for i in item["cor_icon"])

    async def items_to_text(self, items: dict) -> str:
        return "\n".join([
            "  • "
            f"*{val['label'].title()}* {await self.convert_cor_icons(val)}: "
            f"{val['description'].capitalize()}." for val in items.values()
        ])

    async def get_menu_items(self, date_: str) -> dict:
        """
        :param date_: str YYYY-MM-DD
        """
        async with self.req.get(f"{self.base_url}/{date_}") as r:
            lines = (await r.text()).splitlines()
            for line in lines:
                if "Bamco.menu_items" in line:
                    return json.loads(line.split("= ")[1][:-1])
            raise LookupError

    async def menu_items(self, date_) -> str:
        """
        Get menu items as string for specified date.
        :param date_: str YYYY-MM-DD
        """
        return await self.items_to_text(await self.get_menu_items(date_))
