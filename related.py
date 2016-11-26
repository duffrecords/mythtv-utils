#!/usr/bin/env python

from database import Database
from collections import Counter

def get_random_movie_id(db):
    result = db.run_query("select intid from videometadata where contenttype='MOVIE' order by rand() limit 1;")[0][0]
    return str(result)

def get_movie_data(db, movie_id):
    movie = {}
    result = db.run_query("select title, year, director from videometadata where contenttype='MOVIE' and intid='"+movie_id+"';")[0]
    movie['id'] = movie_id
    movie['title'] = result[0]
    movie['year'] = str(result[1])
    movie['director'] = result[2]
    movie['genre'] = []
    results = db.run_query("select videogenre.genre from videogenre inner join videometadatagenre on videogenre.intid=videometadatagenre.idgenre where videometadatagenre.idvideo='"+movie_id+"';")
    for result in results:
        movie['genre'].append(result[0])
    return movie

db = Database()

# start with a random movie
current_movie_id = get_random_movie_id(db)
current_movie = get_movie_data(db, current_movie_id)
print "%s (%s)" % (current_movie['title'], current_movie['year'])

# get list of all movies released in the same year
movies_same_year = []
results = db.run_query("select intid from videometadata where year='"+current_movie['year']+"' and contenttype='MOVIE' and intid <> '" + current_movie['id'] + "';")
for result in results:
    movies_same_year.append(get_movie_data(db, str(result[0])))
    print "    %s (%s)" % (movies_same_year[-1]['title'], movies_same_year[-1]['year'])
