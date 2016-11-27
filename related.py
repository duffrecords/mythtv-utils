#!/usr/bin/env python

from database import Database
#from collections import Counter
import sys

titles_displayed = 21
director_weight = 3

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
                            "and intid='" + movie_id + "';")[0]
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

def get_list_index(listname, key, value):
    try:
        d = filter(lambda n: n.get(key) == value, listname)[0]
        return listname.index(d)
    except:
        return None

db = Database()

# start with a random movie
if len(sys.argv) > 1:
    current_movie_title = ' '.join(sys.argv[1:])
    current_movie_id = str(db.run_query("select intid "
                                    "from videometadata "
                                    "where contenttype='MOVIE' "
                                    "and title='" + current_movie_title + "';")[0][0])
else:
    current_movie_id = get_random_movie_id(db)
current_movie = get_movie_data(db, current_movie_id)
print "%s (%s)" % (current_movie['title'], current_movie['year'])

# get list of all movies released in the same year
movies_same_year = []
year = int(current_movie['year'])
plus_or_minus_one = "('" + str(year - 1) + "', '" + str(year + 1) + "')"
plus_or_minus_two = "('" + str(year - 1) + "', '" + str(year + 1) + "')"
results = db.run_query("select intid, "
                        "'3' as similarity "
                        "from videometadata "
                        "where contenttype='MOVIE' "
                        "and intid <> '" + current_movie['id'] + "' "
                        "and year='" + current_movie['year'] + "' "
                        "union select intid, "
                        "'2' as similarity "
                        "from videometadata "
                        "where contenttype='MOVIE' "
                        "and year in " + plus_or_minus_one + " "
                        "union select intid, "
                        "'1' as similarity "
                        "from videometadata "
                        "where contenttype='MOVIE' "
                        "and year in " + plus_or_minus_two + ";")
for result in results:
    movies_same_year.append(get_movie_data(db, str(result[0])))
    movies_same_year[-1]['similarity'] += int(result[1])
    #print "    %s (year: %s) +%s" % (movies_same_year[-1]['title'], movies_same_year[-1]['year'], movies_same_year[-1]['similarity'])

# get list of all movies by same director
movies_same_director = []
results = db.run_query("select intid "
                        "from videometadata "
                        "where contenttype='MOVIE' "
                        "and intid <> '" + current_movie['id'] + "' "
                        "and director='" + current_movie['director'] + "';")
for result in results:
    movies_same_director.append(get_movie_data(db, str(result[0])))
    #print "    %s (director: %s)" % (movies_same_director[-1]['title'], movies_same_director[-1]['director'])

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
                        "order by duplicates.totalCount desc limit 100;")
for result in results:
    movies_same_genres.append(get_movie_data(db, str(result[0])))
    movies_same_genres[-1]['similarity'] += result[1]
    #print "    %s (%s genres in common)" % (movies_same_genres[-1]['title'], movies_same_genres[-1]['similarity'])

# merge lists into new list, ordered by similarity
gallery_list = []
#print "movies_same_year: %s" % len(movies_same_year)
#print "movies_same_genres: %s" % len(movies_same_genres)
#print "movies_same_director: %s" % len(movies_same_director)
#print "gallery list: %s" % len(gallery_list)

for movie in movies_same_genres:
    if len(gallery_list) >= titles_displayed:
        break
    gallery_list.append(movie)
    m = get_list_index(movies_same_director, 'id', movie['id'])
    if m:
        #if any(d['id'] == movie['id'] for d in movies_same_director):
        gallery_list[-1]['similarity'] += director_weight
        #print "    %s %s" % (gallery_list[-1]['title'], gallery_list[-1]['similarity'])
    m = get_list_index(movies_same_year, 'id', movie['id'])
    if m:
        #if any(d['id'] == movie['id'] for d in movies_same_year):
        movies_same_year[m]['similarity']
        gallery_list[-1]['similarity'] += movies_same_year[m]['similarity']
        #print "    %s %s" % (gallery_list[-1]['title'], gallery_list[-1]['similarity'])

#print "gallery list: %s" % len(gallery_list)

gallery_list.sort(key=lambda x: x['similarity'], reverse=True)
for movie in gallery_list:
    print "    %s %s" % (movie['similarity'], movie['title'])
