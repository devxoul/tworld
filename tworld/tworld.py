# -*- coding: utf-8 -*-

import json
import requests
import rsa
import urlparse


session = requests.Session()


def query_from_url(url):
    query_str = urlparse.urlparse(url).query
    return query_from_string(query_str)


def query_from_string(query_str):
    return {k: v[0] for k, v in urlparse.parse_qs(query_str).iteritems()}


def get_login_page_url():
    url = 'http://www.tworld.co.kr/twd/common/loginout/view/login_popup.jsp'
    r = session.get(url)
    return r.text.split('self.location.href = "')[1].split('"')[0]


def get_encryption_data(username, password):
    url = 'https://auth.skt-id.co.kr/auth/api/v1/keys.do'
    r = session.post(url, data={'valueType': 'hex'})
    data = json.loads(r.text)
    kid = data['kid']

    n = long(data['n'], 16)
    e = long(data['e'], 16)
    key = rsa.PublicKey(n, e)

    nonce = data['nonce']
    plaintext = '{}|{}|{}'.format(username, password, nonce)
    ciphertext = rsa.encrypt(plaintext, key).encode('hex')

    return {
        'cipher_kid': kid,
        'ciphertext': ciphertext,
    }


def get_data(username, password):
    login_page_url = get_login_page_url()
    data = query_from_url(login_page_url)
    data['answer'] = ''
    data['_service_type'] = ''
    data['chnlEasyLoginType'] = 'E1'
    data['issuing_type'] = 10  # ID_PASS
    data['tword_group_yn'] = 'Y'

    html = session.get(login_page_url).text
    rq = html.split('<input type="hidden" name="rq" id="rq" value="')[1]\
             .split('"')[0]
    sid = html.split('<input type="hidden" name="sid" id="sid" value="')[1]\
              .split('"')[0]
    data['rq'] = rq
    data['sid'] = sid
    data.update(get_encryption_data(username, password))
    return data


def fuck(url):
    if '#' not in url:
        raise Exception()

    print url

    params = query_from_string(url.split('#')[1])
    request_url = 'http://www.tworld.co.kr/tidRequestServlet.do'
    session.get(request_url, params=params)


def login(username, password):
    # 1
    data = get_data(username, password)

    # 2
    url = 'https://auth.skt-id.co.kr/auth/type/login/loginPreChecker.do'
    r = session.post(url, data=data)
    if r.status_code not in xrange(200, 300):
        message = json.loads(r.text).get('resultMsg', '')
        raise Exception(message)

    # 3
    url = 'https://auth.skt-id.co.kr/auth/type/login/loginProcess.do'
    r = session.post(url, data=data)
    html = r.text

    # 4
    url = 'http://sktsso.tworld.co.kr/createsubcookie.jsp'
    r = session.post(url, data={'mode': 'check'})
    if '"Y"' in r.text:
        url = html.split('location.href="')[1].split('"')[0]
        req_url = session.get(url).url
    else:
        target_url = html.split('var targetURL ="')[1].split('"')[0]
        param = html.split('var redirecParma ="')[1].split('"')[0]
        endpoint = html.split('var redirectEndPoint ="')[1].split('"')[0]
        url = target_url + param + endpoint
        req_url = session.get(url).url

    # 5
    if '#' not in req_url:
        raise Exception()
    params = query_from_string(req_url.split('#')[1])
    url = 'http://www.tworld.co.kr/tidRequestServlet.do'
    r = session.get(url, params=params)
    return 'http://www.tworld.co.kr/twd/main/index.jsp' in r.text


def logged_in():
    url = 'http://www.tworld.co.kr/normal.do'
    params = {
        'serviceId': 'S_MYTW0028',
        'viewId': 'V_MYTW0130',
    }
    r = session.get(url, params=params)
    return 'http://auth.skt-id.co.kr/auth/authorize.do?' not in r.text


print login('devxoul', 'jx$0yu!L6o7u4x')
# print logged_in()
