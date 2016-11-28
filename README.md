# mythtv-utils

a set of utilities to work with MythTV metadata

### Configuration

Copy mythtv.example.conf to mythtv.conf and edit with your backend database settings.

##### Usage
```sh
user@host:~/mythtv-utils$ python lookup_title.py Big Buck Bunny
intid:		2191
title:		Big Buck Bunny
subtitle:
tagline:	None
director:	Sacha Goedegebure
studio:		Blender Foundation
plot:		Follow a day of the life of Big Buck Bunny when he meets three bullying rodents: Frank, Rinky, and Gamera. The rodents amuse themselves by harassing helpless creatures by throwing fruits, nuts and rocks at them. After the deaths of two of Bunny's favorite butterflies, and an offensive attack on Bunny himself, Bunny sets aside his gentle nature and orchestrates a complex plan for revenge.
rating:		G
inetref:	tmdb3.py_10378
year:		2008
releasedate:	2008-04-10
userrating:	6.5
length:		8
playcount:	0
season:		0
episode:	0
filename:	Big Buck Bunny.mp4
coverfile:	tmdb3.py_10378_coverart.jpg
fanart:		tmdb3.py_10378_fanart.jpg
insertdate:	2016-11-28 14:54:41
contenttype:	MOVIE
```

```sh
user@host:~/mythtv-utils$ python related.py Sintel
Finding movies that are similar to:
Sintel (2010) Colin Levy
------------------------
Score   | Movie
------------------------
 6.0	| How to Train Your Dragon
 3.0	| The Tale of the Princess Kaguya
 3.0	| Spirited Away
 3.0	| The Lego Movie
 3.0	| Mind Game
 3.0	| Avatar
 2.0	| Monsters, Inc.
 2.0	| Princess Mononoke
 2.0	| Beauty and the Beast
 2.0	| The Rescuers
 2.0	| The Secret of NIMH
 2.0	| Labyrinth
 2.0	| E.T. the Extra-Terrestrial
 1.0	| Edward Scissorhands
 1.0	| The Lord of the Rings: The Fellowship of the Ring
 1.0	| Eraserhead
 1.0	| Mars Attacks!
 1.0	| The Lord of the Rings: The Return of the King
 1.0	| Ghost in the Shell
 1.0	| The Lord of the Rings: The Two Towers
 1.0	| Batman Forever
 ```
