#!/usr/bin/env python3
import sys

from markov import MarkovModel

def err_msg():
    print("Usage: {} <sqlite3 file> <text file>: add text file to markov chain\n       {} <sqlite3 file> delete: delete markov db\n       {} <sqlite3 file> get s/p: get random sentence/paragraph".format(sys.argv[0], sys.argv[0], sys.argv[0]))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mm = MarkovModel(sys.argv[1])
        if len(sys.argv) == 3 and sys.argv[2] == "delete":
            mm.delete_table()
        elif len(sys.argv) == 4 and sys.argv[2] == "get":
            if sys.argv[3] == "p":
                print(mm.get_random_paragraph())
            elif sys.argv[3] == "s":
                print(mm.get_random_sentence())
        elif len(sys.argv) == 3:
            with open(sys.argv[2]) as f:
                for l in f.readlines():
                    mm.add_text(l.replace("\r\n"," ").replace("\n"," "))
        else:
            err_msg()
    else:
        err_msg()
