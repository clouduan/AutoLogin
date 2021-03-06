import os
import re
import requests
import http.cookiejar
import logging

from config import account
from config import cookies
from urllib.parse import urljoin

home_url = "https://readfree.me"
post_url = "https://readfree.me/auth/login/?next=/"
current_path = os.path.dirname(os.path.abspath(__file__))
cookies_path = os.path.join(current_path, "readfree.cookies")
logfile_path = os.path.join(current_path, "readfree.log")
captcha_path = os.path.join(current_path, "captcha.png")

headers = {}
headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/51.0"
headers['Host'] = 'readfree.me'
headers['Content-Type'] = 'application/x-www-form-urlencoded'
s = requests.Session()
s.headers.update(headers)

logging.basicConfig(filename=logfile_path,
                    level='INFO',
                    format="%(asctime)s [line: %(lineno)d] - %(message)s",
                    filemode='w')


def load_cookies():
    cj = http.cookiejar.LWPCookieJar()
    cj.load(cookies_path, ignore_expires=True, ignore_discard=True)
    ck = requests.utils.dict_from_cookiejar(cj)
    logging.info("Cookies file was loaded")
    return ck


def save_cookies(cookies):
    cj = http.cookiejar.LWPCookieJar()
    ck = {c.name: c.value for c in cookies}
    requests.utils.cookiejar_from_dict(ck, cj)
    cj.save(cookies_path, ignore_expires=True, ignore_discard=True)
    logging.info('Cookies file was updated.')


def process_cookies():
    cj = http.cookiejar.LWPCookieJar()
    requests.utils.cookiejar_from_dict(cookies, cj)
    cj.save(cookies_path, ignore_expires=True, ignore_discard=True)
    logging.info('Pre-set cookies was transformed.')


def login_by_cookies():
    if not os.path.exists(cookies_path):
        logging.info("Cookies file doesn't exist.")

        if cookies['csrftoken'] and cookies['sessionid']:
            logging.info("Use pre-set cookies.")
            process_cookies()
        else:
            return
    else:
        logging.info("Cookies file exists.")

    ck = load_cookies()
    s.cookies.update(ck)
    req = s.get(home_url)
    if req.status_code == 200:
        logging.info("Login by cookies successfully")
        save_cookies(s.cookies)
        return True
    else:
        logging.error('Cookies expired, please update the cookies')


def login():
    req = s.get(home_url)
    captcha_url = re.findall(r'<img src="(.*?)"', req.text)[0]
    captcha_url = urljoin(home_url, captcha_url)
    req2 = s.get(captcha_url)
    with open(captcha_path, 'wb') as f:
        f.write(req2.content)
        logging.info('Captcha saved.')

    form_data = {}
    form_data['login'] = account['email']
    form_data['password'] = account['password']
    form_data['captcha_0'] = re.findall(r'name="captcha_0".*?value="(.*?)"', req.text)[0]
    form_data['csrfmiddlewaretoken'] = re.findall(
        r'name=["\']csrfmiddlewaretoken["\'] value=["\'](.*?)["\']', req.text)[0]
    form_data['captcha_1'] = input('Please open captcha.png and input it:')

    req2 = s.post(post_url, data=form_data, allow_redirects=False)

    if req2.status_code != 302:
        logging.error('Login failed.')
        return False
    else:
        s.get(req2.url)
        logging.info('Login successfully.')
        save_cookies(s.cookies)
        return True


def main():
    if login_by_cookies():
        print("Login by cookies successfully!")
    else:
        while True:
            if login():
                print("Login by password successfully!")
                break


if __name__ == '__main__':
    main()
