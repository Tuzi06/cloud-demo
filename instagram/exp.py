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

finder.get('https://www.instagram.com/p/Cp3XtortlhY/')
input('pause')
soup = BeautifulSoup(finder.page_source,'html.parser')
open('res.html','w').write(soup.prettify())