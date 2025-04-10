import os, csv
from flask import Flask, redirect, render_template, request, flash, url_for
from App.models import *
from datetime import timedelta

from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
    current_user,
    set_access_cookies,
    unset_jwt_cookies,
    current_user,
)


def create_app():
    app = Flask(__name__, static_url_path='/static')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'data.db')
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'MySecretKey'
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
    app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token'
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["JWT_SECRET_KEY"] = "super-secret"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

    app.app_context().push()
    return app


app = create_app()
db.init_app(app)

jwt = JWTManager(app)


@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.get(identity)


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    flash("Your session has expired. Please log in again.")
    return redirect(url_for('login'))


def initialize_db():
    db.drop_all()
    db.create_all()
    bob = User('bob', 'bobpass')
    db.session.add(bob)

    rap = Genre(name="Rap")
    reggae = Genre(name="Reggae")
    rnb = Genre(name= "Alternative R&B")
    db.session.add_all([rap, reggae,rnb])
    db.session.commit()

    track1 = Track(title="Nonestop", artist="Drake", album="Scorpian", genre_id=rap.id)
    track2 = Track(title="Redemption Song", artist="Bob Marley", album="Uprising", genre_id=reggae.id)
    track3 = Track(title="DNA", artist="Kendrick", album="Damn", genre_id=rap.id)
    track4 = Track(title="Blinding lights", artist="The Weeknd", album="After Hours", genre_id=rnb.id)
    db.session.add_all([track1, track2, track3, track4])
    db.session.commit()

    print("Database initialized")

@app.route('/')
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_action():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        response = redirect(url_for('home'))
        access_token = create_access_token(identity=user.id)
        set_access_cookies(response, access_token)
        return response
    else:
        flash('Invalid username or password')
        return redirect(url_for('login'))


@app.route('/app')
@jwt_required()
def home():
    genre_filter = request.args.get('genre', 'all')
    genres = Genre.query.all()
    genre_list = [g.name for g in genres]

    if genre_filter == 'all':
        tracks = Track.query.all()
    else:
        genre = Genre.query.filter_by(name=genre_filter).first()
        tracks = genre.tracks if genre else []

    queue_ids = [q.track_id for q in QueueEntry.query.filter_by(user_id=current_user.id)]
    queue = Track.query.filter(Track.id.in_(queue_ids)).all()

    return render_template(
        'index.html',
        user=current_user,
        tracks=tracks,
        genre_list=genre_list,
        selected_genre=genre_filter,
        queue=queue
    )

@app.route('/add', methods=['POST'])
@jwt_required()
def add_track():
    track_id = request.form.get('track_id')
    existing = QueueEntry.query.filter_by(track_id=track_id, user_id=current_user.id).first()
    if not existing:
        entry = QueueEntry(track_id=track_id, user_id=current_user.id)
        db.session.add(entry)
        db.session.commit()
        flash("Track added to queue.")
    else:
        flash("Track is already in queue.")
    return redirect(url_for('home'))

@app.route('/remove/<int:track_id>')
@jwt_required()
def remove_track(track_id):
    entry = QueueEntry.query.filter_by(track_id=track_id, user_id=current_user.id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
        flash("Track removed from queue.")
    else:
        flash("Track not found in queue.")
    return redirect(url_for('home'))

@app.route('/logout')
@jwt_required()
def logout():
    response = redirect(url_for('login'))
    unset_jwt_cookies(response)
    flash('logged out')
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
