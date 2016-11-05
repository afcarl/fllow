from gevent import monkey
monkey.patch_all()

import datetime
import logging
import random
import time

import gevent

import api
import database


FOLLOWS_PER_DAY = 100
DAY = datetime.timedelta(days=1)
FOLLOW_PERIOD = datetime.timedelta(seconds=5)
UPDATE_PERIOD = 1 * DAY
UNFOLLOW_PERIOD = 3 * DAY


def now():
    return datetime.datetime.now(datetime.timezone.utc)

def log(user, message, *args, level=logging.INFO):
    logging.log(level, '[%s] ' + message, user.screen_name, *args)

def warn(user, message, *args):
    log(user, message, *args, level=logging.WARNING)


def update_followers(db, user, twitter_id):
    # only update followers if they haven't been updated recently:
    with db, db.cursor() as cursor:
        twitter = database.get_twitter(cursor, twitter_id)
        last_updated_time = database.get_twitter_followers_last_updated_time(cursor, twitter_id)
    log(user, 'maybe updating followers for %s last updated at %s', twitter, last_updated_time)
    if last_updated_time and now() - last_updated_time < UPDATE_PERIOD: return log(user, 'updated too recently')

    api_cursor = -1  # cursor=-1 requests first page
    while api_cursor:  # cursor=0 means no more pages
        log(user, 'getting cursor=%s', api_cursor)
        data = api.get(user, 'followers/ids', user_id=twitter.api_id, cursor=api_cursor)
        api_cursor = data['next_cursor']
        log(user, 'got %d followers, next_cursor=%s', len(data['ids']), api_cursor)

        with db, db.cursor() as cursor:
            twitter_ids = database.add_twitter_api_ids(cursor, data['ids'])
            database.update_twitter_followers(cursor, twitter.id, twitter_ids)

    if last_updated_time:  # delete followers who weren't seen again
        with db, db.cursor() as cursor:
            database.delete_old_twitter_followers(cursor, twitter.id, last_updated_time)


def unfollow(db, user, twitter_id):
    # only unfollow someone if this user followed them,
    # and they've had some time to follow them back but didn't:
    with db, db.cursor() as cursor:
        twitter = database.get_twitter(cursor, twitter_id)
        user_follow = database.get_user_follow(cursor, user.id, twitter.id)
        updated_time = database.get_twitter_followers_updated_time(cursor, user.twitter_id)
    log(user, 'unfollowing %s followed at %s updated at %s', twitter, user_follow.followed_time, updated_time)
    if not user_follow: return warn(user, 'but they were never followed')
    if user_follow.unfollowed_time: return warn(user, 'but they were already unfollowed at %s', user_follow.unfollowed_time)
    if not (updated_time and updated_time - user_follow.followed_time > UNFOLLOW_PERIOD): return warn(user, 'but they were followed too recently')

    api.post(user, 'friendships/destroy', user_id=twitter.api_id)
    with db, db.cursor() as cursor:
        database.set_user_unfollowed(cursor, user.id, twitter.id)


def follow(db, user, twitter_id):
    # only follow someone if this user hasn't already followed them,
    # and hasn't followed anyone too recently,
    # and hasn't followed too many people recently:
    with db, db.cursor() as cursor:
        twitter = database.get_twitter(cursor, twitter_id)
        user_follow = database.get_user_follow(cursor, user.id, twitter.id)
        last_followed_time = database.get_user_last_followed_time(cursor, user.id)
        follows_today = database.get_user_follows_count(cursor, user.id, now() - DAY)
    log(user, 'following %s last followed at %s and %d follows today', twitter, last_followed_time, follows_today)
    if user_follow: return warn(user, 'but already followed at %s', user_follow.followed_time)
    if last_followed_time and now() - last_followed_time < FOLLOW_PERIOD: return warn(user, 'but followed too recently')
    if follows_today >= FOLLOWS_PER_DAY: return warn(user, 'but too many follows today')

    api.post(user, 'friendships/create', user_id=twitter.api_id)
    with db, db.cursor() as cursor:
        database.add_user_follow(cursor, user.id, twitter.id)


def run(db, user):
    update_followers(db, user, user.twitter_id)

    with db, db.cursor() as cursor:
        mentor_ids = database.get_user_mentor_ids(cursor, user.id)
    for mentor_id in mentor_ids:
        update_followers(db, user, mentor_id)

    with db, db.cursor() as cursor:
        updated_time = database.get_twitter_followers_updated_time(cursor, user.twitter_id)
        before = updated_time - UNFOLLOW_PERIOD
        followed_ids = set(database.get_user_followed_ids(cursor, user.id, before=before,
                                                          exclude_unfollowed=True))
        follower_ids = set(database.get_twitter_follower_ids(cursor, user.twitter_id))
    log(user, 'followers updated at %s', updated_time)
    log(user, '%d followed before %s', len(followed_ids), before)
    followed_ids -= follower_ids  # don't unfollow people who followed back
    log(user, '%d have not followed back', len(followed_ids))
    for followed_id in followed_ids:
        unfollow(db, user, followed_id)

    with db, db.cursor() as cursor:
        followed_ids = set(database.get_user_followed_ids(cursor, user.id))
        follow_ids = [id for mentor_id in mentor_ids
                      for id in database.get_twitter_follower_ids(cursor, mentor_id)
                      if id not in followed_ids]
        follows_today = database.get_user_follows_count(cursor, user.id, now() - DAY)
    log(user, 'already has %d follows today', follows_today)
    if follows_today < FOLLOWS_PER_DAY:
        random.shuffle(follow_ids)
        follow_ids = follow_ids[:(FOLLOWS_PER_DAY - follows_today)]
        for follow_id in follow_ids:
            follow(db, user, follow_id)
            # TODO delay = random.uniform(FOLLOW_PERIOD.total_seconds(), DAY.total_seconds() / FOLLOWS_PER_DAY)
            delay = random.uniform(1, 2) * FOLLOW_PERIOD.total_seconds()
            log(user, 'sleeping for %.2f seconds', delay)
            time.sleep(delay)

def run_forever(db, user):
    while True:
        run(db, user)
        delay = random.uniform(0.1, 0.9) * DAY.total_seconds()
        log(user, 'sleeping for %.2f seconds', delay)
        time.sleep(delay)


def main():
    db = database.connect()

    with db, db.cursor() as cursor:
        users = database.get_users(cursor)

    gevent.joinall([gevent.spawn(run_forever, db, user)
                    for user in users])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    main()
