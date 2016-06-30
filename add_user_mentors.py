import logging
import sys

import api
import database


def main(user, mentors):
    db = database.connect()

    with db, db.cursor() as cursor:
        user = database.get_user(cursor, user)

    mentor_data = api.get(user, 'users/lookup', screen_name=','.join(mentors))
    unknown = {m.lower() for m in mentors} - {m['screen_name'].lower() for m in mentor_data}
    if unknown: logging.warning('unknown screen names: %s', unknown)

    with db, db.cursor() as cursor:
        mentor_ids = database.update_twitters(cursor, mentor_data)
        database.add_user_mentors(cursor, user.id, mentor_ids)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
