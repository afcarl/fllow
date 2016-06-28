import logging
import sys

import database
import twitter


def main(user, mentors):
    db = database.connect()

    with db, db.cursor() as cursor:
        user = database.get_user(cursor, user)

    mentor_data = twitter.get(user, 'users/lookup', screen_name=','.join(mentors))
    unknown = mentors - {m['screen_name'] for m in mentor_data}
    if unknown: logging.warn('unknown screen names: %s', unknown)

    with database.connect() as db, db.cursor() as cursor:
        mentor_ids = database.upsert_twitters(cursor, mentor_data)
        database.insert_user_mentors(cursor, user.id, mentor_ids)


if __name__ == '__main__':
    main(sys.argv[1], set(sys.argv[2:]))
