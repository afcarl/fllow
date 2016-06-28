import logging
import sys

import database
import twitter


def main(user, mentors):
    db = database.connect()

    with db, db.cursor() as cursor:
        cursor.execute('select users.* from users, twitters where users.twitter_id=twitters.id and screen_name=%s', (user,))
        user = cursor.fetchone()

    mentor_data = twitter.get(user, 'users/lookup', screen_name=','.join(mentors))
    unknown = mentors - {m['screen_name'] for m in mentor_data}
    if unknown: logging.warn('unknown screen names: %s', unknown)

    with database.connect() as db, db.cursor() as cursor:
        mentor_ids = database.upsert_twitters(cursor, mentor_data)
        cursor.execute(
            'insert into user_mentors (user_id, mentor_id) values '
            + ','.join('%s' for _ in mentor_ids) +
            ' on conflict (user_id, mentor_id) do nothing',
            [(user.id, mentor_id) for mentor_id in mentor_ids])



if __name__ == '__main__':
    main(sys.argv[1], set(sys.argv[2:]))
