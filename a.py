import json,requests,random,time,copy,string
from multiprocessing import Process,Manager
from bs4 import BeautifulSoup as bs

def p(headers,cookies,count):
    
    url ="https://edith.xiaohongshu.com/api/sns/web/v2/comment/sub/page?note_id=65f560c40000000012035930&root_comment_id=65fb002c000000000b018c3e&num=10&cursor=65fb01a5000000000b0208d6&image_formats=jpg,webp,avif" 
    # url = "https://www.xiaohongshu.com/explore"
    header = copy.deepcopy(headers['htmlHeaders'])
    while count.value<10000000:
        cookie = headers['cookie']
        newCookie = cookie.split('; ')
        newCookie[2] = 'webId='+''.join([random.choice(string.ascii_lowercase + string.digits)for i in range(32)])
        newCookie= '; '.join(newCookie)
        header['cookie'] = newCookie
        try:
            res = requests.get(url,headers=header).json()
            # res = requests.get(url,headers=header)
            # _ = res['data']['comments']
            # soup = bs(res.content,'html.parser')
            # linklist =soup.findAll('a','title')
            # if len(linklist) == 0:
            #     raise Exception('Saaa')
            if res['data']['comments'] == []:
                raise Exception('as')
            print('\r',count.value, end='\r')
            # print(res['data'])
        except:
            print('crashed in round ',count.value)
            if res == None:
                continue
            if 'data' in res and 'comments' in res['data']:
                print(res['data']['comments'])
            else:
                print(res)
      
        count.value += 1


headers = json.load(open('headers.json','r'))
cookies = Manager().list(json.load(open('cookies.json','r')))
count = Manager().Value(int,0)

ps = []
for _ in range(30):
    ps.append(Process(target=p,args=[headers,cookies,count]))
    ps[-1].start()
    time.sleep(1)
for p in ps:
    p.join()