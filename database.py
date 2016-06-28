import psycopg2
import psycopg2.extras


def connect():
    return psycopg2.connect(host='db', user='postgres',
                            cursor_factory=psycopg2.extras.NamedTupleCursor)

def upsert_twitters(cursor, twitters):
    cursor.execute(
        'insert into twitters (twitter_id, screen_name) values ' + ','.join('%s' for _ in twitters)
        + ' on conflict (twitter_id) do update set screen_name=excluded.screen_name,'
        ' updated_time=now() returning id', [(t['id'], t['screen_name']) for t in twitters])
    return [row.id for row in cursor.fetchall()]

def get_user(cursor, screen_name):
    cursor.execute('select users.* from users, twitters where users.twitter_id=twitters.id and screen_name=%s', (screen_name,))
    return cursor.fetchone()

def upsert_user(cursor, twitter_id, access_token, access_token_secret):
    cursor.execute(
        'insert into users (twitter_id, access_token, access_token_secret) values (%s, %s, %s)'
        ' on conflict (twitter_id) do update set access_token=excluded.access_token,'
        ' access_token_secret=excluded.access_token_secret, updated_time=now()',
        (twitter_id, access_token, access_token_secret))

def insert_user_mentors(cursor, user_id, mentor_ids):
    cursor.execute(
        'insert into user_mentors (user_id, mentor_id) values ' + ','.join('%s' for _ in mentor_ids)
        + ' on conflict (user_id, mentor_id) do nothing',
        [(user_id, mentor_id) for mentor_id in mentor_ids])
