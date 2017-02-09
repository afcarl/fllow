import flask

import database

app = flask.Flask(__name__)
db = database.connect()

@app.route('/users')
def users():
    with db, db.cursor() as cursor:
        users = database.get_users(cursor)
    return flask.render_template('users.html', users=users)

@app.route('/users/<screen_name>')
def user(screen_name):
    with db, db.cursor() as cursor:
        user = database.get_user(cursor, screen_name)
        follow_day_counts = database.get_user_follow_day_counts(cursor, user.id)
        unfollow_day_counts = database.get_user_unfollow_day_counts(cursor, user.id)
        follower_day_counts = database.get_twitter_follower_day_counts(cursor, user.twitter_id)
    return flask.render_template(
        'user.html',
        follow_day_counts=as_timestamps(follow_day_counts),
        unfollow_day_counts=as_timestamps(unfollow_day_counts),
        follower_day_counts=as_timestamps(follower_day_counts)
    )

def as_timestamps(day_counts):
    return [(day.timestamp(), count) for day, count in day_counts]

app.run(host='0.0.0.0', debug=True)
