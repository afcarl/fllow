import collections
import statistics

import flask

import api
import database
import secret


User = collections.namedtuple('User', ('access_token', 'access_token_secret'))

app = flask.Flask(__name__)
app.secret_key = secret.APP_SECRET

db = database.connect()


@app.route('/authorize')
def authorize():
    if 'oauth_token' not in flask.request.args:
        request_token = api.get_request_token(flask.request.url)
        return flask.redirect(api.get_authorize_url(request_token['oauth_token']))

    access_token = api.get_access_token(flask.request.args['oauth_token'],
                                        flask.request.args['oauth_verifier'])
    user = User(access_token['oauth_token'], access_token['oauth_token_secret'])
    user_data = api.get(user, 'account/verify_credentials')

    with db, db.cursor() as cursor:
        twitter_id, = database.update_twitters(cursor, [user_data])
        database.update_user(cursor, twitter_id, user.access_token, user.access_token_secret)

    flask.session['screen_name'] = user_data['screen_name']
    return flask.redirect(flask.url_for('user', screen_name=user_data['screen_name']))


@app.route('/users')
def users():
    with db, db.cursor() as cursor:
        users = database.get_users(cursor)
    return flask.render_template('users.html', users=users)

@app.route('/users/<screen_name>')
def user(screen_name):
    with db, db.cursor() as cursor:
        user = database.get_user(cursor, screen_name)
        mentors = database.get_user_mentors(cursor, user.id)
        follow_day_counts = as_timestamps(database.get_user_follow_day_counts(cursor, user.id))
        unfollow_day_counts = as_timestamps(database.get_user_unfollow_day_counts(cursor, user.id))
        follower_day_counts = as_timestamps(database.get_twitter_follower_day_counts(cursor,
                                                                                     user.twitter_id))
        leader_day_counts = as_timestamps(database.get_twitter_leader_day_counts(cursor,
                                                                                 user.twitter_id))

    follow_rate = average_daily_rate(follow_day_counts) or 0
    follow_rate_week = average_daily_rate(follow_day_counts, days=7) or 0
    unfollow_rate = average_daily_rate(unfollow_day_counts) or 0
    unfollow_rate_week = average_daily_rate(unfollow_day_counts, days=7) or 0
    follower_rate = average_daily_rate(follower_day_counts)
    follower_rate_week = average_daily_rate(follower_day_counts, days=7)
    leader_rate = average_daily_rate(leader_day_counts)
    leader_rate_week = average_daily_rate(leader_day_counts, days=7)

    return flask.render_template('user.html', **locals())

def as_timestamps(day_counts):
    return [(day.timestamp(), count) for day, count in day_counts]

def average_daily_rate(day_counts, days=None):
    counts = [count for day, count in day_counts]
    counts = counts[1:-1]  # first day jumps and last day is incomplete so throw them out
    if days:
        counts = counts[-days:]
    if counts:
        return statistics.mean(counts)


app.run(host='0.0.0.0', debug=True)
