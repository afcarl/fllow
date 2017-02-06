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
        followed_times = database.get_user_followed_times(cursor, user.id)
        unfollowed_times = database.get_user_unfollowed_times(cursor, user.id)
    return flask.render_template(
        'user.html',
        followed=[t.timestamp() for t in followed_times],
        unfollowed=[t.timestamp() for t in unfollowed_times]
    )


app.run(host='0.0.0.0', debug=True)
