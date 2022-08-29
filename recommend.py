import sqlite3
from sqlite3.dbapi2 import Cursor, connect

import spacy
nlp = spacy.load("en_core_web_sm")

def recommendUser(data):
    likedpostId=[]
    for datum in data:
        likedpostId.append(datum[2])

    likedposts=[]
    con = sqlite3.connect('hodomate.db')
    cur = con.cursor()
    for id in likedpostId:
        cur.execute(f"SELECT * FROM cposts where postid='{id}';")
        data=cur.fetchone()
        likedposts.append(data)
    cur.close()
    con.close()

    con = sqlite3.connect('hodomate.db')
    cur = con.cursor()
    cur.execute(f"SELECT * FROM cposts;")
    data=cur.fetchall()
    cur.close()
    con.close()
    s1=""
    s2=""
    recommendedPosts=[]
    for post in likedposts:
        s1 = nlp(post[3])
        for datum in data:
            s2 = nlp(datum[3])
            if(s1.similarity(s2)>0.3 and datum not in recommendedPosts):
                recommendedPosts.append(datum)
    return recommendedPosts
