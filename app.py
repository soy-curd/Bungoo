#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import url_for, render_template, request, redirect
import bungoo
from functools import reduce
import db_psql

app = db_psql.app

MARKOVS = bungoo.make_markovs(db_psql.read_data())

@app.route('/')
def root():
    return redirect(url_for('start'))


@app.route('/Bungoo/')
@app.route('/Bungoo/<text>')
def start(text=None):
    if not text:
        text = ">>"

    bungoo.download()
    return render_template('hello.html', text=text)

@app.route('/Bungoo/auto')
def auto_write():
    text = bungoo.auto(MARKOVS)
    return render_template('hello.html', text=text)

@app.route('/Bungoo/', methods=['POST'])
def text_proc():

    txt = request.form['input_text'].replace('\n', '').replace('\r', '')
    print(txt)
    words = bungoo.makeword_from_obj(txt, MARKOVS)
    if len(words) > 0:
        html_words = add_p(words)
    else:
        html_words = "<p>no suggestion</p>"

    return render_template('hello.html', text=txt, snipet=html_words)

# pタグを追加する
def add_p(word_list):
    ptext = ['<p>' + str(word) + '</p>' for word in word_list]
    return reduce(lambda a, x: a + x, ptext).replace('\n', '').replace('\r', '')

if __name__ == '__main__':
    app.run(port=5001, debug=True)
