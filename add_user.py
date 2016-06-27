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

    db = database.connect()
    with db, db.cursor() as cursor:
        cursor.execute(
            'insert into twitters (twitter_id, screen_name) values (%(id)s, %(screen_name)s)'
            ' on conflict (twitter_id) do update set screen_name=excluded.screen_name,'
            ' updated_time=now() returning id', user_data)
        twitter_id = cursor.fetchone().id
        cursor.execute(
            'insert into users (twitter_id, access_token, access_token_secret) values (%s, %s, %s)'
            ' on conflict (twitter_id) do update set access_token=excluded.access_token,'
            ' access_token_secret=excluded.access_token_secret, updated_time=now()',
            (twitter_id, user.access_token, user.access_token_secret))


if __name__ == '__main__':
    main()
