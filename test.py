from flask import Flask
import requests

app = Flask(__name__)

@app.route('/i')
def test():
    code = 0
    username = 'spal93ysiq'
    password = 'iLvsubq3727BujKvZx'
    proxy = f"http: //{username}:{password}@gate.smartproxy.com:10000"
    for i in range(1000):
        response = requests.get('https://www.instagram.com/attorneycrump/?__a=1&__d=dis',proxies=proxy)
        if response.status_code != 200:
            return 'scraper detected'
    return 'success'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=False)