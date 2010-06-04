#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Wyświetla RSS dla ogłoszeń umieszczonych na stronie wz.uni.lodz.pl.

BY d33tah, LICENSED UNDER WTFPL.

Wymaga RSS2Gen: http://www.dalkescientific.com/Python/PyRSS2Gen.html
"""
from os import system
import urllib 
from lxml import html
import PyRSS2Gen
import datetime
import time
import pysqlite2.dbapi2 as sqlite3

def application(environ, start_response):

  frequency = 30 #for caching purposes
  now = int(time.time())
  url = 'http://zarzadzanie.uni.lodz.pl/Stronag%c5%82%c3%b3wna/' + \
  'Wyszukiwarkaog%c5%82osze%c5%84/tabid/169/language/pl-PL/'   + \
  'Default.aspx?uid='+environ["QUERY_STRING"]
  
  #open the db and re-initialize it if needed
  conn = sqlite3.connect("/home/deathplanter/www/wz/cache.sqlite")
  c = conn.cursor()
  c.execute("CREATE TABLE IF NOT EXISTS cache " + \
	      "(url TEXT UNIQUE, value TEXT, lasttime TEXT)")
  
  #look for the entry for a given url. check its time, use the data if correct
  entry = c.execute("SELECT * FROM cache WHERE url = ?", (url,) ).fetchone()
  if entry:
    if now - int(entry[2]) < frequency:
      page = entry[1]
    else:
      page = urllib.urlopen(url).read().decode('utf-8')
      c.execute("UPDATE cache SET lasttime = ?, value = ?" \
		+ "WHERE url = ?", (now,page,url))
      conn.commit()
  else:
    page = urllib.urlopen(url).read().decode('utf-8')
    c.execute("INSERT INTO cache VALUES (?,?,?)", (url,page,now))
    conn.commit()
  
  tree = html.fromstring(page)
  notices = tree.xpath('//table[@id="%s"]//td[@style="width:300px;"]'
    % 'dnn_ctr558_Search_grvWykladowca' )

  rss = PyRSS2Gen.RSS2(
  title = tree.xpath('//option[@selected="selected"]')[1].text_content(),
  link = "http://deetah.jogger.pl",
  description = "Kanał RSS zawiera najnowsze ogłoszenia od wybranych"
		"wykładowców Wydziału Zarządzania Uniwersytetu Łódzkiego.",
  )
  
  for entry in notices:
    publishDate = entry.getprevious().text
    noticeText = (entry.text_content()
			  .replace("\r", 		'')
			  .replace('\n\t'+12*' ',	'') #some HTML align
		  )[4:] #apparently, there are more spaces here :P

    if len(noticeText)>15 :
      summary = '[%s] %s (...)' % ( publishDate, 
				    noticeText.replace('\n','')[:15] )

    rss.items.append(PyRSS2Gen.RSSItem(
	title = summary,
	description = noticeText,
	link = url,
	guid = PyRSS2Gen.Guid( publishDate + noticeText ),
	pubDate = datetime.datetime(*(int(x) for x in publishDate.split('-')))
	))

  start_response('200 OK', [('Content-type','application/rss+xml')])
  return rss.to_xml(encoding='utf-8')

#print application({"QUERY_STRING":"135"},'')
