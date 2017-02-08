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
    return flask.render_template(
        'user.html',
        follow_day_counts=[(day.timestamp(), count) for day, count in follow_day_counts],
        unfollow_day_counts=[(day.timestamp(), count) for day, count in unfollow_day_counts]
    )


app.run(host='0.0.0.0', debug=True)
