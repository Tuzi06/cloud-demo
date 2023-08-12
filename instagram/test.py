
import traceback
from selenium.webdriver.common.by import By
import pickle,time
from requests import session
from bs4 import BeautifulSoup

from lowlevel.main import prepare_driver,Producer
from fake_useragent import UserAgent
from fake_headers import Headers

cookies = pickle.load(open('lowlevel/ins_cookies.pkl','rb'))
# # # print(len(cookies))
# producer = prepare_driver(cookies,1,False)[0]
finder = prepare_driver(cookies,1,False)[0]

finder.get('https://www.instagram.com/p/CuhaYfNNJgl/')
time.sleep(5)
buttons = finder.find_elements(By.CLASS_NAME,'x1i10hfl')
for button in buttons:
    try: 
        if button.get_attribute('role') == 'button' and button.get_attribute('tabindex') == '0' and 'View all'in button.text:
            button.click()
    except:
        print(traceback.print_exc())
        continue
input('pause')
