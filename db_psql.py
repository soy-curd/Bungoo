#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

database_url = os.environ['DATABASE_URL']
app = Flask("bungoo")
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
db = SQLAlchemy(app)

class Novel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text())
    link = db.Column(db.Text())
    author = db.Column(db.Text())
    body = db.Column(db.Text())
    markov1 = db.Column(db.PickleType())
    markov2 = db.Column(db.PickleType())
    markov3 = db.Column(db.PickleType())

    __tablename__ = 'novel'

    def __init__(self, title, link, author, body, markov1, markov2, markov3):
        self.title = title
        self.link = link
        self.author = author
        self.body = body
        self.markov1 = markov1
        self.markov2 = markov2
        self.markov3 = markov3

    def __repr__(self):
        return '<Novel %r>' % self.title


def main():
    # insert_data(Novel(
    #     title="hogeeeee",
    #     link="ほうげ",
    #     author="ほな",
    #     body="ほう",
    #     markov1=pickle.dumps({(1, 2): 23}),
    #     markov2=pickle.dumps("ほんあ"),
    #     markov3=pickle.dumps("ほ")
    # ))

    objs = read_data()
    for x in objs:
        print(x)


def insert_data(novel):
    try:
        db.create_all()
        db.session.add(novel)
        db.session.commit()
    except:
        print("the object {0} already exists".format(novel.title))


def read_data():
    novels = Novel.query.all()
    return novels

if __name__ == '__main__':
    main()
