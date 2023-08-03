from flask import Flask,request,jsonify
import os,logging,time,pickle,queue,requests,json 
from multiprocessing import Process,Pipe
from lowlevel import main
class Scraper:
    def __init__(self) -> None:
        self.state = 'idle'
        self.parent, self.child = Pipe()
    
    def run(self, pipe):
        self.child = pipe
        job = self.child.recv()
        if job != None:
            self.child.send('busy')
            link,_ = job.values()
            response = requests.get(f"{link}?__a=1&d=dis")
            if response.status_code == 200:  
                shortCodes = [[node['node']['shortcode'] for node in response['graphql']['user']['edge_felix_video_timeline']['edges']]] 
                self.child.send('idle')  
                return shortCodes  
            else:
                self.child.send('scraping-detected')
                return


app = Flask(__name__)

@app.route('/start')
def start_child_process(): #Gunicorn does not allow the creation of new processes before the app creation, so we need to define this route
    global scraper
    scraper = Scraper()

    return "Scraper running"

@app.route('/job')
def process_job():
    scraper.parent.send(request.args)
    shortCodes = scraper.run(scraper.pipe)
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