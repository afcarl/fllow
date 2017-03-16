import datetime
import logging
import time

import requests
import requests_oauthlib

import secret


CONSUMER_KEY = '9QswJgHJg1w1IzyVklleqS9Wb'
RETRY_PERIOD = datetime.timedelta(minutes=1)

session = requests  # requests.Session() keep-alive seems to die eventually :/

def get_request_token():
    return (requests_oauthlib.OAuth1Session(CONSUMER_KEY, secret.CONSUMER_SECRET)
            .fetch_request_token('https://api.twitter.com/oauth/request_token',
                                 params=dict(oauth_callback='oob')))

def get_authorize_url(request_token):
    return 'https://api.twitter.com/oauth/authorize?oauth_token=' + request_token

def get_access_token(request_token, verifier):
    return (requests_oauthlib.OAuth1Session(CONSUMER_KEY, secret.CONSUMER_SECRET, request_token,
                                            verifier=verifier)
            .fetch_access_token('https://api.twitter.com/oauth/access_token'))

def get(user, path, **params):
    return request('GET', user, path, **params)

def post(user, path, **params):
    return request('POST', user, path, **params)

def request(method, user, path, retry=True, **params):
    response = session.request(method, 'https://api.twitter.com/1.1/' + path + '.json',
                               params=params,
                               auth=requests_oauthlib.OAuth1(CONSUMER_KEY, secret.CONSUMER_SECRET,
                                                             user.access_token,
                                                             user.access_token_secret))

    if response.status_code == 429 and retry:
        reset_time = int(response.headers['x-rate-limit-reset'])
        sleep_time = max(0, 1 + reset_time - time.time())  # sleep an extra second to be safe
        logging.warn('rate limit exceeded; sleeping %.1f seconds until rate limit resets...',
                     sleep_time)
        time.sleep(sleep_time)
        return request(method, user, path, retry=False, **params)
    elif response.status_code >= 500:
        logging.warn('internal twitter error %d: %s', response.status_code, response.text)
        logging.warn('sleeping for %s', RETRY_PERIOD)
        time.sleep(RETRY_PERIOD.total_seconds())

    response.raise_for_status()
    return response.json()
