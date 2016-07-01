import psycopg2
import psycopg2.extras


def connect():
    return psycopg2.connect(host='db', user='postgres',
                            cursor_factory=psycopg2.extras.NamedTupleCursor)


## twitters ##

def get_twitter(cursor, twitter_id):
    cursor.execute('select id, api_id, screen_name from twitters where id=%s', (twitter_id,))
    return cursor.fetchone()

def update_twitters(cursor, api_twitters):
    cursor.execute('insert into twitters (api_id, screen_name) values '
                   + ','.join('%s' for _ in api_twitters) +
                   ' on conflict (api_id) do update set screen_name=excluded.screen_name,'
                   ' updated_time=now() returning id',
                   [(t['id'], t['screen_name']) for t in api_twitters])
    return [row.id for row in cursor.fetchall()]

def add_twitter_api_ids(cursor, api_ids):
    # note that you can't use "do nothing" and "returning", so we do a meaningless update:
    cursor.execute('insert into twitters (api_id) values ' + ','.join('(%s)' for _ in api_ids) +
                   ' on conflict (api_id) do update set id=twitters.id returning id',
                   api_ids)
    return [row.id for row in cursor.fetchall()]


## twitter_followers ##

def get_twitter_follower_ids(cursor, twitter_id):
    cursor.execute('select follower_id from twitter_followers where twitter_id=%s', (twitter_id,))
    return [row.follower_id for row in cursor.fetchall()]

def get_twitter_followers_updated_time(cursor, twitter_id):
    cursor.execute('select max(updated_time) from twitter_followers where twitter_id=%s',
                   (twitter_id,))
    return cursor.fetchone().max

def update_twitter_followers(cursor, twitter_id, follower_ids):
    cursor.execute('insert into twitter_followers (twitter_id, follower_id) values '
                   + ','.join('%s' for _ in follower_ids) +
                   ' on conflict (twitter_id, follower_id) do update set updated_time=now()',
                   [(twitter_id, follower_id) for follower_id in follower_ids])

def delete_old_twitter_followers(cursor, twitter_id, before):
    cursor.execute('delete from twitter_followers where twitter_id=%s and updated_time < %s',
                   (twitter_id, before))


## users ##

def get_users(cursor):
    cursor.execute('select users.id, users.twitter_id, access_token, access_token_secret'
                   ' from users')
    return cursor.fetchall()

def get_user(cursor, screen_name):
    cursor.execute('select users.id, users.twitter_id, access_token, access_token_secret'
                   ' from users, twitters where users.twitter_id=twitters.id and screen_name=%s',
                   (screen_name,))
    return cursor.fetchone()

def update_user(cursor, twitter_id, access_token, access_token_secret):
    cursor.execute('insert into users (twitter_id, access_token, access_token_secret)'
                   ' values (%s, %s, %s)'
                   ' on conflict (twitter_id) do update set access_token=excluded.access_token,'
                   ' access_token_secret=excluded.access_token_secret, updated_time=now()',
                   (twitter_id, access_token, access_token_secret))


## user_mentors ##

def add_user_mentors(cursor, user_id, mentor_ids):
    cursor.execute('insert into user_mentors (user_id, mentor_id) values '
                   + ','.join('%s' for _ in mentor_ids) +
                   ' on conflict (user_id, mentor_id) do nothing',
                   [(user_id, mentor_id) for mentor_id in mentor_ids])

def get_user_mentor_ids(cursor, user_id):
    cursor.execute('select mentor_id from user_mentors where user_id=%s', (user_id,))
    return [row.mentor_id for row in cursor.fetchall()]


## user_follows ##

def get_user_followed_ids(cursor, user_id):
    cursor.execute('select followed_id from user_follows where user_id=%s', (user_id,))
    return [row.follower_id for row in cursor.fetchall()]

def get_user_follows_count(cursor, user_id, since):
    cursor.execute('select count(*) from user_follows where user_id=%s and followed_time > %s',
                   (user_id, since))
    return cursor.fetchone().count

def get_user_followed_time(cursor, user_id):
    cursor.execute('select max(followed_time) from user_follows where user_id=%s', (user_id,))
    return cursor.fetchone().max

def get_user_follow(cursor, user_id, followed_id):
    cursor.execute('select followed_time, unfollowed_time from user_follows'
                   ' where user_id=%s and followed_id=%s', (user_id, followed_id))
    return cursor.fetchone()

def add_user_follow(cursor, user_id, followed_id):
    cursor.execute('insert into user_follows (user_id, followed_id) values (%s, %s)',
                   (user_id, followed_id))
