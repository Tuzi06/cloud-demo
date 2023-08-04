# from selenium.webdriver import Chrome,ChromeOptions
# from selenium.webdriver.chrome.service import Service
# from flask import Flask,request
# import os,time
# from multiprocessing import Process,Pipe
# from utls import GCloudConnection
# from selenium import webdriver


# class Scraper(GCloudConnection):
#     def __init__(self):
#         self.state = 'idle'
#         self.parent,self.child = Pipe()
#         options = ChromeOptions()
#         options.add_argument('--ignore-ssl-errors=yes')
#         options.add_argument('--ignore-certificate-errors')
#         self.driver = webdriver.Remote(command_executor='http://172.17.0.2:4444',options=options)
    
#     def run(self,pipe):
#         self.child = pipe
#         for _ in range(1000):
#             time.sleep(60)

# app = Flask(__name__)

# @app.route('/start')
# def start_child_process(): #Gunicorn does not allow the creation of new processes before the app creation, so we need to define this route

#     global scraper
#     scraper = Scraper()
#     p = Process(target = scraper.run,args = [scraper.child])
#     p.start()
#     print('scraper running')
#     return "Scraper running"

# @app.route('/job')
# def process_job():
#     time.sleep(60)
#     scraper.child.send('scraper-detected') #sends a job to the Scraper through the "parent" end of the pipe

# @app.route('/state')
# def current_state():
#     return 'suceed reach out'
#     try:
#         if scraper.parent.poll(timeout=3): #checks if there are new messages from the child process
#             scraper.state = scraper.parent.recv() # updates the state in such case
#         return scraper.state
#     except:
#         return "not-started"
# @app.route('/kill')
# def kill():
#     func = request.environ.get('werkzeug.server.shutdown')
#     if func is None:
#         raise RuntimeError('Not running with the Werkzeug Server')
#     func()
#     return "Shutting down..."

# if __name__ == "__main__":
#     port = int(os.environ.get('PORT', 5000))
#     app.run(debug=False, host='0.0.0.0', port=port)
import os
import pickle
from flask import Flask
import requests


app = Flask(__name__)

@app.route('/i')
def test():
    code = 0
    username = 'user-spal93ysiq-sessionduration-1'
    password = 'iLvsubq3727BujKvZx'
    proxy = f"http://{username}:{password}@gate.smartproxy.com:10000"
    for _ in range(10):
        code = requests.get('https://www.instagram.com/attorneycrump/?__a=1&__d=dis',proxies = {
            'http': proxy,
            'https': proxy
        }).status_code
        print (code)
    return str(code)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)