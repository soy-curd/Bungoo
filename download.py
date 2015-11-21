#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
import os.path

class Novel():
    def __init__(self, title, link):
        self.title = title
        self.link = link
        self.download_link = None
        
    def set(self, download_link):
        self.download_link = download_link


def main():
    make_binary()


def make_binary():
    urls = read_url_from_txt('dazai.txt')
    for x in urls:
        print(x)


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
        novels.append(Novel(title, link))

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
            # import pdb
            # pdb.set_trace()
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
