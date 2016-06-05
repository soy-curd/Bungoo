from logics.collect_data import collect_data, WordType, dump_data, load_data
from pymongo import MongoClient
import re
import functools
import random
import os


def get_sentences(words):
    stop_words = ["。"]

    # "。"で区切る
    sentences = []
    sentence = []
    for word in words:
        if word["surface"] in stop_words:
            if sentence:
                sentences.append(sentence + [word])
                sentence = []
        else:
            sentence.append(word)

    return sentences


def main(save=False):
    # 異世界ファンタジーラノベをダウンロード
    # 太宰治をダウンロード
    if save:
        collect_data()

    # 文章を生成
    # MongoDB接続
    mongo_client = MongoClient("localhost:27017")
    # データベース選択
    db_connect = mongo_client["bungoo"]

    c = db_connect.bungoo

    # 太宰
    novel = c.find_one({"title": re.compile(r"人間失格")})
    sentences = get_sentences(novel["wakati_text"])
    _sentences = [concat(sentence, lambda x: x["surface"]) for sentence in sentences]
    buf = [(i, _s) for i, _s in enumerate(_sentences) if "恥" in _s]
    target = concat(sentences[47:53], init=[])
    print(sentences)

    # カクヨム
    novels = c.find({"url": re.compile(r"kakuyomu")})
    file_name = "new_words.dat"
    if os.path.exists(file_name):
        new_words = load_data(file_name)
    else:
        new_words = concat([novel["wakati_text"] for novel in novels], init=[])
        dump_data(new_words, file_name)

    print(len(new_words))
    ret = replace(target, new_words)
    print(concat(ret, lambda x: x["surface"]))


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
