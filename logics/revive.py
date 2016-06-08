from logics.collect_data import collect_data, WordType, dump_data, load_data
from typing import Sequence, Any
from pymongo import MongoClient
import re
import functools
import random
import os
import copy


def get_sentences(words: Sequence[WordType]):
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


def concat(sentence: Sequence[Any], func=lambda x: x, init=""):
    return functools.reduce(lambda a, x: a + func(x), sentence, init)


def replace(target, words):
    return [random.choice(words) if "名詞" in word["word_types"] else word for word in target]


def make_word(words):
    markov1 = gen_markov1(words)

    return markov1


def gen_markov1(words: Sequence[str]):
    words = [word for word in words if word != "\r" and word != "\u3000"]
    markov = {}
    w1 = None
    for word in words:
        if w1:
            if (w1,) not in markov:
                markov[(w1,)] = []
            markov[(w1,)].append(word)
        w1 = word
    return markov


def gen_markov2(words: Sequence[str]):
    words = [word for word in words if word != "\r" and word != "\u3000"]
    markov = {}
    w1 = None
    w2 = None
    for word in words:
        if w1 and w2:
            if (w1, w2) not in markov:
                markov[(w1, w2)] = []
            markov[(w1, w2)].append(word)
        w1, w2 = w2, word
    return markov


def gen_dict(words: Sequence[WordType]):
    return {word["surface"]: word["word_types"] for word in words}


def replace_by_nown(target, word_dict):
    ret = []
    nown_words = [word for word in word_dict.keys() if "名詞" in word_dict[word]]

    for word in target:
        if "名詞" in word["word_types"]:
            ret.append(random.choice(nown_words))
        ret.append(word["surface"])

    return concat(ret)


def replace_by_markov(target, word_dict, markov1, markov2):
    ret = []
    pre_word = ""
    pre_pre_word = ""

    for word in target:
        print(ret)
        print(word["surface"], word["word_types"][0])
        if "名詞" == word["word_types"][0]:
            # markov辞書の単語は重複しているため、
            # ランダムに抽出するだけで重みが表現される

            if (pre_pre_word, pre_word) in markov2.keys():
                markov_words = [_word for _word in markov2[(pre_pre_word, pre_word)]
                                if _word in word_dict.keys()
                                and word_dict[_word][0] == "名詞"
                                and _word != "\r"
                                ]

                if markov_words:
                    markov_word = random.choice(markov_words)
                    ret.append(markov_word)
                    print(2, markov_word, markov_words)
                    pre_pre_word = pre_word
                    pre_word = word["surface"]
                    continue

            if (pre_word,) in markov1.keys():
                markov_words = [_word for _word in markov1[(pre_word,)]
                                if _word in word_dict.keys()
                                and word_dict[_word][0] == "名詞"
                                and _word != "\r"
                                ]
                if markov_words:
                    markov_word = random.choice(markov_words)
                    ret.append(markov_word)
                    print(1, markov_word, markov_words)
                    pre_pre_word = pre_word
                    pre_word = word["surface"]
                    continue

        ret.append(word["surface"])
        pre_pre_word = pre_word
        pre_word = word["surface"]

    return concat(ret)


def cutup():
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
    dazai_markov = gen_markov1([word["surface"] for word in novel["wakati_text"]])
    dazai_markov2 = gen_markov2([word["surface"] for word in novel["wakati_text"]])
    buf = [(i, _s) for i, _s in enumerate(_sentences) if "恥" in _s]
    target = concat(sentences[47:53], init=[])
    target = [word for word in target[4:] if word["surface"] != "\r"]
    random_target = copy.deepcopy(target)
    random.shuffle(random_target)
    random_dazai = concat([word["surface"] for word in random_target]).replace("\r", "").replace("\u3000", "")

    # カクヨム
    novels = c.find({"url": re.compile(r"kakuyomu")})
    file_name = "new_words.dat"
    if os.path.exists(file_name):
        new_words = load_data(file_name)
    else:
        new_words = concat([novel["wakati_text"] for novel in novels], init=[])
        dump_data(new_words, file_name)
    print(len(new_words))

    # 名詞抽出
    file_name = "new_noun.dat"
    if os.path.exists(file_name):
        new_noun = load_data(file_name)
    else:
        new_noun = [word for word in new_words if "名詞" in word["word_types"]]
        dump_data(new_noun, file_name)
    print(len(new_noun))
    ret = replace(target, new_noun)
    print(concat(ret, lambda x: x["surface"]))

    file_name = "markov.dat"
    if os.path.exists(file_name):
        markov = load_data(file_name)
    else:
        markov = gen_markov1([word["surface"] for word in new_words])
        dump_data(markov, file_name)

    file_name = "markov2.dat"
    if os.path.exists(file_name):
        markov2 = load_data(file_name)
    else:
        markov2 = gen_markov2([word["surface"] for word in new_words])
        dump_data(markov2, file_name)

    file_name = "dictionary.dat"
    if os.path.exists(file_name):
        dictionary = load_data(file_name)
    else:
        dictionary = gen_dict(new_words)
        dump_data(dictionary, file_name)

    dictionary = load_data("dictionary.dat")
    dazai_dict = gen_dict(novel["wakati_text"])
    ret = replace_by_nown(target, dazai_dict).replace("\r", "").replace("\u3000", "")
    print(ret)

    ret = replace_by_markov(target[:100], dazai_dict, dazai_markov, dazai_markov2)
    print(ret)

    ret = replace_by_markov(target, dictionary, markov, markov2)
    print(ret)


def main(save=False):
    # 異世界ファンタジーラノベをダウンロード
    # 太宰治をダウンロード
    if save:
        collect_data()

    cutup()


if __name__ == "__main__":
    main()
