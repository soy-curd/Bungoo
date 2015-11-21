#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
import os.path
from bungoo import textdownload, wakati_sub, genmarkov1, genmarkov2, genmarkov3

import db_psql
import pickle

class NovelLink(object):
    def __init__(self, title, link):
        self.title = title
        self.link = link
        self.download_link = None
        
    def set(self, download_link):
        self.download_link = download_link


def main():
    make_obj()


def make_obj():
    urls = read_url_from_txt('dazai.txt')
    print(len(urls))
    for url in urls:

        # テキストのダウンロード
        text = textdownload(url)

        # 値の作成
        wordlist = wakati_sub(text[2].replace("　", ""))
        markov1 = genmarkov1(wordlist)
        markov2 = genmarkov2(wordlist)
        markov3 = genmarkov3(wordlist)

        obj = db_psql.Novel(
            title=text[0],
            link=url,
            author=text[1],
            body=text[2],
            markov1=pickle.dumps(markov1),
            markov2=pickle.dumps(markov2),
            markov3=pickle.dumps(markov3)
        )

        # dbにインポート
        db_psql.insert_data(obj)

        # クローリングのため一応sleep
        print(text[0])
        time.sleep(1)

    # dbから値の読み出し
    objs = db_psql.read_data()
    return objs


def read_url_from_txt(filename):
    with open(filename, 'r') as f:
        lines = list(map(lambda x: x.rstrip(), f))

    return lines


def download_dazai():
    url = 'http://www.aozora.gr.jp/index_pages/person35.html'
    hostname = 'http://www.aozora.gr.jp'

    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html)

    all_al = soup.find_all('ol')
    novel_links = all_al[0]

    novels = []
    for x in novel_links.find_all('li'):

        link = x.a['href']
        title = x.text
        novels.append(NovelLink(title, link))

    for novel in novels:
        url = hostname + novel.link[2:]
        html = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(html)

        download_table = soup.find('table', {'class': 'download'})
        units = download_table.find_all('tr', {'bgcolor': 'white'})
        for unit in units:
            link = unit.find('a')['href']
            _, ext = os.path.splitext(link)
            print(unit, link, _, ext)
            if ext == '.html':
                novel.set(urljoin(url, link))
                break

        # クローリングのため一応スリープ
        time.sleep(0.5)

    with open('dazai.txt', 'w') as f:
        for x in novels:
            if x.download_link:
                f.write(x.download_link + '\n')

if __name__=='__main__':
    main()
