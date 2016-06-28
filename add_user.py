import collections

import database
import twitter


User = collections.namedtuple('User', ('access_token', 'access_token_secret'))


def main():
    request_token = twitter.get_request_token()
    pin = input('Go to {} and enter the PIN here: '
                .format(twitter.get_authorize_url(request_token['oauth_token'])))
    access_token = twitter.get_access_token(request_token['oauth_token'],
                                            request_token['oauth_token_secret'], pin)
    user = User(access_token['oauth_token'], access_token['oauth_token_secret'])
    user_data = twitter.get(user, 'account/verify_credentials')

    with database.connect() as db, db.cursor() as cursor:
        twitter_id, = database.upsert_twitters(cursor, [user_data])
        database.upsert_user(cursor, twitter_id, user.access_token, user.access_token_secret)

if __name__ == '__main__':
    main()
