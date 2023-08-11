from flask import Flask,request,jsonify
import os,logging,time,pickle,queue,requests,json
from flask.scaffold import F 
from multiprocessing import Process,Pipe
from lowlevel.ins import findPicture,run

class Scraper:
    def __init__(self) -> None:
        self.userState = 'idle'
        self.dataState = 'idle'
        self.parent, self.child = Pipe() # pipe for passing users name to getShortCode and update UserState
        self.codeParent,self.codeChild = Pipe() # pipe for return the shorCode list
        self.postParent,self.postChild = Pipe() # pipe for passing html to getData and update dataState
        self.resParent,self.resChild = Pipe()
        self.stop = False

    def getShortCode(self, pipe):
        self.child = pipe
        while not self.stop:
            job = self.child.recv()
            if job != None:
                self.child.send('busy')
                userlink,_ = job.values()
                print(userlink)
                username = 'user-tuzi06-sessionduration-5'
                password = 'i2Zgeyyk5SwTCu28im'
                proxy = f"http://{username}:{password}@ca.smartproxy.com:20001"
                response = requests.get(f"{userlink}?__a=1&__d=dis",proxies={'http':proxy,'https':proxy})
                
                print(response.status_code)
                if response.status_code == 200:  
                    userres = json.loads(response.text)
                    user= dict()
                    user['user-id'] = userres['graphql']['user']['id'],
                    user['username'] = username,
                    user['user-info'] = userres['graphql']['user']['biography'],
                    user['user-link'] =  f"https://www.instagram.com/{username}/"
                    shortCodes = [node['node']['shortcode'] for node in userres['graphql']['user']['edge_felix_video_timeline']['edges']]  
                    self.codeParent.send({'userinfo':user,'shortCodes':shortCodes})
                    self.child.send('idle')
          

    def getData(self,postpipe,respipe):
        self.postChild = postpipe
        self. resChild= respipe
        while not self.stop:
            job = self.postChild.recv()
            if job != None:
                # print(job)
                self.postChild.send('busy')
                # data = job
                # html,user,pics = job.get('html','user','pics')
                print(job.get('user'))
                post = run(job['html'],job['user'],job['pics'])
                print(post.keys())
                self.postChild.send('idle')
                self.resChild.send(json.dumps(post,ensure_ascii=False))

app = Flask(__name__)

@app.route('/start')
def start_child_process(): #Gunicorn does not allow the creation of new processes before the app creation, so we need to define this route
    global scraper
    scraper = Scraper()
    Process(target = scraper.getShortCode, args = [scraper.child]).start()
    Process(target = scraper.getData, args = [scraper.postChild,scraper.resChild]).start()
    return "Scraper running"

@app.route('/stop')
def stop():
    scraper.stop = True
    return 'stopped'

@app.route('/userJob')
def process_userjob():
    print(request.args)
    scraper.parent.send(request.args)
    while True:
        shortCodes = scraper.codeChild.recv()
        if shortCodes != None:
            break
    print(shortCodes)
    if shortCodes:
        return shortCodes

@app.route('/dataJob',methods=['POST'])
def process_dataJob():
    scraper.postParent.send(request.get_json())
    while True:
        post= scraper.resParent.recv()
        if post != None:
            break
        time.sleep(3)
    return post
 

@app.route('/reset')
def reset_post():
    scraper.posts = []

@app.route('/state')
def current_state():
    try:
        process,_ = request.args.values()
        if process == "user":
                if scraper.parent.poll(timeout=3): #checks if there are new messages from the child process
                    scraper.userState = scraper.parent.recv() # updates the state in such case
                return scraper.userState
        elif process == 'data':
            if scraper.postParent.poll(timeout=3): #checks if there are new messages from the child process
                scraper.dataState = scraper.postParent.recv() # updates the state in such case
            return scraper.dataState
    except:
        return "not-started"
 

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)



# curl -x 'http://user-tuzi06-sessionduration-1:i2Zgeyyk5SwTCu28im@ca.smartproxy.com:20001' 'https://ip.smartproxy.com/json'