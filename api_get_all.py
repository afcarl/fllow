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
    data = []
    while True:
        max_id = min(x['id'] for x in data) - 1 if data else None
        data = api.get(user, path, max_id=max_id, **params)
        logging.info('got %d results', len(data))
        if not data: break
        all_data += data

    print(json.dumps(all_data, indent=2))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1], sys.argv[2], dict(sys.argv[i].split('=', 1) for i in range(3, len(sys.argv))))
