import requests
import requests_oauthlib

import secret


CONSUMER_KEY = '9QswJgHJg1w1IzyVklleqS9Wb'

session = requests.Session()

def get_request_token():
    return (requests_oauthlib.OAuth1Session(CONSUMER_KEY, secret.CONSUMER_SECRET)
            .fetch_request_token('https://api.twitter.com/oauth/request_token',
                                 params=dict(oauth_callback='oob')))

def get_authorize_url(request_token):
    return 'https://api.twitter.com/oauth/authorize?oauth_token=' + request_token

def get_access_token(request_token, request_token_secret, pin):
    return (requests_oauthlib.OAuth1Session(CONSUMER_KEY, secret.CONSUMER_SECRET,
                                            request_token, request_token_secret,
                                            verifier=pin)
            .fetch_access_token('https://api.twitter.com/oauth/access_token'))

def get(user, path, **params):
    return request('GET', user, path, **params)

def post(user, path, **params):
    return request('POST', user, path, **params)

def request(method, user, path, **params):
    return session.request(method, 'https://api.twitter.com/1.1/' + path + '.json', params=params,
                           auth=requests_oauthlib.OAuth1(CONSUMER_KEY, secret.CONSUMER_SECRET,
                                                         user.access_token,
                                                         user.access_token_secret)).json()
