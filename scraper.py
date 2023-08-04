from flask import Flask,request,jsonify
import os,logging,time,pickle,queue,requests,json 
from multiprocessing import Process,Pipe
from lowlevel import main

class Scraper:
    def __init__(self) -> None:
        self.state = 'idle'
        self.parent, self.child = Pipe()
        self.send,self.recieve = Pipe()
    def run(self, pipe):
        self.child = pipe
        while True:
            job = self.child.recv()
            if job != None:
                self.child.send('busy')
                link,_ = job.values()
                response = requests.get(f"{link}?__a=1&__d=dis")
                print(response.status_code)
                if response.status_code == 200:  
                    shortCodes = [node['node']['shortcode'] for node in (json.loads(response.text))['graphql']['user']['edge_felix_video_timeline']['edges']]
                    print(shortCodes)   
                    self.send.send(shortCodes)
                    print('done')
                    self.child.send('idle')
                   
                else:
                    self.child.send('scraping-detected')


app = Flask(__name__)

@app.route('/start')
def start_child_process(): #Gunicorn does not allow the creation of new processes before the app creation, so we need to define this route
    global scraper
    scraper = Scraper()
    Process(target = scraper.run, args = [scraper.child]).start()
    return "Scraper running"

@app.route('/job')
def process_job():
    print(request.args)
    scraper.parent.send(request.args)
    while True:
        shortCodes = scraper.recieve.recv()
        if shortCodes != None:
            break
    print(shortCodes)
    if shortCodes:
        return jsonify(result = shortCodes)
    
@app.route('/download')
def store_posts():
    
    return jsonify(result = scraper.posts)

@app.route('/reset')
def reset_post():
    scraper.posts = []

@app.route('/state')
def current_state():
    try:
        if scraper.parent.poll(timeout=3): #checks if there are new messages from the child process
            scraper.state = scraper.parent.recv() # updates the state in such case
        return scraper.state
    except:
        return "not-started"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)