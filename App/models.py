from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  password = db.Column(db.String(120), nullable=False)

  queue = db.relationship('QueueEntry', backref='user', lazy=True)

  def __init__(self, username, password):
    self.username = username
    self.set_password(password)

  def set_password(self, password):
    self.password = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password, password)


class Genre(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(50), nullable=False, unique=True)


class Track(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(100), nullable=False)
  artist = db.Column(db.String(100), nullable=False)
  album = db.Column(db.String(100), nullable=False)
  genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), nullable=False)

  genre = db.relationship('Genre', backref='tracks')


class QueueEntry(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)
