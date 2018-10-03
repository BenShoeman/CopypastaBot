import random
import re

_censor_words = []
_censor_chars = ['*']

# Sets the censor characters based on a list (or string) of characters.
def set_censor_chars(chars_list=['*'], replace=True):
    global _censor_chars
    # Convert to a list if user provides a string
    if type(chars_list) == str:
        chars_list = list(c for c in chars_list)
    # Make sure all of the characters are actual characters, and that we
    # actually have a list
    assert _censor_chars and all(len(c) == 1 for c in chars_list)
    if replace:
        _censor_chars = chars_list
    else:
        _censor_chars += chars_list

# Sets the censor words based on a list of words. None will use the default word
# list from censorlist.txt.
def set_censor_words(word_list=None, replace=False):
    global _censor_words
    if not word_list:
        with open("data/censorlist.txt") as f:
            word_list = [l.strip() for l in f]
    if replace:
        _censor_words = word_list
    else:
        _censor_words += word_list

# Censors the given text using _censor_words.
def censor(text, vowels_only=True):
    # If we have no censor words, load the default list
    if not _censor_words:
        set_censor_words()
    for censor_word in _censor_words:
        text = re.sub(
            re.escape(censor_word),
            _get_censored_word(censor_word, vowels_only),
            text,
            flags=re.IGNORECASE
        )
    return text
    
# Get a censored version of the word inputted, using _censor_chars.
def _get_censored_word(word, vowels_only=True):
    censor = []
    while len(censor) < len(word):
        # Keep on adding shuffled _censor_chars until we're longer than word
        censor += random.sample(_censor_chars, k=len(_censor_chars))
    # Replace censor chars with consonants where applicable
    if vowels_only:
        for i,c in enumerate(word):
            if c not in "AEIOUaeiou":
                censor[i] = c
    return "".join(censor)[:len(word)]

# Load the default list
set_censor_words()