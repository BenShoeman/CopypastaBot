import random
import re
import sqlite3

import censorer

EXTRA_PUNCT_REGEX = re.compile(r"[\/#$%\^{}=_`~()\"]")
WORD_REGEX = re.compile(r"([A-Za-z0-9\-\']+|[.,!?&;:])")

class MarkovModel:
    def __init__(self, sqldb_filename, fallback_probability=0.2, beginning_word_probability=0.8, censor=True):
        self.sqldb = sqldb_filename
        # fallback_pr is the probability of using the first-order model instead
        # of the second-order. This is partially to prevent infinite loops as
        # well as ensure some degree of randomness.
        self.fallback_pr = fallback_probability
        # begin_word_pr is the probability of a sentence beginning with a word
        # that starts off a sentence rather than one in the middle. This also
        # is to ensure a degree of randomness.
        self.begin_word_pr = beginning_word_probability
        # censor set to True will censor words through the default word list.
        # Defaults to True because I don't wanna get zucced super easily.
        self.censor = censor
        self._make_table()

    def _make_table(self):
        con = sqlite3.connect(self.sqldb)
        try:
            cur = con.cursor()

            # Determine if SQL table exists
            cur.execute("select name from sqlite_master where type='table' and name='edges_first';")
            # ...and then add if it doesn't
            if len(cur.fetchall()) == 0:
                cur.execute("create table edges_first (currword varchar, nextword varchar, instances int);")
                con.commit()
            
            # Do the same for second-order edges
            cur.execute("select name from sqlite_master where type='table' and name='edges_second';")
            if len(cur.fetchall()) == 0:
                cur.execute("create table edges_second (prevword varchar, currword varchar, nextword varchar, instances int);")
                con.commit()

        except sqlite3.OperationalError as e:
            print("Error:", e)
            con.rollback()
        finally:
            con.close()

    def add_text(self, text):
        # Remove unnecessary punctuation
        text = EXTRA_PUNCT_REGEX.sub("", text)
        if text == "":
            return
        text = ". " + text

        words = WORD_REGEX.findall(text)

        con = sqlite3.connect(self.sqldb)

        try:
            cur = con.cursor()

            for i in range(len(words) - 1):
                prevword = words[i-1] if i > 0 else None
                currword = words[i]
                nextword = words[i+1]

                print(currword, end=' ')

                # Escape single quotes properly
                if prevword: prevword = prevword.replace("'","''")
                currword = currword.replace("'","''")
                nextword = nextword.replace("'","''")

                # Try to find this edge
                cur.execute("select * from edges_first where currword='{}' and nextword='{}';".format(currword, nextword))

                # If edge doesn't exist, add it
                if len(cur.fetchall()) == 0:
                    cur.execute("insert into edges_first (currword, nextword, instances) values ('{}', '{}', 1);".format(currword, nextword))
                # Otherwise increment number of instances
                else:
                    cur.execute("update edges_first set instances = instances + 1 where currword='{}' and nextword='{}';".format(currword, nextword))
                
                # Do the same for second-order edges if prevword exists
                if prevword:
                    cur.execute("select * from edges_second where prevword='{}' and currword='{}' and nextword='{}';".format(prevword, currword, nextword))
                    if len(cur.fetchall()) == 0:
                        cur.execute("insert into edges_second (prevword, currword, nextword, instances) values ('{}', '{}', '{}', 1);".format(prevword, currword, nextword))
                    else:
                        cur.execute("update edges_second set instances = instances + 1 where prevword='{}' and currword='{}' and nextword='{}';".format(prevword, currword, nextword))

                if i % 5000 == 4999: con.commit() # Commit every 5000 words

            con.commit()

        except sqlite3.OperationalError as e:
            print("Error:", e)
            con.rollback()
        finally:
            con.close()

    def get_random_string(self, words=30, init_prevword=None):
        con = sqlite3.connect(self.sqldb)

        try:
            cur = con.cursor()

            # Pick random word in words
            prevword = init_prevword
            currword = "."
            while re.search(r"[.,!?;:]", currword): # Make sure it's not a punctuation mark
                if random.random() < self.begin_word_pr:
                    cur.execute("select distinct nextword from edges_first where currword='.' or currword='!' or currword='?';")
                else:
                    cur.execute("select distinct currword from edges_first;")
                currword = random.choice(cur.fetchall())[0]

            currstring = currword

            while currword not in ".!?":
                # If we have a previous word, try to find a connection from previous two words and get all possible next words
                rows = []
                if prevword and random.random() > self.fallback_pr:
                    cur.execute("select nextword, cast(instances as float) / (select sum(instances) from edges_second where prevword='{}' and currword='{}') as probability from edges_second where prevword='{}' and currword='{}';".format(prevword.replace("'","''"), currword.replace("'","''"), prevword.replace("'","''"), currword.replace("'","''")))
                    rows = cur.fetchall()
                if not prevword or len(rows) == 0:
                    # Otherwise get all possible next words from first-order connections
                    cur.execute("select nextword, cast(instances as float) / (select sum(instances) from edges_first where currword='{}') as probability from edges_first where currword='{}';".format(currword.replace("'","''"), currword.replace("'","''")))
                    rows = cur.fetchall()

                # Get next word using probabilities
                p = random.random()
                if len(rows) > 0:
                    for word, pr in rows:
                        if p < pr:
                            prevword = currword
                            currword = word
                            break
                        p -= pr
                else:
                    # Select new random word since we don't have one
                    cur.execute("select distinct currword from edges_first;")
                    prevword = None
                    currword = random.choice(cur.fetchall())[0]

                if not re.search(r"[.,!?;:]", currword):
                    currstring += " "

                # Add next word to string
                currstring += currword

                # Break once we've arrived at the desired number of words
                if len(currstring.split(" ")) == words:
                    break
            
            if self.censor: currstring = censorer.censor(currstring)

        except sqlite3.OperationalError as e:
            print("Error:", e)
            currstring = None
            con.rollback()
        finally:
            con.close()
            return currstring

    def get_random_string_min(self, wordmin=30, init_prevword=None):
        con = sqlite3.connect(self.sqldb)

        try:
            cur = con.cursor()

            # Pick random word in words
            prevword = init_prevword
            currword = "."
            while re.search(r"[.,!?;:]", currword): # Make sure it's not a punctuation mark
                if random.random() < self.begin_word_pr:
                    cur.execute("select distinct nextword from edges_first where currword='.' or currword='!' or currword='?';")
                else:
                    cur.execute("select distinct currword from edges_first;")
                currword = random.choice(cur.fetchall())[0]

            currstring = currword

            while currword not in ".!?":
                # If we have a previous word, try to find a connection from previous two words and get all possible next words
                rows = []
                if prevword and random.random() > self.fallback_pr:
                    cur.execute("select nextword, cast(instances as float) / (select sum(instances) from edges_second where prevword='{}' and currword='{}') as probability from edges_second where prevword='{}' and currword='{}';".format(prevword.replace("'","''"), currword.replace("'","''"), prevword.replace("'","''"), currword.replace("'","''")))
                    rows = cur.fetchall()
                if not prevword or len(rows) == 0:
                    # Otherwise get all possible next words from first-order connections
                    cur.execute("select nextword, cast(instances as float) / (select sum(instances) from edges_first where currword='{}') as probability from edges_first where currword='{}';".format(currword.replace("'","''"), currword.replace("'","''")))
                    rows = cur.fetchall()

                # Get next word using probabilities
                p = random.random()
                if len(rows) > 0:
                    for word, pr in rows:
                        if p < pr:
                            prevword = currword
                            currword = word
                            break
                        p -= pr
                else:
                    # Select new random word since we don't have one
                    cur.execute("select distinct currword from edges_first;")
                    prevword = None
                    currword = random.choice(cur.fetchall())[0]

                if not re.search(r"[.,!?;:]", currword):
                    currstring += " "

                # Add next word to string
                currstring += currword

                # Add another sentence if the description is really short
                if len(currstring.split(" ")) < wordmin and re.search(r"[.!?]", currword):
                    while re.search(r"[.,!?;:]", currword): # Make sure it's not a punctuation mark
                        if random.random() < self.begin_word_pr:
                            cur.execute("select distinct nextword from edges_first where currword='.' or currword='!' or currword='?';")
                        else:
                            cur.execute("select distinct currword from edges_first;")
                        currword = random.choice(cur.fetchall())[0]
                    currstring += " " + currword
            
            if self.censor: currstring = censorer.censor(currstring)

        except sqlite3.OperationalError as e:
            print("Error:", e)
            currstring = None
            con.rollback()
        finally:
            con.close()
            return currstring

    def get_random_sentence(self, capitalize=True, init_prevword=None):
        sentence = self.get_random_string_min(wordmin=1, init_prevword=init_prevword)
        if capitalize: sentence = sentence[0:1].upper() + sentence[1:]
        return sentence

    def get_random_paragraph(self, sentences=5):
        # Generates `sentences` sentences, puts them in a list, and then joins them with spaces.
        paragraph = self.get_random_sentence()
        for _ in range(sentences-1):
            # Get last word of last sentence, without punctuation
            init_prevword = paragraph.split(" ")[-1][:-1]
            paragraph += " " + self.get_random_sentence(init_prevword=init_prevword)
        return paragraph
    
    def get_random_paragraph_min(self, wordmin=30):
        paragraph = self.get_random_sentence()
        while len(paragraph.split()) < wordmin:
            # Get last word of last sentence, without punctuation
            init_prevword = paragraph.split(" ")[-1][:-1]
            paragraph += " " + self.get_random_sentence(init_prevword=init_prevword)
        return paragraph

    def delete_table(self):
        con = sqlite3.connect(self.sqldb)
        try:
            cur = con.cursor()

            # Determine if SQL table exists
            cur.execute("select name from sqlite_master where type='table' and name='edges_first';")
            # ...and then delete if it does
            if len(cur.fetchall()) > 0:
                cur.execute("drop table edges_first;")
                con.commit()
            
            # Same for second-order edges
            cur.execute("select name from sqlite_master where type='table' and name='edges_second';")
            if len(cur.fetchall()) > 0:
                cur.execute("drop table edges_second;")
                con.commit()
            
        except sqlite3.OperationalError as e:
            print("Error:", e)
            con.rollback()
        finally:
            con.close()
