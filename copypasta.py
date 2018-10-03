from collections import Counter
import random
import re

import images
from markov import MarkovModel

PASTA_MM = MarkovModel("data/copypasta.sqlite3")
MEAN_WORDS_PER_PARAGRAPH = 50
STDEV_WORDS_PER_PARAGRAPH = 20
with open("data/mostcommonwords.txt") as f:
    COMMON_WORDS = [l.strip().lower() for l in f]

def generate_copypasta(short=False):
    wordmin = discrete_normal(
        mu=MEAN_WORDS_PER_PARAGRAPH - (45 if short else 0),
        sigma=STDEV_WORDS_PER_PARAGRAPH - (10 if short else 0),
        minimum=1
    )
    return PASTA_MM.get_random_paragraph_min(wordmin)

# Gets n most common words from text, barring most common words in English.
def get_most_common_words(text, n):
    words = [word.lower() for word in re.findall(r"[A-Za-z'\*\-]+", text)
        if word.lower() not in COMMON_WORDS and '*' not in word]
    ctr = Counter(words)
    return [w for w,_ in ctr.most_common(n)]

def discrete_normal(mu, sigma, minimum=-float('inf')):
    retval = round(random.gauss(mu,sigma))
    return minimum if minimum > retval else retval

# FOR TESTING ONLY
if __name__ == "__main__":
    i = 1
    while True:
        inpt = input("1 for text, 2 for text+image: ")
        if inpt == '2':
            pasta = generate_copypasta(short=True)
            print(pasta)
            words = get_most_common_words(pasta,3)
            print(words)
            imgs = images.get_google_images(' '.join(words))
            # images.get_image_from_url(random.choice(images)[0]).show()
            meem = images.create_text_with_image_meme(pasta, random.choice(imgs)[0])
            if meem:
                meem.show()
                meem.save("testmeem_" + str(i) + ".png")
        elif inpt == '1':
            pasta = generate_copypasta(short=False)
            print(pasta)
            meem = images.create_text_meme(pasta)
            meem.show()
            meem.save("testmeem_" + str(i) + ".png")
        i += 1