from gevent import monkey; monkey.patch_all()

import datetime
import logging
import random
import time

import gevent
import requests

import api
import database


FOLLOWS_PER_DAY = 200
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


def update_leaders(db, user, follower_id):
    # only update leaders if they haven't been updated recently:
    with db, db.cursor() as cursor:
        twitter = database.get_twitter(cursor, follower_id)
        updated_time = database.get_twitter_leaders_updated_time(cursor, follower_id)
        cutoff_time = database.get_current_time(cursor)
    log(user, 'maybe updating leaders for %s updated at %s', twitter, updated_time)
    if updated_time and now() - updated_time < UPDATE_PERIOD:
        return log(user, 'updated too recently')

    api_cursor = -1  # cursor=-1 requests first page
    while api_cursor:  # cursor=0 means no more pages
        log(user, 'getting cursor=%s', api_cursor)
        data = api.get(user, 'friends/ids', user_id=twitter.api_id, cursor=api_cursor)
        api_cursor = data['next_cursor']
        log(user, 'got %d leaders, next_cursor=%s', len(data['ids']), api_cursor)

        with db, db.cursor() as cursor:
            leader_ids = database.add_twitter_api_ids(cursor, data['ids'])
            database.update_twitter_leaders(cursor, follower_id, leader_ids)

    # delete leaders who weren't seen again:
    with db, db.cursor() as cursor:
        database.delete_old_twitter_leaders(cursor, follower_id, cutoff_time)


def update_followers(db, user, leader_id):
    # only update followers if they haven't been updated recently:
    with db, db.cursor() as cursor:
        twitter = database.get_twitter(cursor, leader_id)
        updated_time = database.get_twitter_followers_updated_time(cursor, leader_id)
        cutoff_time = database.get_current_time(cursor)
    log(user, 'maybe updating followers for %s updated at %s', twitter, updated_time)
    if updated_time and now() - updated_time < UPDATE_PERIOD:
        return log(user, 'updated too recently')

    api_cursor = -1  # cursor=-1 requests first page
    while api_cursor:  # cursor=0 means no more pages
        log(user, 'getting cursor=%s', api_cursor)
        data = api.get(user, 'followers/ids', user_id=twitter.api_id, cursor=api_cursor)
        api_cursor = data['next_cursor']
        log(user, 'got %d followers, next_cursor=%s', len(data['ids']), api_cursor)

        with db, db.cursor() as cursor:
            follower_ids = database.add_twitter_api_ids(cursor, data['ids'])
            database.update_twitter_followers(cursor, leader_id, follower_ids)

    # delete followers who weren't seen again:
    with db, db.cursor() as cursor:
        database.delete_old_twitter_followers(cursor, leader_id, cutoff_time)


def unfollow(db, user, leader_id):
    # only unfollow someone if this user followed them,
    # and they've had some time to follow them back but didn't:
    with db, db.cursor() as cursor:
        twitter = database.get_twitter(cursor, leader_id)
        user_follow = database.get_user_follow(cursor, user.id, leader_id)
        user_unfollow = database.get_user_unfollow(cursor, user.id, leader_id)
        updated_time = database.get_twitter_followers_updated_time(cursor, user.twitter_id)
    log(user, 'unfollowing %s followed at %s updated at %s',
        twitter, user_follow, updated_time)
    if not user_follow:
        return warn(user, 'but they were never followed')
    if user_unfollow:
        return warn(user, 'but they were already unfollowed at %s', user_unfollow.time)
    if not (updated_time and updated_time - user_follow.time > UNFOLLOW_PERIOD):
        return warn(user, 'but they were followed too recently')

    try:
        api.post(user, 'friendships/destroy', user_id=twitter.api_id)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 404:
            raise e
        return warn(user, 'failed to unfollow %s [%d %s]',
                    twitter, e.response.status_code, e.response.text)

    with db, db.cursor() as cursor:
        database.add_user_unfollow(cursor, user.id, leader_id)


def follow(db, user, leader_id):
    # only follow someone if this user hasn't already followed them,
    # and hasn't followed anyone too recently,
    # and hasn't followed too many people recently:
    with db, db.cursor() as cursor:
        twitter = database.get_twitter(cursor, leader_id)
        user_follow = database.get_user_follow(cursor, user.id, leader_id)
        last_follow_time = database.get_user_follows_last_time(cursor, user.id)
        follows_today = database.get_user_follows_count(cursor, user.id, now() - DAY)
    log(user, 'following %s last followed at %s and %d follows today',
        twitter, last_follow_time, follows_today)
    if user_follow:
        return warn(user, 'but already followed at %s', user_follow.time)
    if last_follow_time and now() - last_follow_time < FOLLOW_PERIOD:
        return warn(user, 'but followed too recently')
    if follows_today >= FOLLOWS_PER_DAY:
        return warn(user, 'but too many follows today')

    try:
        api.post(user, 'friendships/create', user_id=twitter.api_id)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 403:
            raise e
        # 403 can mean blocked or already following
        warn(user, 'marking %s as followed [%d %s]',
             twitter, e.response.status_code, e.response.text)

    with db, db.cursor() as cursor:
        database.add_user_follow(cursor, user.id, leader_id)


def run(db, user):
    with db, db.cursor() as cursor:
        mentor_ids = database.get_user_mentor_ids(cursor, user.id)
    for mentor_id in mentor_ids:
        update_followers(db, user, mentor_id)

    update_leaders(db, user, user.twitter_id)
    update_followers(db, user, user.twitter_id)

    with db, db.cursor() as cursor:
        leader_ids = set(database.get_twitter_leader_ids(cursor, user.twitter_id))
        follower_ids = set(database.get_twitter_follower_ids(cursor, user.twitter_id))
        updated_time = database.get_twitter_followers_updated_time(cursor, user.twitter_id)
        before = updated_time - UNFOLLOW_PERIOD
        followed_ids = set(database.get_user_follow_leader_ids(cursor, user.id, before=before))
    log(user, '%d followers, updated at %s', len(follower_ids), updated_time)
    log(user, '%d currently followed', len(leader_ids))
    log(user, '%d followed before %s', len(followed_ids), before)
    log(user, '…of whom %d are still followed', len(followed_ids & leader_ids))
    # don't unfollow people we aren't following, or who followed back:
    unfollow_ids = followed_ids & leader_ids - follower_ids
    log(user, '…of whom %d have not followed back', len(unfollow_ids))
    for unfollow_id in unfollow_ids:
        unfollow(db, user, unfollow_id)

    with db, db.cursor() as cursor:
        followed_ids = set(database.get_user_follow_leader_ids(cursor, user.id))
        followed_ids |= leader_ids
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
    try:
        while True:
            run(db, user)
            delay = random.uniform(0.1, 0.9) * DAY.total_seconds()
            log(user, 'sleeping for %.2f seconds', delay)
            time.sleep(delay)
    except requests.exceptions.HTTPError as e:
        log(user, 'http error response: %s', e.response.text, level=logging.ERROR)
        raise e


def main():
    db = database.connect()

    with db, db.cursor() as cursor:
        users = database.get_users(cursor)

    gevent.joinall([gevent.spawn(run_forever, db, user)
                    for user in users])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    main()
