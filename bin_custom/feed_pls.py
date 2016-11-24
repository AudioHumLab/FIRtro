#!/usr/bin/env python
#coding=utf-8

import feedparser
from subprocess import Popen
from os.path import expanduser
import re

HOME            = expanduser("~")
PLAYLISTSDIR    = HOME + "/music"   # la ponemos aquí pq es donde MPaD las lee
FEEDSFILE       = PLAYLISTSDIR + "/_mis_feeds" 
PLAYLIST_PREFIX = "RSS_"    # Un prefijo a las playlist de feeds, que quede la lista ordenadita

# OjO    [ ] / \ = + ; : " , | *   cannot be used on CIFS/SMB:
cifs_prohib = ['[', ']', '/', '\\', '=', '+', ';', ':', '"', ',', '|', '*']

mis_urls = []

f = open(FEEDSFILE, "r")

while True:
    url = f.readline()
    if not url: break
    if ("http" in url) and (not "#" in url):  # una validación naif
        mis_urls.append(url[:-1]) 
f.close()

# vamos pallá
for url in mis_urls:

    feed = feedparser.parse(url)
    nombre_feed = feed['feed'].title

    for x in cifs_prohib:    # evitamos caracteres prohibidos en el nas montado cifs
        nombre_feed = nombre_feed.replace(x, "-")
        
    playlist = PLAYLISTSDIR + "/" + PLAYLIST_PREFIX + nombre_feed + ".pls"

    f = open(playlist, "w")
    f.write("[playlist]\n")
    
    n = 0   # contador de podcasts

    for entrada in feed['entries']:
    
        # print entrada.keys()
        # RTVE:
        # ['summary_detail', 'subtitle', 'published_parsed', 'links', 'title', 'tags', 'itunes_explicit', 'summary', 'content', 'guidislink', 'title_detail', 'link', 'itunes_keywords', 'published', 'subtitle_detail', 'id', 'itunes_duration']
        # AUDIOATALAIA:
        # ['summary_detail', 'published_parsed', 'links', 'title', 'tags', 'summary', 'guidislink', 'title_detail', 'link', 'published', 'media_content', 'id', 'media_keywords']  
        
        n = n + 1

        mp3_title = entrada.title
        mp3_title = re.sub( '.rs .onora',         'AS ', mp3_title)
        mp3_title = re.sub(u'25 años',            '25',  mp3_title)
        mp3_title = re.sub( '..a ..mite',         'VL ', mp3_title)
        mp3_title = re.sub( '.a .asa .el .onido', 'LCS', mp3_title)
        mp3_title = re.sub( '..sica .e .adie',    'MdN', mp3_title)
        mp3_title = re.sub( '.l o.do atento',     'EOA', mp3_title)
        mp3_title = re.sub( '..sica .iva',        'MV ', mp3_title)
        
        mp3_descrip = entrada.description.split("</p>")[0][3:] # probado solo en RTVE

        # Buscamos el audio, que está en algún campo de "links":
        # OjO a veces no hay un mp3, hay una llamada a una peich que no se utilizar:
        # <enclosure url="http://ztnr.rtve.es/ztnr/res/_PROVIDER_/audio/high/_TOKEN_" length="226963963" type="audio/mpeg" />
        for elemento in entrada.links:
            if 'mp3' in elemento.href:
                mp3_url = elemento.href
                mp3_length = elemento.length 
                segundos = int(int(mp3_length) / 32000) # solo vale para los de rtve 256Kbps

            
                f.write("File"   + str(n) + " = " + mp3_url                   + "\n")
                f.write("Title"  + str(n) + " = " + mp3_title.encode('UTF-8') + "\n")
                f.write("Length" + str(n) + " = " + str(segundos)             + "\n")
                f.write("\n")
 
    f.write("NumberOfEntries = " + str(n) + "\n")
    f.close()


