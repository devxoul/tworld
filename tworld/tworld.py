# -*- coding: utf-8 -*-

import json
import requests
import rsa
import urlparse


class TWorld(object):

    session = requests.Session()

    def __init__(self, username=None, password=None):
        if username and password:
            self.login(username, password)

    def _query_from_url(self, url):
        query_str = urlparse.urlparse(url).query
        return self._query_from_string(query_str)

    def _query_from_string(self, query_str):
        return {k: v[0] for k, v in urlparse.parse_qs(query_str).iteritems()}

    def _get_login_page_url(self):
        url = 'http://www.tworld.co.kr'\
              '/twd/common/loginout/view/login_popup.jsp'
        r = self.session.get(url)
        return r.text.split('self.location.href = "')[1].split('"')[0]

    def _get_encryption_data(self, username, password):
        url = 'https://auth.skt-id.co.kr/auth/api/v1/keys.do'
        r = self.session.post(url, data={'valueType': 'hex'})
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

    def _get_login_data(self, username, password):
        login_page_url = self._get_login_page_url()
        data = self._query_from_url(login_page_url)
        data['answer'] = ''
        data['_service_type'] = ''
        data['chnlEasyLoginType'] = 'E1'
        data['issuing_type'] = 10  # ID_PASS
        data['tword_group_yn'] = 'Y'

        html = self.session.get(login_page_url).text
        rq = html.split('input type="hidden" name="rq" id="rq" value="')[1]\
                 .split('"')[0]
        sid = html.split('input type="hidden" name="sid" id="sid" value="')[1]\
                  .split('"')[0]
        data['rq'] = rq
        data['sid'] = sid
        data.update(self._get_encryption_data(username, password))
        return data

    def login(self, username, password):
        # 1
        data = self._get_login_data(username, password)

        # 2
        url = 'https://auth.skt-id.co.kr/auth/type/login/loginPreChecker.do'
        r = self.session.post(url, data=data)
        if r.status_code not in xrange(200, 300):
            message = json.loads(r.text).get('resultMsg', '')
            raise Exception(message)

        # 3
        url = 'https://auth.skt-id.co.kr/auth/type/login/loginProcess.do'
        r = self.session.post(url, data=data)
        if r.status_code not in xrange(200, 300):
            raise Exception()
        html = r.text

        # 4
        url = 'http://sktsso.tworld.co.kr/createsubcookie.jsp'
        r = self.session.post(url, data={'mode': 'check'})
        if r.status_code not in xrange(200, 300):
            raise Exception()
        if '"Y"' in r.text:
            url = html.split('location.href="')[1].split('"')[0]
            req_url = self.session.get(url).url
        else:
            target_url = html.split('var targetURL ="')[1].split('"')[0]
            param = html.split('var redirecParma ="')[1].split('"')[0]
            endpoint = html.split('var redirectEndPoint ="')[1].split('"')[0]
            url = target_url + param + endpoint
            req_url = self.session.get(url).url

        # 5
        if '#' not in req_url:
            raise Exception()
        params = self._query_from_string(req_url.split('#')[1])
        url = 'http://www.tworld.co.kr/tidRequestServlet.do'
        r = self.session.get(url, params=params)
        succeeded = 'http://www.tworld.co.kr/twd/main/index.jsp' in r.text
        if not succeeded:
            raise Exception()

    def logged_in(self):
        url = 'http://www.tworld.co.kr/normal.do'
        params = {
            'serviceId': 'S_MYTW0028',
            'viewId': 'V_MYTW0130',
        }
        r = self.session.get(url, params=params)
        logged_in = 'http://auth.skt-id.co.kr/auth/authorize.do?' not in r.text
        return logged_in
