from selenium.webdriver import Chrome,ChromeOptions
from selenium.webdriver.chrome.service import Service
from flask import Flask,request
import os,time
from multiprocessing import Process,Pipe
from utls import GCloudConnection

class Scraper(GCloudConnection):
    def __init__(self):
        self.state = 'idle'
        self.parent,self.child = Pipe()
        self.driver = Chrome(Service = Service('./lowlevel/chromedriver_linux64/chromedriver'),options=ChromeOptions())

    def run(self,pipe):
        self.child = pipe
        for _ in range(1000):
            time.sleep(60)

app = Flask(__name__)

@app.route('/start')
def start_child_process(): #Gunicorn does not allow the creation of new processes before the app creation, so we need to define this route

    global scraper
    scraper = Scraper()
    p = Process(target = scraper.run(),args = scraper.child)
    print('scraper running')
    return "Scraper running"

@app.route('/job')
def process_job():
    time.sleep(60)
    scraper.child.send('scraper-detected') #sends a job to the Scraper through the "parent" end of the pipe

@app.route('/state')
def current_state():
    try:
        if scraper.parent.poll(timeout=3): #checks if there are new messages from the child process
            scraper.state = scraper.parent.recv() # updates the state in such case
        return scraper.state
    except:
        return "not-started"
@app.route('/kill')
def kill():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return "Shutting down..."

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 80))
    app.run(debug=True, host='0.0.0.0', port=port)