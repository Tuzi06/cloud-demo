import lowlevel.xhs2 as xhs  
from selenium import webdriver
from selenium. webdriver.common.by import By
from threading import Thread
from queue import Queue
import sys,pickle,time,datetime,json
from selenium.webdriver.chrome.service import Service

url = 'https://www.xiaohongshu.com/explore'

def init():
    soption = webdriver.ChromeOptions()
    soption.add_argument('disable-blink-features=AutomationControlled')
    service = Service(executable_path= '/usr/bin/chromedriver.exe')
    driver = webdriver.Chrome(options = soption,service=service)
    driver.get(url)
    input('pause for login ... press enter when finished')
    cookies = driver.get_cookies()
    driver.quit()
    return cookies

def prepare_driver(cookies,workers,headless = True):
    drivers = []
    options = webdriver.ChromeOptions()
    options.add_argument('disable-blink-features=AutomationControlled')
    service = Service(executable_path= '/usr/bin/chromedriver.exe')

    if headless:
        options.add_argument('headless')
    
    for _ in range(workers):
        driver = webdriver.Chrome(options = options,service=service)
        driver.get(url)
        time.sleep(1)
        driver.get(url)
        for cookie in cookies: 
            if isinstance(cookie.get('expiry'), float):
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)
        driver.refresh()
        drivers.append(driver)
    return drivers

def Finder(driver,userlink):
    try:
        driver.get(userlink)
        if ' https://www.xiaohongshu.com/website-login/error?redirectPath=' in str(driver.current_url):
            driver.get(userlink)
        xhs.wait_for_page(driver,'user-interactions')
        user = xhs.getUser(driver)
        user['userLink'] = userlink
        if 'W' in user['follow'] or '万' in user['follow']:
            return {'info':user,'post':xhs.getLinks(driver)}
    except:
        return 

def Worker(driver,postInfo,posts):
    try:
        xhs.run(driver,postInfo['post'],posts,postInfo['info'])
    except:
        return 