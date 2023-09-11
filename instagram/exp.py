import pickle
import time

import keyboard
from lowlevel.main import prepare_driver,init
from selenium.webdriver.common.by import By

browser1 = prepare_driver(pickle.load(open('lowlevel/ins_cookies_linux.pkl','rb')),1,False)[0]
browser2 = prepare_driver(pickle.load(open('lowlevel/ins_cookies_linux.pkl','rb')),1,False)[0]

browser1.get('https://www.instagram.com/explore/search/keyword/?q=tech')
i =0 
while True:
    time.sleep(1)
    containers = browser1.find_element(By.CLASS_NAME,'x1gryazu')
    containers = containers.find_element(By.TAG_NAME,'section')
    containers = containers.find_elements(By.TAG_NAME,'a')
    links = [link.get_attribute('href') for link in containers]
    links = [link for link in links if 'https://www.instagram.com/p/' in link ]
    for link in links:
        browser2.get(link)
        time.sleep(4)
        # browser2.delete_all_cookies()
        percent = ("{0:." + str(2) + "f}").format(100 * (i/ float(50000)))
        print(f'\r{percent}% Complete', end = '\r')
        i+=1
    
    browser1.execute_script("arguments[0].scrollIntoView();",containers[-1])