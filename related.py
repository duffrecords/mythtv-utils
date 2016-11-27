#!/usr/bin/env python

from database import Database
from collections import Counter

def get_random_movie_id(db):
    result = db.run_query("select intid "
                            "from videometadata "
                            "where contenttype='MOVIE' "
                            "order by rand() limit 1;")[0][0]
    return str(result)

def get_movie_data(db, movie_id):
    movie = {}
    result = db.run_query("select title, year, director "
                            "from videometadata "
                            "where contenttype='MOVIE' "
                            "and intid='"+movie_id+"';")[0]
    movie['id'] = movie_id
    movie['title'] = result[0]
    movie['year'] = str(result[1])
    movie['director'] = result[2]
    movie['genre'] = []
    movie['similarity'] = 0
    results = db.run_query("select videogenre.genre "
                            "from videogenre inner "
                            "join videometadatagenre "
                            "on videogenre.intid=videometadatagenre.idgenre "
                            "where videometadatagenre.idvideo='" + movie_id + "';")
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
results = db.run_query("select intid "
                        "from videometadata "
                        "where contenttype='MOVIE' "
                        "and intid <> '" + current_movie['id'] + "' "
                        "and year='" + current_movie['year'] + "';")
for result in results:
    movies_same_year.append(get_movie_data(db, str(result[0])))
    print "    %s (year: %s)" % (movies_same_year[-1]['title'], movies_same_year[-1]['year'])

# get list of all movies by same director
movies_same_director = []
results = db.run_query("select intid "
                        "from videometadata "
                        "where contenttype='MOVIE' "
                        "and intid <> '" + current_movie['id'] + "' "
                        "and director='" + current_movie['director'] + "';")
for result in results:
    movies_same_director.append(get_movie_data(db, str(result[0])))
    print "    %s (director: %s)" % (movies_same_director[-1]['title'], movies_same_director[-1]['director'])

# get list of all movies from same genres
movies_same_genres = []
#print(','.join(current_movie['genre']))
results = db.run_query("select vm.intid, "
                        "duplicates.totalCount "
                        "from videometadata vm "
                        "inner join "
                            "(select vm.intid, count(*) totalCount "
                            "from videometadata vm "
                            "join videometadatagenre vmg "
                            "on vmg.idvideo = vm.intid "
                            "join videogenre vg "
                            "on vg.intid = vmg.idgenre "
                            "where vm.contenttype='MOVIE' "
                            "and vg.genre in ('" + "','".join(current_movie['genre']) + "') "
                            "group by vm.intid) duplicates "
                        "on vm.intid = duplicates.intid "
                        "where vm.intid <> '" + current_movie['id'] + "' "
                        "order by duplicates.totalCount desc limit 10;")
for result in results:
    movies_same_genres.append(get_movie_data(db, str(result[0])))
    movies_same_genres[-1]['similarity'] += int(result[1])
    print "    %s (%s genres in common)" % (movies_same_genres[-1]['title'], movies_same_genres[-1]['similarity'])
