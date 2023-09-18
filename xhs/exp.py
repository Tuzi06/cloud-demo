import pickle
import time
from selenium.webdriver import Chrome,ChromeOptions
from bs4 import BeautifulSoup as bs
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

service = Service(executable_path='lowlevel/chromedriver-mac-arm64/chromedriver')
cookies = pickle.load(open('lowlevel/cookies_linux.pkl','rb'))
options = ChromeOptions()
options.add_argument('disable-blink-features=AutomationControlled')
options.add_arguments('headless')

browser1 = Chrome(service=service,options=options)
browser1.get('https://www.xiaohongshu.com/explore')
for cookie in cookies: 
    if isinstance(cookie.get('expiry'),float):
        cookie['expiry'] = int(cookie['expiry'])
    browser1.add_cookie(cookie)

browser2 = Chrome(service=service,options=options)

total = 0
sucess = 0
# input('pause')
# pickle.dump(browser1.get_cookies(),open('lowlevel/xhs_cookies.pkl','wb'))
browser1.get('https://www.xiaohongshu.com/explore?channel_id=homefeed_recommend')
time.sleep(5)
while total<1000:
    wrappers = browser1.find_elements(By.CLASS_NAME,'author-wrapper')
    userlinks = [wrapper.find_element(By.TAG_NAME,'a').get_attribute('href') for wrapper in wrappers]
    browser1.execute_script("arguments[0].scrollIntoView();",wrappers[-1])
    for user in userlinks:
        browser2.get(user)
        time.sleep(2)
        total +=1
        soup = bs(browser2.page_source,'html.parser')
        follow = soup.findAll('span',class_='count')[1].text

        if 'W' in follow or '万' in follow:
            sucess+=1
        p1 =percent = ("{0:." + str(3) + "f}").format(100 * (sucess/total))
        print(f"{p1}% of user has follow greater than 10000, and {total} users checked",end="\r")
browser1.quit()
browser2.quit()