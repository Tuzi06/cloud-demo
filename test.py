import json
import time
from urllib.parse import urlencode
from lowlevel.main import prepare_driver
from lowlevel.ins import findPicture
import requests,pickle
from flask import jsonify

cookies = pickle.load(open('lowlevel/ins_cookies.pkl','rb'))
driver = prepare_driver(cookies,1)
driver.get('https://www.instagram.com/p/Cvt1PgPtUMj/')
time.sleep(5)
pictures = findPicture(driver,0)
response = requests.get('http://192.168.1.67:5000/dataJob?'+urlencode({'html':jsonify(driver.page_source),'user':{'id':'asdf'},'pics':pictures}))