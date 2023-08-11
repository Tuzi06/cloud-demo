import json
import time
from urllib.parse import urlencode
from lowlevel.main import prepare_driver
from lowlevel.ins import findPicture
import requests,pickle


# cookies = pickle.load(open('lowlevel/ins_cookies.pkl','rb'))
# driver = prepare_driver(cookies,1,False)[0]
# driver.get('https://www.instagram.com/p/Cvt1PgPtUMj/')
# time.sleep(5)
# pictures = findPicture(driver,0)
# driver.quit()
from bs4 import BeautifulSoup as bs
html = open('res.html','r').read()
response = requests.post('http://192.168.1.67:5000/dataJob',data = {'html':html,'user':{'id':'asdf'},'pics':[]},files = {'file':html})
# driver.quit()