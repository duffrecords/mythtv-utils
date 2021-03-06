#!/usr/bin/env python

from database import Database
from formatting import Formatting
import sys
import re

# initialize some parameters
titles_displayed = 21
weight = {
    'director': 3.0,
    'year': 1.0,
    'cast': 0.5,
    'rating': 1.0
}
categories = ['director', 'rating', 'year', 'cast']
similar_movies = {}
fmt = Formatting()
db = Database()

def get_random_movie_id(db):
    query = ("select intid from videometadata "
            "where contenttype='MOVIE' "
            "order by rand() limit 1")
    result = db.run_query(query, '')[0][0]
    return str(result)

def get_movie_data(db, movie_id):
    movie = {}
    query = ("select title, year, director, rating from videometadata "
            "where contenttype='MOVIE' and intid=%s")
    result = db.run_query(query, (movie_id,))[0]
    movie['id'] = movie_id
    movie['title'] = result[0]
    movie['year'] = str(result[1])
    movie['director'] = result[2]
    movie['rating'] = result[3]
    movie['genre'] = []
    movie['cast'] = []
    movie['similarity'] = 0.0
    query = ("select videogenre.genre from videogenre "
            "inner join videometadatagenre "
            "on videogenre.intid=videometadatagenre.idgenre "
            "where videometadatagenre.idvideo=%s")
    results = db.run_query(query, (movie_id,))
    for result in results:
        movie['genre'].append(result[0])
    query = ("select videocast.cast from videocast "
            "inner join videometadatacast "
            "on videocast.intid=videometadatacast.idcast "
            "where videometadatacast.idvideo=%s")
    result = db.run_query(query, (movie_id,))
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

# start with user-specified movie or random movie if not specified
if len(sys.argv) > 1:
    if sys.argv[1] == '--batch' or sys.argv[1] == '-B':
        batch_mode = True
        current_movie_title = ' '.join(sys.argv[2:])
    else:
        batch_mode = False
        current_movie_title = ' '.join(sys.argv[1:])
    query = ("select intid from videometadata "
            "where contenttype='MOVIE' and title = %s")
    result = db.run_query(query, (current_movie_title,))
    if len(result) != 1:
        print "Couldn't find movie!"
        sys.exit(1)
    current_movie_id = str(result[0][0])
else:
    current_movie_id = get_random_movie_id(db)
current_movie = get_movie_data(db, current_movie_id)

# print table with formatting
if not batch_mode:
    print fmt.reset + "Finding movies that are similar to:\n"
    header =  "%s (%s) %s" % (current_movie['title'],
                              current_movie['year'],
                              current_movie['director'])
    print fmt.header + header + fmt.reset
    print fmt.ruler + ("-" * min(len(header), 80)) + fmt.reset
    print "%sScore%s   | %sMovie%s" % (fmt.header,
                                       fmt.reset,
                                       fmt.header,
                                       fmt.reset)
    print fmt.ruler + ("-" * min(len(header), 80)) + fmt.reset

# get list of all movies released in the same year
similar_movies['year'] = []
year = int(current_movie['year'])
plus_or_minus_one = (str(year - 1), str(year + 1))
plus_or_minus_two = "('" + str(year - 1) + "', '" + str(year + 1) + "')"
query = ("select intid, '3' as similarity from videometadata "
        "where contenttype='MOVIE' and intid <> %s and year=%s "
        "union select intid, '2' as similarity from videometadata "
        "where contenttype='MOVIE' and year in (%s,%s) "
        "union select intid, '1' as similarity from videometadata "
        "where contenttype='MOVIE' and year in (%s,%s)")
params = (current_movie['id'], current_movie['year'],
            year-1, year+1, year-2, year+2)
results = db.run_query(query, params)
for result in results:
    similar_movies['year'].append(get_movie_data(db, str(result[0])))
    similar_movies['year'][-1]['similarity'] += int(result[1])

# get list of all movies by same director
similar_movies['director'] = []
query = ("select intid from videometadata "
        "where contenttype='MOVIE' and intid <> %s and director = %s")
results = db.run_query(query, (current_movie['id'], current_movie['director']))
for result in results:
    similar_movies['director'].append(get_movie_data(db, str(result[0])))
    similar_movies['director'][-1]['similarity'] += 1

# get list of all movies with same rating
similar_movies['rating'] = []
query = ("select intid from videometadata "
        "where contenttype='MOVIE' and intid <> %s and rating = %s")
results = db.run_query(query, (current_movie['id'], current_movie['rating']))
for result in results:
    similar_movies['rating'].append(get_movie_data(db, str(result[0])))
    similar_movies['rating'][-1]['similarity'] += 1

# get list of all movies from same genres
similar_movies['genres'] = []
placeholders = ', '.join(['%s'] * len(current_movie['genre']))
query = ("select vm.intid, duplicates.totalCount "
        "from videometadata vm "
        "inner join "
        "(select vm.intid, count(*) totalCount "
        "from videometadata vm "
        "join videometadatagenre vmg on vmg.idvideo = vm.intid "
        "join videogenre vg on vg.intid = vmg.idgenre "
        "where vm.contenttype='MOVIE' and vg.genre in (%s) "
        "group by vm.intid) duplicates "
        "on vm.intid = duplicates.intid "
        "where vm.intid <> %s "
        "order by duplicates.totalCount desc limit 1000") % (placeholders, '%s')
params = [i for i in current_movie['genre']]
params.append(current_movie['id'])
results = db.run_query(query, params)
for result in results:
    similar_movies['genres'].append(get_movie_data(db, str(result[0])))
    similar_movies['genres'][-1]['similarity'] += result[1]

# get list of all movies featuring the same cast
similar_movies['cast'] = []
placeholders = ', '.join(['%s'] * len(current_movie['cast']))
query = ("select vm.intid, duplicates.totalCount "
        "from videometadata vm "
        "inner join (select vm.intid, count(*) totalCount "
        "from videometadata vm "
        "join videometadatacast vmc on vmc.idvideo = vm.intid "
        "join videocast vc on vc.intid = vmc.idcast "
        "where vm.contenttype='MOVIE' and vc.cast in (%s) "
        "group by vm.intid) duplicates "
        "on vm.intid = duplicates.intid "
        "where vm.intid <> %s "
        "order by duplicates.totalCount desc "
        "limit 1000;") % (placeholders, '%s')
params = [i for i in current_movie['cast']]
params.append(current_movie['id'])
results = db.run_query(query, params)
#print "%s movies with the same cast" % len(results)
for result in results:
    similar_movies['cast'].append(get_movie_data(db, str(result[0])))
    similar_movies['cast'][-1]['similarity'] += result[1]

# merge lists into new list, ordered by similarity
gallery_list = []
for movie in similar_movies['genres']:
    #print "analyzing %s %s" % (movie['id'], movie['title'])
    gallery_list.append(movie)
    for category in categories:
        i = get_list_index(similar_movies[category], 'id', movie['id'])
        if i:
            inc = similar_movies[category][i]['similarity'] * weight[category]
            gallery_list[-1]['similarity'] += inc

# sort the final list and print in table form,
# highlighting movies whose scores are above the mean
gallery_list.sort(key=lambda x: x['similarity'], reverse=True)
gallery_list = gallery_list[:titles_displayed]
scores = [movie['similarity'] for movie in gallery_list]
mean = float(sum(scores) / max(len(scores), 1))
for movie in gallery_list:
    if movie['similarity'] > mean:
        text = fmt.boldtext
    else:
        text = fmt.text
    if not batch_mode:
        print " %s%s\t%s|%s %s%s" % (text, movie['similarity'],
                                    fmt.ruler,
                                    text, movie['title'], fmt.reset)
    else:
        print "%s" % movie['title']
