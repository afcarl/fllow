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
        follow_times = database.get_user_follow_times(cursor, user.id)
        unfollow_times = database.get_user_unfollow_times(cursor, user.id)
    return flask.render_template(
        'user.html',
        followed=[t.timestamp() for t in follow_times],
        unfollowed=[t.timestamp() for t in unfollow_times]
    )


app.run(host='0.0.0.0', debug=True)
