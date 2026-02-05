from datetime import datetime, date
import requests
from bs4 import BeautifulSoup
import time, json
from urllib.parse import urlparse
from dataclasses import dataclass, field
from typing import Optional, Dict, List
import re


@dataclass
class Unit:
    """
    Reprezentuje závod (unit). 
    """
    id: int
    name: str
    purchase_places: List['PurchasePlace'] = field(default_factory=list)

@dataclass
class PurchasePlace:
    """
    Reprezentuje výdejní místo (purchase place) uvnitř závodu.
    """
    id: int
    name: str
    menus: List['Menu'] = field(default_factory=list)

@dataclass
class Menu:
    """
    Reprezentuje jídelní lístek (z pravidla pro určitý týden).
    """
    id: int
    name: str
    purchase_place : 'PurchasePlace' = field(repr=False, default=None)
    menu_days: List['MenuDay'] = field(default_factory=list)

@dataclass
class MenuDay:
    """
    Reprezentuje den v menu.
    """
    id: int
    date: date
    menu : 'Menu' = field(repr=False, default=None)
    items: List['MenuItem'] = field(default_factory=list)

@dataclass
class MenuItem:
    """
    Reprezentuje položku.
    """
    id: int
    description: str
    price: float
    can_order: bool
    order: 'ItemOrder' = field(default=None)
    menu_day : 'MenuDay' = field(repr=False, default=None)

@dataclass
class ItemOrder:
    """
    Reprezentuje objednávku položky.
    """
    can_cancel: bool
    can_update: bool
    menu_item: 'MenuItem' = field(repr=False, default=None)

@dataclass
class Boarder:
    """
    Reprezentuje uživatele.
    """
    id: int
    name: str
    info: str
    account: 'Account' = field(repr=False, default=None)

@dataclass
class Account:
    """
    Reprezentuje uživatelovo konto.
    """
    balance: float
    orders: float
    balance_real: float
    boarder: 'Boarder' = field(repr=False, default=None)



class Primirest:

    def __ts(self):
        return int(time.time() * 1000)

    def __init__(self, username: str, password: str):

        self.session = requests.Session()
        
        # Chrome
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://mujprimirest.cz/"
        })

        self.__auth(username, password)

        self.__get_purchase_places()
        self.__get_menus()

        for purchase_place in self.unit.purchase_places:
            for menu in purchase_place.menus:
                self.__get_menu_days_and_items(menu)

    def __auth(self, username: str, password: str):
        response = self.session.post(
            "https://mujprimirest.cz/ajax/CS/auth/login",
            data={
                "UserName": username,
                "Password": password,
                "RememberMe": "true",
            }
        )
        if response.ok:
            soup = BeautifulSoup(response.text, "html.parser")
            if len(soup.select("body > div.horni-panel > div.horni > div.vitejte-v > div.welcome")) > 0: # prvek pro kontrolu prihlaseni

                boarder_info = self.__get_boarder_info()
                self.boarder = Boarder(id=boarder_info["id"], name=boarder_info["name"], info=boarder_info["additional_info"])

                self.boarder.account = Account(balance=0, orders=0, balance_real=0, boarder=self.boarder)
                self.__update_boarder_balance()

                unit_name = soup.select_one("body > div.horni-panel > div.horni > div.vitejte-v > div.zavod.visible-sm.visible-md.visible-lg.visible-xl").text.strip()
                unit_id = int(urlparse(soup.select_one("body > div.levy-panel > div.info > div.typuctu > span:nth-child(4) > a")["href"]).path.rstrip("/").split("/")[-1])
                self.unit = Unit(id=unit_id, name=unit_name)

            else:
                raise Exception("Přihlášení se nezdařilo. Zkontrolujte uživatelské jméno a heslo.")
        else:
            raise Exception("Chyba při přihlašování. HTTP status code: " + str(response.status_code))
        
    def __get_boarder_info(self):
        req = self.session.get(f"https://mujprimirest.cz/cs/context/available?q=&_={self.__ts()}")
        if req.ok:
            user_data = json.loads(req.text)["Items"][0]
            return {"id": user_data["ID"], "name": user_data["Name"], "additional_info": user_data["AdditionalInfo"]}
        else:
            raise Exception("Chyba při získávání informací o uživateli. HTTP status code: " + str(req.status_code))
        
    def __update_boarder_balance(self):
        req = self.session.get("https://mujprimirest.cz/CS/boarding")
        if req.ok:
            soup = BeautifulSoup(req.text, "html.parser")
            user_balance = float(soup.select_one("body > div.levy-panel > div.info > div.typuctu > a:nth-child(2)").text.strip())
            user_sum_of_orders = float(soup.select_one("body > div.levy-panel > div.info > div.typuctu > span:nth-child(4) > a").text.strip())
            user_balance_real = float(soup.select_one("body > div.levy-panel > div.info > div.typuctu > span:nth-child(6) > strong").text.strip())
            self.boarder.account.balance = user_balance
            self.boarder.account.orders = user_sum_of_orders
            self.boarder.account.balance_real = user_balance_real
        else:
            raise Exception("Chyba při získávání zůstatku uživatele. HTTP status code: " + str(req.status_code))
        
    def __get_purchase_places(self):
        req = self.session.get("https://mujprimirest.cz/CS/boarding")
        if req.ok:
            soup = BeautifulSoup(req.text, "html.parser")

            for purchase_place_option in soup.select("body > div.warp > div > div.panel.panel-default.panel-filter > div > div.pp-select.panel-control.responsive-control option"):
                self.unit.purchase_places.append(PurchasePlace(name=purchase_place_option.text, id=int(purchase_place_option.get("value"))))

    def __get_menus(self):
        for purchase_place in self.unit.purchase_places:
            url = f"https://mujprimirest.cz/CS/boarding/index?purchasePlaceID={purchase_place.id}"
            req = self.session.get(url)
            if req.ok:
                soup = BeautifulSoup(req.text, "html.parser")
                for menu_option in soup.select("body > div.warp > div > div.panel.panel-default.panel-filter > div > div.menu-select.panel-control.responsive-control option"):
                    menu_name = menu_option.text.strip()
                    menu_id = int(menu_option.get("value"))
                    purchase_place.menus.append(Menu(name=menu_name, id=menu_id, purchase_place=purchase_place))

    def __get_menu_days_and_items(self, menu: Menu):
        url = f"https://mujprimirest.cz/ajax/CS/boarding/{self.unit.id}/index?purchasePlaceID={menu.purchase_place.id}&menuID={menu.id}&menuViewType=SIMPLE&_={self.__ts()}"
        req = self.session.get(url)
        if req.ok:
            menu_data = json.loads(req.text)["Menu"]
            menu_orders = {}
            for order in menu_data["Orders"]:
                menu_orders[int(order["IDMenuDay"])] = {
                    "can_cancel": bool(order["CanCancel"]),
                    "can_update": bool(order["CanUpdate"]),
                    "item_ids": [int(item["IDItem"]) for item in order["Items"]]
                    }
            
            for menu_day_data in menu_data["Days"]:
                if len(menu_day_data["Items"]) > 0:
                    id_menu_day = int(menu_day_data["Items"][0]["IDMenuDay"])
                    menu_day_date = datetime.fromtimestamp(int(re.search(r'\d+', menu_day_data["Items"][0]["MenuDayDate"]).group()) / 1000).date()
                    menu_day = MenuDay(id=id_menu_day, date=menu_day_date, menu=menu)

                    for item in menu_day_data["Items"]:
                        item_id = int(item["Flags"][0]["IDEntity"])
                        item_description = item["Description"]
                        item_price = float(item["BoarderTotalPriceVat"])
                        item_can_order = bool(item["CanOrder"])
                        menu_item = MenuItem(id=item_id, description=item_description, price=item_price, can_order=item_can_order, menu_day=menu_day)

                        if id_menu_day in menu_orders:
                            if item_id in menu_orders[id_menu_day]["item_ids"]:
                                menu_item.order = ItemOrder(can_cancel=menu_orders[id_menu_day]["can_cancel"], can_update=menu_orders[id_menu_day]["can_update"], menu_item=menu_item)

                        menu_day.items.append(menu_item)
                    
                    menu.menu_days.append(menu_day)

    def __update_menu_days_and_items(self, menu: Menu):
        menu.menu_days.clear()
        self.__get_menu_days_and_items(menu)
                    
    def get_boarder_consumptions(self, start: date, end: date):
        url = f"https://mujprimirest.cz/ajax/cs/consumptions/{self.boarder.id}/index?id={self.boarder.id}&from={start.strftime('%d.%m.%Y')}&to={end.strftime('%d.%m.%Y')}&_={self.__ts()}"
        req = self.session.get(url)
        consumptions = []
        if req.ok:
            for consumption in json.loads(req.text)["Rows"]:
                if consumption["Order"] != 0: # pokud jde o nakup, ma order id 0; vydej objednaneho jidla ma vzdy specificke order id
                    consumptions.append(consumption["Description"])
        return consumptions
    
    def order(self, item: MenuItem):
        url = f"https://mujprimirest.cz/ajax/CS/boarding/0/order?menuID={item.menu_day.menu.id}&dayID={item.menu_day.id}&itemID={item.id}&purchasePlaceID={item.menu_day.menu.purchase_place.id}&_={self.__ts()}"
        req = self.session.get(url)

        if req.ok:
            self.__update_boarder_balance()
            self.__update_menu_days_and_items(item.menu_day.menu)
            result = json.loads(req.text)
            return {"success": result["Success"], "message": result["Message"]}
        else:
            raise Exception("Chyba při objednávání. HTTP status code: " + str(req.status_code))
        
    def find_order_id(self, menu_day: MenuDay):
        url = f"https://mujprimirest.cz/ajax/CS/boarding/{self.unit.id}/index?purchasePlaceID={menu_day.menu.purchase_place.id}&menuID={menu_day.menu.id}&menuViewType=SIMPLE&_={self.__ts()}"
        req = self.session.get(url)
        if req.ok:
            for order in json.loads(req.text)["Menu"]["Orders"]:
                if int(order["IDMenuDay"]) == menu_day.id:
                    return order["ID"]
            return None
        else:
            raise Exception("Chyba při hledání objednávky. HTTP status code: " + str(req.status_code))
        
    def cancel_order(self, menu_day: MenuDay):
        order_id = self.find_order_id(menu_day)
        if order_id is None:
            return {"success": False, "message": "Pro daný den neexistuje žádná objednávka"}
        else:
            url = f"https://mujprimirest.cz/ajax/CS/boarding/0/cancelOrder?orderID={order_id}&menuID={menu_day.menu.id}&purchasePlaceID={menu_day.menu.purchase_place.id}&_={self.__ts()}"
            req = self.session.get(url)

            if req.ok:
                self.__update_boarder_balance()
                self.__update_menu_days_and_items(menu_day.menu)
                result = json.loads(req.text)
                return {"success": result["Success"], "message": result["Message"]}
            else:
                raise Exception("Chyba při rušení objednávky. HTTP status code: " + str(req.status_code))

    def logout(self):
        self.session.get("https://mujprimirest.cz/ajax/CS/auth/logout")
        self.session.close()
        self.boarder = None
        self.unit = None