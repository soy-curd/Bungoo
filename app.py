#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, url_for, render_template, request
import bungoo

app = Flask(__name__)


@app.route('/')
def hello_world():
    return "Hello World!"


@app.route('/Bungoo/')
@app.route('/Bungoo/<text>')
def hello(text=None):
    if not text:
        text = ">>ここに文章を入力してください。"

    bungoo.download()
    return render_template('hello.html', text=text)


@app.route('/Bungoo/', methods=['GET', 'POST'])
def login():
    url_for('static', filename='jquery.balloon.min.js')

    if request.method == 'POST':
        txt = request.form['input_text'].replace('\n', '').replace('\r', '')
        print(txt)
        words = bungoo.makeword(str(txt))
        if len(words) > 0:
            html_words = add_p(words)
        else:
            html_words = "<p>no suggestion</p>"

        return render_template('hello.html', text=txt, snipet=html_words)

    else:
        return render_template('hello.html', text='Please input any text.')


def add_p(word_list):
    ptext = ['<p>' + unicode(word) + '</p>' for word in word_list]
    return reduce(lambda a, x: a + x, ptext)

if __name__ == '__main__':
    app.run(debug=True)