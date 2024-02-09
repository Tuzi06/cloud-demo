from server import Scraper
from queue import Queue
from bs4 import BeautifulSoup as bs
s = Scraper(1,1)
# s.headers['headers']

q = Queue()
p = Queue()
q.put('https://www.xiaohongshu.com/user/profile/5f8f21aa0000000001002ad6')
p.put({'userInfo':{'user-id':'adfasd'},'links':['/explore/611206df0000000021037225']})

s.homePageScraper(q)