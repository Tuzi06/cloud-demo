from lowlevel.main import prepare_driver,Producer
from selenium.webdriver.common.by import By
import pickle,queue,json,time,requests,random

driver = prepare_driver(pickle.load(open('lowlevel/ins_cookies.pkl','rb')),1,False)[0]
finder = prepare_driver(pickle.load(open('lowlevel/ins_cookies.pkl','rb')),1,False)[0]

username = 'user-spal93ysiq-sessionduration-5'
password ='eIg4qQxqoA4bG74yun'
proxy = f"https://{username}:{password}@us.smartproxy.com:10001"

workq = queue.Queue()
posts = []

keywords = json.load(open('keywords.json','r'))
random.shuffle(keywords)
for keyword in keywords:
    driver.get(f"https://www.instagram.com/explore/search/keyword/?q={keyword}")
    time.sleep(5)
    while len(posts) < (1000 // len(keywords)):
        Producer(driver,workq)
        while not workq.empty():
                try:
                    link =workq.get()['link']
                    # response = requests.get(f"{link}?__a=1&__d=dis",proxies={'http':proxy,'https':proxy})
                
                    # username = (json.loads(response.text))['graphql']['shortcode_media']['owner']['username']
                    finder.get(link)
                    time.sleep(2)
                    container = finder.find_element(By.CLASS_NAME,'_aaqt')
                    url = container.find_element(By.TAG_NAME,'a')
                    username = url.text
                    userres = requests.get(f"{url.get_attribute('href')}?__a=1&__d=dis",proxies={'http':proxy,'https':proxy})

                    # userres = requests.get(f"https://www.instagram.com/{username}/?__a=1&__d=dis",proxies={'http':proxy,'https':proxy})
                    
                    print(f"https://www.instagram.com/{username}/?__a=1&__d=dis")

                    if userres.status_code != 200:
                        continue
                    userres = json.loads(userres.text)
                    if int(userres['graphql']['user']['edge_followed_by']['count'])<10000:
                        continue
                   
                    shortcode = [node['node']['shortcode'] for node in userres['graphql']['user']['edge_owner_to_timeline_media']['edges']]
                    for code in shortcode:
                        try:
                            post = dict()
                            post['user-id'] = userres['graphql']['user']['id'],
                            post['username'] = username,
                            post['user-info'] = userres['graphql']['user']['biography'],
                            post['user-link'] =  f"https://www.instagram.com/{username}/"
                            continue
                            res = requests.get(f"https://www.instagram.com/p/{code}/?__a=1&__d=dis",proxies={'http':proxy,'https':proxy})
                            if res.status_code != 200:
                                print(res.status_code)
                                continue
                            res = json.loads(res.text)
                            post['text'] =res['graphql']['shortcode_media']['edge_media_to_caption']['edges'][0]['node']['text']
                            commentContainer = res['graphql']['shortcode_media']['edge_media_to_parent_comment']['edges']
                            comments = []
                            for comment in commentContainer[0:5]:
                               
                                comments.append({
                                    comment['node']['owner']['username']: comment['node']['text'],
                                    'replys':[{reply['node']['owner']['username'] : reply['node']['text']} for reply in comment['node']['edge_threaded_comments']['edges'][0:5]]
                                })
                            post['comments'] = comments
                            pics = []
                            picContainer = res['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
                            for pic in picContainer:
                                pics.append(pic['node'][ "display_resources"][1]['src'])
                            post['pictures'] = pics
                            posts.append(post)
                        except:
                            continue
                except:
                    continue
                        
        print(len(posts))
driver.quit()
open('test_text.json','w').write(json.dumps(posts,ensure_ascii=False,indent=4))