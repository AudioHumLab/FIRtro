#!/usr/bin/env python
#coding=utf-8

import feedparser
from subprocess import Popen
from os.path import expanduser

HOME            = expanduser("~")
PLAYLISTSDIR    = HOME + "/music"   # la ponemos aquí pq es donde MPaD las lee
FEEDSFILE       = PLAYLISTSDIR + "/_mis_feeds" 
PLAYLIST_PREFIX = "RSS_"    # Un prefijo a las playlist de feeds, que quede la lista ordenadita

# OjO    [ ] / \ = + ; : " , | *   cannot be used on CIFS/SMB:
cifs_prohib = ['[', ']', '/', '\\', '=', '+', ';', ':', '"', ',', '|', '*']


f = open(FEEDSFILE, "r")

while True:

    url = f.readline()

    if not url: break

    if ("http" in url) and (not "#" in url):  # una validación naif
        feed = feedparser.parse(url)
        nombre_feed = feed['feed'].title

        for x in cifs_prohib:    # evitamos caracteres prohibidos en el nas montado cifs
            nombre_feed = nombre_feed.replace(x, "-")
        
        playlist = PLAYLISTSDIR + "/" + PLAYLIST_PREFIX + nombre_feed + ".rss"
        Popen("curl --silent \"" + url + "\" > \"" + playlist + "\"", shell=True)

f.close()

    


