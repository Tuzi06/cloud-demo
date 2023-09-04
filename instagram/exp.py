import pickle
import time
from lowlevel.main import prepare_driver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs

browser = prepare_driver(pickle.load(open('lowlevel/ins_cookies.pkl','rb')),1,False)[0]
browser.get('https://www.instagram.com/explore/search/keyword/?q=tech')
browser1 = prepare_driver(pickle.load(open('lowlevel/ins_cookies.pkl','rb')),1,False)[0]
time.sleep(2)
while True:
    containers = browser.find_element(By.CLASS_NAME,'x1gryazu')
    containers = containers.find_element(By.TAG_NAME,'section')
    containers = containers.find_elements(By.TAG_NAME,'a')
    links = [link.get_attribute('href') for link in containers]
    links = [link for link in links if 'https://www.instagram.com/p/' in link ]

    for link in links:
        browser1.get(link)
        time.sleep(2)
        soup = bs(browser1.page_source,'html.parser')
        if not soup.find('span',class_='x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs xt0psk2 x1i0vuye xvs91rp xo1l8bm x5n08af x10wh9bi x1wdrske x8viiok x18hxmgj'):
            input('pauser')
            browser1.delete_all_cookies()
            browser1.get('https://www.instagram.com')
            input('fasdf')
    
    browser.execute_script("arguments[0].scrollIntoView();",containers[-1])
    time.sleep(2)