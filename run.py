import datetime
import logging
import random
import time

import api
import database


MIN_TIME = datetime.datetime.fromtimestamp(0, datetime.timezone.utc)
DAY = datetime.timedelta(days=1)
UPDATE_PERIOD = datetime.timedelta(days=7)
UNFOLLOW_PERIOD = datetime.timedelta(days=7)
FOLLOW_PERIOD = datetime.timedelta(seconds=10)
FOLLOWS_PER_DAY = 100


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def update_followers(db, user, twitter_id):
    with db, db.cursor() as cursor:
        twitter = database.get_twitter(cursor, twitter_id)
        updated_time = database.get_twitter_followers_updated_time(cursor, twitter_id) or MIN_TIME
    logging.info('followers for %s last updated at %s', twitter, updated_time)
    if now() - updated_time < UPDATE_PERIOD: return

    api_cursor = -1  # cursor=-1 requests first page
    while api_cursor:  # cursor=0 means no more pages
        logging.info('getting followers for %s at cursor=%s', twitter, api_cursor)
        data = api.get(user, 'followers/ids', user_id=twitter.api_id, cursor=api_cursor)
        api_cursor = data['next_cursor']
        logging.info('got %d followers, next_cursor=%s', len(data['ids']), api_cursor)

        with db, db.cursor() as cursor:
            twitter_ids = database.add_twitter_api_ids(cursor, data['ids'])
            database.update_twitter_followers(cursor, twitter.id, twitter_ids)

    with db, db.cursor() as cursor:  # delete followers who weren't seen again
        database.delete_old_twitter_followers(cursor, twitter.id, updated_time)


def follow(db, user, twitter_id):
    logging.info('preparing user %s to follow twitter_id=%d', user, twitter_id)
    with db, db.cursor() as cursor:
        followed_time = database.get_user_followed_time(cursor, user.id) or MIN_TIME
        follows_count = database.get_user_follows_count(cursor, user.id, now() - DAY)
        twitter = database.get_twitter(cursor, twitter_id)
    logging.info('user %s last followed at %s and has %d follows in the last day', user, followed_time, follows_count)
    if now() - followed_time < FOLLOW_PERIOD: raise Exception('user followed too recently')
    if follows_count >= FOLLOWS_PER_DAY: raise Exception('user exceeded follows for the day')

    logging.info(api.post(user, 'friendships/create', user_id=twitter.api_id))
    with db, db.cursor() as cursor:
        database.add_user_follow(cursor, user.id, twitter.id)


def run(db, user):
    logging.info('processing user %s', user)

    update_followers(db, user, user.twitter_id)

    with db, db.cursor() as cursor:
        mentor_ids = database.get_user_mentor_ids(cursor, user.id)
    for mentor_id in mentor_ids:
        update_followers(db, user, mentor_id)

    with db, db.cursor() as cursor:
        followed_ids = set(database.get_user_followed_ids(cursor, user.id))
        follow_ids = [id for mentor_id in mentor_ids
                      for id in database.get_twitter_follower_ids(cursor, mentor_id)
                      if id not in followed_ids]
    random.shuffle(follow_ids)
    for follow_id in follow_ids:
        follow(db, user, follow_id)
        # TODO delay = random.uniform(FOLLOW_PERIOD.total_seconds(), DAY.total_seconds() / FOLLOWS_PER_DAY)
        delay = random.uniform(1, 2) * FOLLOW_PERIOD.total_seconds()
        logging.info('sleeping for %.2f seconds', delay)
        time.sleep(delay)


def main():
    db = database.connect()

    with db, db.cursor() as cursor:
        users = database.get_users(cursor)
    for user in users:
        run(db, user)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
