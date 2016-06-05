#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import urllib.request
from urllib.parse import quote
import re
from bs4 import BeautifulSoup
import MeCab
from pymongo import MongoClient
import pickle
import os


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


def make_sentence():
    stop_words = ["。"]

    mongo_client = MongoClient("localhost:27017")
    db_connect = mongo_client["novel"]
    c = db_connect.novel
    cursor = c.find()
    novels = (novel for novel in cursor)
    contents = ((novel["_id"], novel["wakati_text"]) for novel in novels)

    # "。"で区切る
    for _id, words in contents:
        sentences = []
        sentence = []
        for word in words:
            if word in stop_words:
                sentences.append(sentence)
                sentence = []
            else:
                sentence.append(word)

        c.update({"_id": _id}, {"$set": {"sentences": sentences}})


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


def save_data():
    # MongoDB接続
    mongo_client = MongoClient("localhost:27017")
    # データベース選択
    db_connect = mongo_client["bungoo"]

    kakuyomu = Kakuyomu()
    data_name = "data.dat"
    if not os.path.exists(data_name):
        novels = kakuyomu.get_novel()
        dump_data(novels, data_name)
    else:
        novels = load_data(data_name)

    # データ挿入
    db_connect.drop_collection("bungoo")
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


def main():
    # 異世界ファンタジーラノベをダウンロード
    # 太宰治をダウンロード
    # 文章を生成
    save_data()


def cutup():
    raise NotImplementedError()


def foldin():
    raise NotImplementedError()


if __name__ == "__main__":
    main()
