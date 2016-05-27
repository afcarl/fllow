import logging

import requests
import requests_oauthlib


logging.basicConfig(level=logging.DEBUG)

session = requests.Session()
session.auth = requests_oauthlib.OAuth1(
    client_key='9QswJgHJg1w1IzyVklleqS9Wb',
    client_secret=input('application secret: '),
    resource_owner_key='22175229-iHYC3pAem4YT7Pg8IQpDwdwpSu0B35e9ajQ8G77LB',
    resource_owner_secret=input('user secret: ')
)

def get(path, **params):
    return session.get('https://api.twitter.com/1.1/' + path + '.json', params=params).json()

print(get('followers/ids', screen_name='hrldcpr'))
