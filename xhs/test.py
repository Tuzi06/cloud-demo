import json
import time
from selenium.webdriver import Chrome,ChromeOptions
from selenium.webdriver.chrome.service import Service
service = Service(executable_path='lowlevel/chromedriver-mac-arm64/chromedriver')
options = ChromeOptions()
options.add_argument('disable-blink-features=AutomationControlled')
options.add_argument("--disable-dev-shm-usage")

browser = Chrome(service=service,options=options)

users = json.load(open('1k_follow&10k_like.json','r'))
for user in users[:100]:
    browser.get(user)
    time.sleep(3)
browser.quit()