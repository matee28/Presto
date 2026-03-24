from PrimirestAPI import Primirest, MenuDay
from FoodRecommend import FoodRecommend
from getpass import getpass
import re
from datetime import date
from dotenv import load_dotenv
import os

def get_main_courses(consumptions):
    ret = []
    for consumption in consumptions:
        ret.append(re.split(r',\s*(?=[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ])', consumption)[-1].strip())
    return ret

def get_soup(menu_day: MenuDay):
    if len(menu_day.items) > 0:
        return re.split(r',\s*(?=[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ])', menu_day.items[0].description)[-1].strip()
    return ""

load_dotenv()

username = os.getenv("PRESTO_USERNAME") # input("E-mail: ").strip()
password = os.getenv("PRESTO_PASSWORD") # getpass("Heslo: ")

primirest = Primirest(username=username, password=password)

print("Přihlášen jako: " + primirest.boarder.name)

# print(primirest.boarder.account)
# print(primirest.unit.purchase_places[0].menus[2].menu_days[0].items)
# print(primirest.boarder.account)
# print(primirest.cancel_order(primirest.unit.purchase_places[0].menus[2].menu_days[0]))
# print(primirest.unit.purchase_places[0].menus[2].menu_days[0].items)
# print(primirest.boarder.account)
# print(primirest.order(primirest.unit.purchase_places[0].menus[2].menu_days[0].items[0]))
# print(primirest.unit.purchase_places[0].menus[2].menu_days[0].items)
# print(primirest.boarder.account)


food_recommend = FoodRecommend(debug=True)

consumptions = get_main_courses(primirest.get_boarder_consumptions(date(2020, 1, 1), date(2030, 1, 1)))

for i in range(5):
    menu = get_main_courses([item.description for item in primirest.unit.purchase_places[0].menus[0].menu_days[i].items])
    recommended = food_recommend.recommend(consumptions, menu)
    print(f"Na základě {len(consumptions)} jídel vybráno: {recommended}")

primirest.logout()