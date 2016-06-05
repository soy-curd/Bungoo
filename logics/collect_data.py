#!/usr/bin/env python
# -*- coding: utf-8 -*-


import urllib
import urllib.request
from urllib.parse import quote, urljoin
import re
from bs4 import BeautifulSoup
import MeCab
from pymongo import MongoClient
import pickle
import os
import time


class WordType(object):
    def __init__(self, surface, word_types, basic, kana):
        self.surface = surface
        self.word_types = word_types
        self.basic = basic
        self.kana = kana


class Novel(object):
    def __init__(self, title, author, body, url, children=[], wakati_text=None, key_words=None):
        self.title = title
        self.author = author
        self.body = body
        self.url = url
        self.children = children
        self.wakati_text = wakati_text
        self.key_words = key_words


class NovelSite(object):
    def download_html(self, source_url):
        res = urllib.request.urlopen(source_url)
        return res.read()

    def get_body_text(self, text, url=None):
        raise NotImplementedError()


class Kakuyomu(NovelSite):
    def __init__(self):
        self.domain = "https://kakuyomu.jp"
        self.search_url = self.domain + "/search?q={0}"
        self.ranking_url = self.domain + "/rankings/{0}/{1}"

    def download_html(self, source_url):
        res = urllib.request.urlopen(source_url)
        return str(res.read(), "utf-8")

    def get_novel(self, ranking="monthly", category="fantasy", search_key=None, limit=10):

        if search_key:
            url = self.search_url.format(quote(search_key))
        elif ranking and category:
            url = self.ranking_url.format(quote(category), quote(ranking))
        else:
            raise ValueError()

        html = self.download_html(url)
        soup = BeautifulSoup(html)
        articles = soup.find_all("div", {"class": "widget-work float-parent"})
        results = []

        for i, article in enumerate(articles):
            title_obj = article.find("a", {"class": "widget-workCard-titleLabel"})
            if not title_obj:
                title_obj = article.find("a", {"class": "widget-work-titleLabel"})
            if not title_obj:
                raise ValueError("title is not found.")
            title = title_obj.string
            url = self.domain + title_obj["href"]

            author_obj = article.find("a", {"class": "widget-workCard-authorLabel"})
            if not author_obj:
                author_obj = article.find("a", {"class": "widget-work-authorLabel"})
            if not author_obj:
                raise ValueError("author is not found.")
            author = author_obj.string

            children = self.get_episodes(url)
            n = Novel(title, author, "", url, children, key_words={ranking: ranking, })
            results.append(n)

            if i == limit:
                break

        return results

    def get_episodes(self, url):
        html = self.download_html(url)
        soup = BeautifulSoup(html)
        episodes = soup.find_all("li", {"class": "widget-toc-episode"})
        results = []
        for episode in episodes:
            _url = self.domain + episode.find("a")["href"]
            _html = self.download_html(_url)
            novel = self.get_body_text(_html, _url)
            results.append(novel)
        return results

    def get_body_text(self, text, url=None):
        soup = BeautifulSoup(text)
        try:
            title = soup.find("p", {"class": "widget-episodeTitle"}).text
        except AttributeError:
            title = ""
        try:
            author = soup.find("p", {"id": "contentMain-header-author"}).text
        except AttributeError:
            author = ""
        try:
            body = soup.find("div", {"class": "widget-episodeBody"}).text
        except AttributeError:
            body = ""
        body = re.sub("<.+?>", "", body)

        novel = Novel(title, author, body, url)
        return novel


class Aozora(NovelSite):
    def __init__(self):
        self.domain = 'http://www.aozora.gr.jp'

    def download_html(self, source_url):
        res = urllib.request.urlopen(source_url)
        return str(res.read(), 'shift-jis')

    def get_novel(self, author_num=35):
        url = 'http://www.aozora.gr.jp/index_pages/person{}.html'.format(author_num)
        return self.download_novel(url)

    def download_novel(self, url, max_cnt=1000):
        hostname = 'http://www.aozora.gr.jp'

        html = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(html)

        all_al = soup.find_all('ol')
        novel_links = all_al[0]

        novels = []
        for cnt, x in enumerate(novel_links.find_all('li')):
            if cnt <= 100:
                continue

            link = x.a['href']
            title = x.text
            novels.append(Novel(title, author="", body="", url=link))
            if cnt == max_cnt:
                break

        for novel in novels:
            url = hostname + novel.url[2:]
            html = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(html)

            download_table = soup.find('table', {'class': 'download'})
            units = download_table.find_all('tr', {'bgcolor': 'white'})
            for unit in units:
                link = unit.find('a')['href']
                _, ext = os.path.splitext(link)
                print(unit, link, _, ext)
                if ext == '.html':
                    novel.url = urljoin(url, link)
                    break

            # クローリングのためスリープ
            print("sleeeeeeep ...")
            time.sleep(5)

        for novel in novels:
            try:
                body = self.download_html(novel.url)
                body, title, author = self.remove_ruby(body)
                novel.body = body
                novel.title = title
                novel.author = author
                novel.key_words = [{"site": "aozora"}]
            except:
                print("download error occurred.")
                print(novel.url)

        return novels

    def remove_ruby(self, text):
        soup = BeautifulSoup(text)
        title = soup.find('h1', {'class': 'title'}).text
        author = soup.find('h2', {'class': 'author'}).text
        body = soup.find('div', {'class': 'main_text'})

        # ここでルビをreplaceする必要がある。
        try:
            while body.ruby:
                body.ruby.replace_with(body.ruby.rb.string)
            while body.br:
                soup.br.decompose()
            while body.strong:
                body.strong.decompose()
        except AttributeError:
            pass

        return body.text, title, author


def wakati(text):
    m = MeCab.Tagger("-Ochasen")
    words = []
    m.parse("")  # GCを走らせないようにするために必要 http://shogo82148.github.io/blog/2015/12/20/mecab-in-python3-final/
    nodes = m.parseToNode(text)
    while nodes:
        surface = nodes.surface
        features = nodes.feature.split(",")
        if len(features) < 9:
            words.append(
                    WordType(surface, [features[0], features[1], features[2], features[3], features[4], features[5]],
                             surface, surface))
        else:
            words.append(
                    WordType(surface, [features[0], features[1], features[2], features[3], features[4], features[5]],
                             features[6], features[7]))
        nodes = nodes.next

    return words


def load_data(filename):
    with open(filename, "rb") as f:
        data = pickle.load(f)
    return data


def dump_data(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def collect_data():
    # MongoDB接続
    mongo_client = MongoClient("localhost:27017")
    # データベース選択
    db_connect = mongo_client["bungoo"]

    kakuyomu = Kakuyomu()
    data_name = "data_kakuyomu.dat"
    if not os.path.exists(data_name):
        kakuyomu_novels = kakuyomu.get_novel()
        dump_data(kakuyomu_novels, data_name)
    else:
        kakuyomu_novels = load_data(data_name)

    aozora = Aozora()
    data_name = "data_aozora.dat"
    if not os.path.exists(data_name):
        aozora_novels = aozora.get_novel()
        dump_data(aozora_novels, data_name)
    else:
        aozora_novels = load_data(data_name)

    novels = aozora_novels + kakuyomu_novels
    #
    # データ挿入
    # db_connect.drop_collection("bungoo")
    for novel in novels:
        ret = db_connect["bungoo"].insert_one({
            "title": novel.title,
            "author": novel.author,
            "body": novel.body,
            "url": novel.url,
            "key_words": novel.key_words
        })

        if novel.children:
            for _novel in novel.children:
                db_connect["bungoo"].insert_one({
                    "title": _novel.title,
                    "author": _novel.author,
                    "body": _novel.body,
                    "url": _novel.url,
                    "key_words": _novel.key_words,
                    "parent_id": str(ret.inserted_id)
                })

    # 分かち書きデータを格納
    c = db_connect.bungoo
    cursor = c.find()
    for novel in cursor:
        print(novel["title"])
        _id = novel["_id"]
        wakati_text = [vars(word) for word in wakati(re.sub("\n", "", novel["body"]))]
        c.update({"_id": _id}, {"$set": {"wakati_text": wakati_text}})


if __name__ == "__main__":
    collect_data()
