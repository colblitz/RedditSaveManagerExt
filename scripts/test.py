# try:
#     from urllib.parse import urlparse
# except ImportError:
#      from urlparse import urlparse


# import praw
# from pprint import pprint

# import config as Config

# REDDITUSERAGENT    = Config.redditUserAgent
# REDDITAPPID        = Config.redditAppId
# REDDITAPPSECRET    = Config.redditAppSecret
# REDDITUSERNAME     = Config.redditUsername
# REDDITPASSWORD     = Config.redditPassword
# IMGURCLIENTID      = Config.imgurClientId

# reddit = praw.Reddit(
# 	user_agent=REDDITUSERAGENT,
# 	client_id=REDDITAPPID,
# 	client_secret=REDDITAPPSECRET,
# 	username=REDDITUSERNAME,
# 	password=REDDITPASSWORD)

# i = 0
# saved = reddit.user.me().saved(limit=1000)
# urls = []
# for l in saved:
# 	# print l.id, l.permalink
# 	try:
# 		url = l.url
# 		urls.append(url)
# 	except:
# 		pass	
# 	i += 1
# print i

# with open("url.txt", "w") as f:
# 	for u in urls:
# 		f.write(u + "\n")

import requests

url = "https://redgifs.com/watch/equatorialelegantairedale"

def getRedgifsUrl(linkUrl):
	# https://gfycat.com/ForsakenThinDromedary
	rgid = linkUrl.split('/')[-1]
	# info = 'https://gfycat.com/cajax/get/' + gfyId
	info = 'https://api.redgifs.com/v1/redgifs/' + rgid
	resp = requests.get(url=info)
	data = json.loads(resp.text)
	print data
	mp4url = str(data['gfyItem']['mp4Url'])
	logP("mp4url: " + mp4url)
	return mp4url

#getRedgifsUrl(url)
import urllib2
opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36')]

from bs4 import BeautifulSoup
soup = BeautifulSoup(opener.open(url), "html.parser")
print soup
attributes = {"data-react-helmet":"true","type":"application/ld+json"}
content = soup.find("script",attrs=attributes)
print content

# import praw

# import os
# import json
# import time
# import urllib
# import requests

# import config as Config

# REDDITUSERAGENT    = Config.redditUserAgent
# REDDITAPPID        = Config.redditAppId
# REDDITAPPSECRET    = Config.redditAppSecret
# REDDITUSERNAME     = Config.redditUsername
# REDDITPASSWORD     = Config.redditPassword

# reddit = praw.Reddit(
# 	user_agent=REDDITUSERAGENT,
# 	client_id=REDDITAPPID,
# 	client_secret=REDDITAPPSECRET,
# 	username=REDDITUSERNAME,
# 	password=REDDITPASSWORD)

# IMGURCLIENTID = Config.imgurClientId
# PROCESS_LOG = "processLog.txt"

# urllib.URLopener.version = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
# urlRetriever = urllib.URLopener()

# if os.path.exists(PROCESS_LOG):
# 	os.remove(PROCESS_LOG)

# def getLastProcessed(subreddit):
# 	latest = 0
# 	if os.path.exists(PROCESS_LOG):
# 		with open(PROCESS_LOG, 'r') as f:
# 			for line in f:
# 				parts = line.split(",")
# 				if subreddit == parts[0]:
# 					latest = max(latest, parts[1])
# 	return int(latest)

# def updateLastProcessed(subreddit, latestSeen):
# 	with open(PROCESS_LOG, 'a+') as f:
# 		f.write("{},{}\n".format(subreddit, latestSeen))

# SUBMISSIONS_BASE = "https://api.pushshift.io/reddit/submission/search/"
# # SUBMISSIONS_BASE = "https://api.pushshift.io/reddit/search/submission/"
# BATCH_SIZE = 500
# SCORE_THRESHOLD = 2500

# def buildSearch(subreddit, fields, after):
# 	return "{}?subreddit={}&score=>{}&size={}&fields={}&after={}".format(SUBMISSIONS_BASE, subreddit, SCORE_THRESHOLD, BATCH_SIZE, ','.join(fields), after)

# def downloadSubreddit(subreddit):
# 	now = int(time.time())
# 	latestSeen = getLastProcessed(subreddit)
# 	print "Starting from", latestSeen

# 	processed = set()
# 	while latestSeen <= now:
# 		print "Starting Batch ---------------- "
# 		url = buildSearch(subreddit, ['created_utc', 'id', 'author', 'score'], latestSeen)
# 		print "         Url:", url
# 		data = json.loads(requests.get(url).text)['data']
# 		print "     Results:", len(data)

# 		if len(data) == 0:
# 			print "No more"
# 			updateLastProcessed(subreddit, latestSeen)
# 			return

# 		numProcessed = 0
# 		ids = []
# 		info = {}
# 		for s in data:
# 			date = s['created_utc']
# 			latestSeen = max(latestSeen, date)

# 			rid = s['id']
# 			ids.append(rid)
# 			score = s['score']
# 			author = s['author']
			
# 			info[rid] = { "id": rid, "date": date, "author": author }

# 			#print rid, score, author

# 		print "--------------------------------"

# 		ids2 = [i if i.startswith('t3_') else 't3_' + i for i in ids]
# 		print "getting updated scores"
# 		nscores = reddit.info(ids2)

# 		for s in nscores:
# 			s_info = info[s.id]
# 			s_info["score"] = s.score
# 			print s.id, s_info

# 		print "--------------------------------"

# 		print "  Downloaded:", numProcessed
# 		print "Done with batch"

# 	print "Done with batches, last seen:", latestSeen
# 	updateLastProcessed(subreddit, latestSeen)

# # downloadSubreddit("factorio")

# #with open("testfile.txt", "r+")


# # import plotly.express as px
# # df = px.data.iris()

# # print df
# # print type(df)

# import plotly.express as px
# df = px.data.gapminder().query("continent == 'Oceania'")
# print df
# fig = px.line(df, x='year', y='pop', color='country')
# fig.show()

# # fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species",
# #                  size='petal_length', hover_data=['petal_width'])
# # fig.show()


