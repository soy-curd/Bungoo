#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import urllib
import MeCab
import random
import re


def main():
    print(makeword("ここはどこだ"))
    src = textdownload("http://www.aozora.gr.jp/cards/000119/files/624_14544.html")
    genword(src)
    wordlist = wakati(src)
    markov1 = genmarkov1(wordlist)
    markov2 = genmarkov2(wordlist)
    markov3 = genmarkov3(wordlist)

    txt = "この日、ついに私は到着した。ここはどこだ。"
    while True:
        print(txt)
        sys.stdout.write(">>")
        inp = raw_input()
        if inp == 'q':
            break

        txt = txt + inp

        # 自分の文章を候補に加える
        # wordlist = wordlist + wakati(inp)
        # markov1 = genmarkov1(wordlist)
        # markov2 = genmarkov2(wordlist)
        # markov3 = genmarkov3(wordlist)

        ret = wordchain(wakati(txt), [markov3, markov2, markov1])
        pp(ret)

def download():
    src = reduce(lambda a, x: a + x,
                 map(textdownload, [
                     "http://www.aozora.gr.jp/cards/000119/files/624_14544.html",
                     "http://www.aozora.gr.jp/cards/000160/files/880_23797.html",
                     "http://www.aozora.gr.jp/cards/000160/files/2638_23933.html",
                     ]))
    f = open("txt.txt", "w")
    f.write(src)


def makeword(inp):
    f = open("txt.txt")
    src = f.read()
    print(src)
    wordlist = wakati(src)
    markov1 = genmarkov1(wordlist)
    markov2 = genmarkov2(wordlist)
    markov3 = genmarkov3(wordlist)

    return wordchain(wakati(inp), [markov3, markov2, markov1])


def wordchain(wakatxt, markovs, limit_= 3):
    nextwords = gennextword(wakatxt, markovs, limit=5)
    words = list(set(nextwords))

    # 言葉を連結していく
    for i in range(limit_):
        buf = [cat([word] + list(gennextword(wakatxt + [word], markovs, limit=1))) for word in words]
        words = buf

    # なぜか連結されない？
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


def genword(txt):
    wordlist = wakati(txt)
    markov = genmarkov3(wordlist)
    # カウント数は任意
    count = 300
    sentence =''
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
    w1=''
    w2=''
    for word in wordlist:
        if w1 and w2:
            if (w1,w2) not in markov:
                markov[(w1,w2)] = []
            markov[(w1,w2)].append(word)
        w1,w2=w2,word
    return markov


def genmarkov3(wordlist):
    markov = {}
    w1=''
    w2=''
    w3=''
    for word in wordlist:
        if w1 and w2 and w3:
            if (w1,w2,w3) not in markov:
                markov[(w1,w2,w3)] = []
            markov[(w1,w2,w3)].append(word)
        w1,w2,w3=w2,w3,word
    return markov


def textdownload(sourceURL):
    res = urllib.urlopen(sourceURL)
    downloaded_text = res.read()

    # 文字コード変換
    downloaded_text = unicode(downloaded_text,'shift_jis')
    downloaded_text = re.sub("\n","", downloaded_text)

    # 本文
    downloaded_text = re.search('<div class="main_text">.+?</div>',downloaded_text).group()

    # ルビ削除
    downloaded_text = re.sub(u'（</rp>.+?<rp>）',"", downloaded_text)

    # タグ削除
    downloaded_text = re.sub('<.+?>',"", downloaded_text)
    
    # str形式で出力
    return str(downloaded_text)


def wakati(text):
    t = MeCab.Tagger("-Owakati")
    m = t.parse(text)
    result = m.rstrip(" \n").split(" ")
    return result


def pp(foo):
    if type(foo) == list or type(foo) == tuple or type(foo) == dict:
        for x in foo:
            pp(x)
    else:
        print(foo)

if __name__ == '__main__':
    main()

