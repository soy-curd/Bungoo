#!/usr/bin/env python
# -*- coding: utf-8 -*-

#todo 高速化する
#todo スタート時に落ちるため直す
#todo 全自動ボタン

import sys

# setdefaultencodingするためにはrelodが必要
reload(sys)
sys.setdefaultencoding('utf-8')

import urllib
import random
import re
import db

def main():
    download()
    src = read()

    txt = "この文章はここからはじまる。"
    while True:
        print(txt)
        sys.stdout.write(">>")
        inp = raw_input()
        if inp == 'q':
            break

        txt = txt + inp

        ret = makeword(txt, src)
        pp(ret)


def auto():
    words=[u"私は",u"彼に",u"あなたを",u"僕が",u"今日、",u"いつか",u"その日",u"ある日",u"昔"]
    auto_txt = random.choice(words)
    MAX_TEXTSIZE = 500

    while(len(auto_txt) < MAX_TEXTSIZE):
        src = read()
        words = makeword(str(auto_txt), src)

        if len(words) == 0:
            break

        auto_txt = auto_txt + random.choice(words)

        # 最後が句点の場合終了
        if auto_txt[-1] == u"。":
            break

    return auto_txt

# メモ化関数
def memoize(func):
    cache = {}

    def memoized_function(*args):
        try:
            return cache[args]
        except KeyError:
            value = func(*args)
            cache[args] = value
            return value
    return memoized_function


# 時間計測関数
def time(func):
    import functools
    import datetime
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = datetime.datetime.today()
        result = func(*args, **kwargs)
        end = datetime.datetime.today()
        print(func.__name__, end - start)
        return result
    return wrapper


def download():
    link1 = "http://www.aozora.gr.jp/cards/000119/files/624_14544.html"
    link2 = "http://www.aozora.gr.jp/cards/000160/files/880_23797.html"
    link3 = "http://www.aozora.gr.jp/cards/000160/files/2638_23933.html"

    srcs = map(lambda x: textdownload(x) + [x], [
         link1,
         link2,
         link3,
         ])

    db.make_table()
    for x in srcs:
        db.insert_data(*x)


@memoize
def read():
    srcs = db.read_data()
    return reduce(lambda a, x: a + str(x[2]), srcs, "")


def makeword(inp, src):
    wordlist = wakati_multi(src)
    markov1 = genmarkov1(wordlist)
    markov2 = genmarkov2(wordlist)

    return wordchain(wakati(inp), [markov2, markov1])


@time
def wordchain(wakatxt, markovs, limit_= 3):
    nextwords = gennextword(wakatxt, markovs, limit=5)
    words = list(set(nextwords))

    # 言葉を連結していく
    for i in range(limit_):
        buf = [cat([word] + list(gennextword(wakatxt + [word], markovs, limit=1))) for word in words]
        words = buf

    for i in range(limit_):
        buf = []
        for word in words:
            txxx = wakatxt + [word]
            a = gennextword(txxx, markovs, limit=2)
            b = list(a)
            newword = [word] + b
            buf.append(cat(newword))

        words = buf

    return words


def cat(strlist):
    return reduce(lambda a, x: a + x, strlist)


def gennextword(txt, markovs, limit=3):
    # 単語の後ろから探索
    cnt = 0
    for markov in markovs:
        i = len(markov.keys()[0])
        suggest = markov.get(tuple(txt[-i:]))
        if suggest:
            for x in suggest:
                yield x
                cnt += 1
                if cnt == limit:
                    raise StopIteration


def genword(txt, count=300):
    wordlist = wakati(txt)
    markov = genmarkov3(wordlist)
    sentence = ''
    w1, w2, w3 = random.choice(markov.keys())
    for i in xrange(count):
        if markov.has_key((w1, w2, w3)) == True:
            tmp = random.choice(markov[(w1, w2, w3)])
            sentence += tmp
        w1, w2, w3 = w2, w3, tmp

    print(sentence)
    print(len(sentence))


def genmarkov1(wordlist):
    markov = {}
    w1=''
    for word in wordlist:
        if w1:
            if (w1,) not in markov:
                markov[(w1,)] = []
            markov[(w1,)].append(word)
        w1 = word
    return markov


def genmarkov2(wordlist):
    markov = {}
    w1 = ''
    w2 = ''
    for word in wordlist:
        if w1 and w2:
            if (w1, w2) not in markov:
                markov[(w1, w2)] = []
            markov[(w1, w2)].append(word)
        w1, w2 = w2, word
    return markov


@time
def genmarkov3(wordlist):
    markov = {}
    w1 = ''
    w2 = ''
    w3 = ''
    for word in wordlist:
        if w1 and w2 and w3:
            if (w1, w2, w3) not in markov:
                markov[(w1, w2, w3)] = []
            markov[(w1, w2, w3)].append(word)
        w1, w2, w3 = w2, w3, word
    return markov


def textdownload(sourceURL):
    res = urllib.urlopen(sourceURL)
    downloaded_text = res.read()

    # 文字コード変換
    downloaded_text = unicode(downloaded_text,'shift_jis')

    # タイトル
    title = re.search('<h1 class="title">.+?</h1>', downloaded_text).group()

    # 作者
    author = re.search('<h2 class="author">.+?</h2>', downloaded_text).group()

    # 改行削除
    downloaded_text = re.sub("\n", "", downloaded_text)

    # 本文
    body = re.search('<div class="main_text">.+?</div>', downloaded_text).group()

    # ルビ削除
    body = re.sub(u'（</rp>.+?<rp>）', "", body)

    # タグ削除
    body = re.sub('<.+?>', "", body)

    # str形式で出力
    return map(str, [title, author, body])


@memoize
def wakati(text):
    import igo

    print(u"text size: ", len(text))
    text = unicode(text)

    t = igo.Tagger.Tagger('ipadic')

    return t.wakati(text)


# 分かち書き関数
# 別関数にすることでmultiprocessingのPicklingErrorを回避
def wakati_sub(text):
    import igo

    t = igo.Tagger.Tagger('ipadic')

    return t.wakati(text)


def split_list(xlist, num):
    splited_list = []
    for x in range(num):
        buf = xlist[(x - 1) * len(xlist)/num : x * len(xlist)/num]
        splited_list.append(buf)

    return splited_list


@memoize
def wakati_multi(text, process=4):
    from multiprocessing import Pool

    print(u"text size: ", len(text))
    p = Pool(process)
    text = unicode(text)
    splited_text = split_list(text, process)
    print(len(splited_text))

    return cat(p.map(wakati_sub, splited_text))


def pp(foo):
    if type(foo) == list or type(foo) == tuple or type(foo) == dict:
        for x in foo:
            pp(x)
    else:
        print(foo)


if __name__ == '__main__':
    main()

