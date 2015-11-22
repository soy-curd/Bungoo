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
    author_name = "芥川龍之介"
    # novels = db_psql.read_novel(author_name)
    # for x in novels:
    #     print(x)
    #     print(x.author)
    db_psql.remove_tag("太宰治")


def fix_author():
    pre_author = """<h2 class="author">太宰治</h2>"""
    post_author = "太宰治"
    db_psql.update_data(pre_author, post_author)


def make_obj(filename):
    urls = read_url_from_txt(filename)
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
    filename = 'dazai.txt'
    download_novel(url, filename)

def download_akutagawa():
    url = 'http://www.aozora.gr.jp/index_pages/person879.html'
    filename = 'akutagawa.txt'
    download_novel(url, filename)
    return filename

def download_novel(url, filename):
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

    with open(filename, 'w') as f:
        for x in novels:
            if x.download_link:
                f.write(x.download_link + '\n')

if __name__=='__main__':
    main()
