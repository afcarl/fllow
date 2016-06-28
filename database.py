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
