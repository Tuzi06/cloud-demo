import pickle,json
from lowlevel.xhs2 import prepare_driver,getUser,grabing,wait_for_page
from bs4 import BeautifulSoup as bs
import time
driver = prepare_driver([],1)[0]
scraper = prepare_driver([],1,False)[0]
time.sleep(5)
driver.get('https://www.xiaohongshu.com/user/profile/5a6d37f911be100505ad38d2')
time.sleep(2)
soup = bs(driver.page_source,'html.parser')
user = getUser(soup)
links = ["https://www.xiaohongshu.com"+a['href'] for a in soup.findAll('a','cover ld mask')]
posts = []
idx = 0
for link in links[:5]:
    print(link)
    scraper.get(link)
    wait_for_page(scraper,'comment-item')
    soup1 = bs(scraper.page_source,'html.parser')
    idx,post= grabing(soup1,user,idx)
    posts.append(post)
driver.quit()
scraper.quit()
print(json.dumps(posts,ensure_ascii=False,indent=4))