import click, csv
from flask import Flask
from App import app, initialize_db


@app.cli.command("init")
def initialize():
  initialize_db()
