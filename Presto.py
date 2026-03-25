from PrimirestAPI import Primirest, MenuDay
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

if not os.path.exists(".env"):
    env_username = input("E-mail: ").strip()
    env_password = getpass("Heslo: ")
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"PRESTO_USERNAME={env_username}\n")
        f.write(f"PRESTO_PASSWORD={env_password}\n")
    print("Přihlašovací údaje byly uloženy.\n")

load_dotenv()

username = os.getenv("PRESTO_USERNAME")
password = os.getenv("PRESTO_PASSWORD")

primirest = Primirest(username=username, password=password)

print("Přihlášen jako: " + primirest.boarder.name)

# print(primirest.boarder.account)
print(primirest.unit.purchase_places[0].menus[1].menu_days[0].items)


# consumptions = get_main_courses(primirest.get_boarder_consumptions(date(2020, 1, 1), date(2030, 1, 1)))

primirest.logout()