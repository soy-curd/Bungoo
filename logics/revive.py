from logics.collect_data import save_data, WordType
from pymongo import MongoClient
import re
import functools
import random


def get_sentences(_id):
    stop_words = ["。"]

    mongo_client = MongoClient('localhost:27017')
    db_connect = mongo_client["bungoo"]
    c = db_connect.bungoo
    novel = c.find_one({"_id": _id})

    # "。"で区切る
    sentences = []
    sentence = []
    for word in novel["wakati_text"]:
        if word["surface"] in stop_words:
            if sentence:
                sentences.append(sentence + [word])
                sentence = []
        else:
            sentence.append(word)

    return sentences


def main(save=False):
    # 異世界ファンタジーラノベをダウンロード -> 済
    # 太宰治をダウンロード
    # 文章を生成
    if save:
        save_data()

    # MongoDB接続
    mongo_client = MongoClient("localhost:27017")
    # データベース選択
    db_connect = mongo_client["bungoo"]

    c = db_connect.bungoo
    novel = c.find_one({"title": re.compile(r"人間失格")})
    sentences = get_sentences(novel["_id"])
    _sentences = [concat(sentence, lambda x: x["surface"]) for sentence in sentences]
    buf = [(i, _s) for i, _s in enumerate(_sentences) if "恥" in _s]
    target = concat(sentences[47:53], init=[])
    print(sentences)
    new_words = [vars(WordType("ナウイ", [], "", "")),
                 vars(WordType("ほげ", [], "", "")),
                 vars(WordType("ふが", [], "", ""))]
    ret = replace(target, new_words)
    print(concat(ret, lambda x: x["surface"]))


    # cursor = c.find()
    # for novel in cursor:
    #     print(novel["title"])
    #     _id = novel["_id"]


def concat(sentence, func=lambda x: x, init=""):
    return functools.reduce(lambda a, x: a + func(x), sentence, init)


def replace(target, words):
    return [random.choice(words) if "名詞" in word["word_types"] else word for word in target]


def cutup():
    raise NotImplementedError()


def foldin():
    raise NotImplementedError()


if __name__ == "__main__":
    main()
