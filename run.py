import datetime
import logging

import api
import database


UPDATE_PERIOD = datetime.timedelta(days=7)


def update_followers(db, user, twitter):
    api_cursor = -1  # cursor=-1 requests first page
    while api_cursor:  # cursor=0 means no more pages
        logging.debug('getting follower for %s at cursor=%s', twitter, api_cursor)
        data = api.get(user, 'followers/ids', user_id=twitter.api_id, cursor=api_cursor)
        api_cursor = data['next_cursor']
        logging.debug('got %d followers, next_cursor=%s', len(data['ids']), api_cursor)

        with db, db.cursor() as cursor:
            twitter_ids = database.add_twitter_api_ids(cursor, data['ids'])
            database.update_twitter_followers(cursor, twitter.id, twitter_ids)

def update_user_stale_mentor_followers(db, user):
    with db, db.cursor() as cursor:
        stale_mentor_ids = database.get_user_mentor_ids(cursor, user.id, updated_before=UPDATE_PERIOD)
    for mentor_id in stale_mentor_ids:
        update_followers(db, user, mentor_id)
