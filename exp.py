from requests import session

headers ={'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.28 Safari/537.36'}
s = session()
s.headers = headers

username = 'user-spal93ysiq-sessionduration-5'
password ='eIg4qQxqoA4bG74yun'
proxy = f"https://{username}:{password}@us.smartproxy.com:10001"
s.proxies.update({'http':proxy,'https':proxy})
response = s.get('https://www.instagram.com/p/CviKG1Tts1r/?z')
print(response.status_code)
# open('res.html','w').write(str(response.content))
