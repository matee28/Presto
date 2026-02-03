from PrimirestAPI import Primirest, MenuDay
from getpass import getpass
import re

def get_main_courses(consumptions):
    ret = []
    for consumption in consumptions:
        ret.append(re.split(r',\s*(?=[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ])', consumption)[-1].strip())
    return ret

def get_soup(menu_day: MenuDay):
    if len(menu_day.items) > 0:
        return re.split(r',\s*(?=[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ])', menu_day.items[0].description)[-1].strip()
    return ""


username = input("E-mail: ").strip()
password = getpass("Heslo: ")

primirest = Primirest(username=username, password=password)

print("Přihlášen jako: " + primirest.boarder.name)

primirest.logout()