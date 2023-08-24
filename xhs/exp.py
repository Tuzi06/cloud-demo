url = 'https://www.xiaohongshu.com/explore/64aaf8b8000000001c00f0dc'

import asyncio
from re import A
import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEnginePage
from bs4 import BeautifulSoup as bs

# class client (QWidget):
#     def __init__(self,url):
#         super().__init__()
#         layout = QVBoxLayout()
#         self.view = QWebEngineView()
#         layout.addWidget(self.view)
#         self.view.setUrl(QUrl(url))

#         self.setLayout(layout)
#         self.show()

# class client(QWebEnginePage):
#     def __init__(self,url):
#         self.html = ''
#         self.app = QApplication(sys.argv)
#         QWebEnginePage.__init__(self)
#         self.loadFinished.connect(self.dosomething)
#         self.load(QUrl(url))
#         self.app.exec()
       
#     def dosomething(self):
#         print('ifnish')
#         time.sleep(20)
#         self.app.quit()

#     def gethtml(self,html):
#         self.html = html

# app = QApplication(sys.argv)
# webclient = client('https://www.xiaohongshu.com/explore/64d4055f000000001201b80f')

# source = webclient.html
# # print(source)

from requests_html import HTMLSession

session = HTMLSession()

r = session.get(url)
time.sleep(10)
r.html.render(sleep = 10,keep_page = True)
soup = bs(r.html.html,'lxml')
open('a.html','w').write(r.html.html)


