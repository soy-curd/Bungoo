#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import bungoo


def main():
    make_table()
    insert_data("test", "foo", "foo", "foo, foo, foo.")

    for x in read_data():
        bungoo.pp(x)


def make_table():
    con = sqlite3.connect("data.db")
    sql = """
    create table novel (
        title TEXT UNIQUE,
        link TEXT,
        author TEXT,
        body TEXT
    );
    """

    try:
        con.execute(sql)

    # 既にテーブルがあったらpass
    except sqlite3.OperationalError:
        print("SQL table has been existed.")

    con.close()


def insert_data(title, author, body, link):
    con = sqlite3.connect("data.db")
    sql = "insert or replace into novel values ('" + title + "', '" + author + "', '" + body + "', '" + link + "')"
    con.execute(sql)
    con.commit()
    con.close()


def read_data():
    con = sqlite3.connect("data.db")
    c = con.cursor()
    c.execute("select * from novel")
    data = [x for x in c.fetchall()]
    con.close()

    return data


if __name__ == '__main__':
    main()
