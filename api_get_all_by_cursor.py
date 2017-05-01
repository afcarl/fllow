import json
import logging
import sys

import api
import database


def main(user, path, params):
    db = database.connect()

    with db, db.cursor() as cursor:
        user = database.get_user(cursor, user)

    all_data = []
    cursor = -1  # cursor=-1 requests first page
    while cursor:  # cursor=0 means no more pages
        logging.info('loading cursor=%d', cursor)
        data = api.get(user, path, cursor=cursor, **params)
        cursor = data['next_cursor']
        all_data.append(data)

    print(json.dumps(all_data, indent=2))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1], sys.argv[2], dict(sys.argv[i].split('=', 1) for i in range(3, len(sys.argv))))
