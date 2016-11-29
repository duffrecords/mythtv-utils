#!/usr/bin/env python

from database import Database
from formatting import Formatting
import sys
import re

titles_displayed = 21
director_weight = 3.0
year_weight = 1.0
cast_weight = 0.5
rating_weight = 1.0
fmt = Formatting()

def get_random_movie_id(db):
    result = db.run_query("select intid "
                            "from videometadata "
                            "where contenttype='MOVIE' "
                            "order by rand() limit 1;")[0][0]
    return str(result)

def get_movie_data(db, movie_id):
    movie = {}
    result = db.run_query("select title, year, director, rating "
                            "from videometadata "
                            "where contenttype='MOVIE' "
                            "and intid='" + movie_id + "';")[0]
    movie['id'] = movie_id
    movie['title'] = result[0]
    movie['year'] = str(result[1])
    movie['director'] = result[2]
    movie['rating'] = result[3]
    movie['genre'] = []
    movie['cast'] = []
    movie['similarity'] = 0.0
    results = db.run_query("select videogenre.genre "
                            "from videogenre "
                            "inner join videometadatagenre "
                            "on videogenre.intid=videometadatagenre.idgenre "
                            "where videometadatagenre.idvideo='" + movie_id + "';")
    for result in results:
        movie['genre'].append(result[0])
    results = db.run_query("select videocast.cast "
                            "from videocast "
                            "inner join videometadatacast "
                            "on videocast.intid=videometadatacast.idcast "
                            "where videometadatacast.idvideo='" + movie_id + "';")
    for result in results:
        movie['cast'].append(result[0])
    return movie

def get_list_index(listname, key, value):
    try:
        d = filter(lambda n: n.get(key) == value, listname)[0]
        return listname.index(d)
    except:
        return None

def escape_list(listname):
    return [re.sub("'", "\\'", s) for s in listname]

db = Database()

# start with user-specified movie or random movie if not specified
if len(sys.argv) > 1:
    current_movie_title = ' '.join(sys.argv[1:])
    current_movie_id = str(db.run_query("select intid "
                                    "from videometadata "
                                    "where contenttype='MOVIE' "
                                    "and title='" + current_movie_title + "';")[0][0])
else:
    current_movie_id = get_random_movie_id(db)
current_movie = get_movie_data(db, current_movie_id)
print fmt.reset + "Finding movies that are similar to:\n"
header =  "%s (%s) %s" % (current_movie['title'], current_movie['year'], current_movie['director'])
print fmt.header + header + fmt.reset
print fmt.ruler + ("-" * min(len(header), 80)) + fmt.reset
print fmt.header + "Score" + fmt.reset + "   | " + fmt.header + "Movie" + fmt.reset
print fmt.ruler + ("-" * min(len(header), 80)) + fmt.reset

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

# get list of all movies by same director
movies_same_director = []
results = db.run_query("select intid "
                        "from videometadata "
                        "where contenttype='MOVIE' "
                        "and intid <> '" + current_movie['id'] + "' "
                        "and director='" + current_movie['director'] + "';")
for result in results:
    movies_same_director.append(get_movie_data(db, str(result[0])))
    movies_same_director[-1]['similarity'] += 1

# get list of all movies with same rating
movies_same_rating = []
results = db.run_query("select intid "
                        "from videometadata "
                        "where contenttype='MOVIE' "
                        "and intid <> '" + current_movie['id'] + "' "
                        "and rating='" + current_movie['rating'] + "';")
for result in results:
    movies_same_rating.append(get_movie_data(db, str(result[0])))
    movies_same_rating[-1]['similarity'] += 1

# get list of all movies from same genres
movies_same_genres = []
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
                        "order by duplicates.totalCount desc limit 200;")
for result in results:
    movies_same_genres.append(get_movie_data(db, str(result[0])))
    movies_same_genres[-1]['similarity'] += result[1]

# get list of all movies featuring the same cast
movies_same_cast = []
results = db.run_query("select vm.intid, "
                        "duplicates.totalCount "
                        "from videometadata vm "
                        "inner join "
                            "(select vm.intid, count(*) totalCount "
                            "from videometadata vm "
                            "join videometadatacast vmc "
                            "on vmc.idvideo = vm.intid "
                            "join videocast vc "
                            "on vc.intid = vmc.idcast "
                            "where vm.contenttype='MOVIE' "
                            "and vc.cast in ('" + "','".join(escape_list(current_movie['cast'])) + "') "
                            "group by vm.intid) duplicates "
                        "on vm.intid = duplicates.intid "
                        "where vm.intid <> '" + current_movie['id'] + "' "
                        "order by duplicates.totalCount desc limit 200;")
for result in results:
    movies_same_cast.append(get_movie_data(db, str(result[0])))
    movies_same_cast[-1]['similarity'] += result[1]
    #print "%s cast: %s" % (movies_same_cast[-1]['title'], movies_same_cast[-1]['similarity'])
    #if movies_same_cast[-1]['title'] == 'Quantum of Solace' or movies_same_cast[-1]['title'] == 'Casino Royale':
        #print "%s has %s of the same actors" % (movies_same_cast[-1]['title'], movies_same_cast[-1]['similarity'])

# merge lists into new list, ordered by similarity
gallery_list = []
for movie in movies_same_genres:
    #print "analyzing %s" % movie['title']
    if len(gallery_list) >= titles_displayed:
        break
    gallery_list.append(movie)
    m = get_list_index(movies_same_director, 'id', movie['id'])
    if m:
        increment = movies_same_director[m]['similarity'] * director_weight
        gallery_list[-1]['similarity'] += increment
        #print "incrementing similarity of %s by %s because of director" % (increment, movie['title'])
    m = get_list_index(movies_same_rating, 'id', movie['id'])
    if m:
        increment = movies_same_rating[m]['similarity'] * rating_weight
        gallery_list[-1]['similarity'] += increment
        #print "incrementing similarity by %s because of rating" % increment
    m = get_list_index(movies_same_year, 'id', movie['id'])
    if m:
        increment = movies_same_year[m]['similarity'] * year_weight
        gallery_list[-1]['similarity'] += increment
        #print "incrementing similarity by %s because of year" % increment
    m = get_list_index(movies_same_cast, 'id', movie['id'])
    if m:
        increment = movies_same_cast[m]['similarity'] * cast_weight
        gallery_list[-1]['similarity'] += increment
        #print "incrementing similarity of %s by %s because of cast" % (increment, movie['title'])

gallery_list.sort(key=lambda x: x['similarity'], reverse=True)
scores = [movie['similarity'] for movie in gallery_list]
mean = float(sum(scores) / max(len(scores), 1))
for movie in gallery_list:
    if movie['similarity'] > mean:
        text = fmt.boldtext
    else:
        text = fmt.text
    print " %s%s\t%s|%s %s%s" % (text, movie['similarity'], fmt.ruler, text, movie['title'], fmt.reset)
