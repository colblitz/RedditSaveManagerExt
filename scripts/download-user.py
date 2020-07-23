import os
import json
import time
import urllib
import argparse
import requests

import config as Config

IMGURCLIENTID = Config.imgurClientId

parser = argparse.ArgumentParser()
parser.add_argument('--user', help='Username to download')

urllib.URLopener.version = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
urlRetriever = urllib.URLopener()

def getFilename(url):
	return url.split('/')[-1].split('#')[0].split('?')[0]

def getImgurAlbumLinks(albumId):
	info = 'https://api.imgur.com/3/album/' + albumId + '/images'
	resp = requests.get(url=info, headers={'Authorization': 'Client-ID ' + IMGURCLIENTID})
	data = json.loads(resp.text)
	links = []
	for image in data['data']:
		links.append(image['link'])
	return links

def getGfycatUrl(linkUrl):
	# https://gfycat.com/ForsakenThinDromedary
	gfyId = linkUrl.split('/')[-1]
	# info = 'https://gfycat.com/cajax/get/' + gfyId
	info = 'https://api.gfycat.com/v1/gfycats/' + gfyId
	resp = requests.get(url=info)
	data = json.loads(resp.text)
	mp4url = str(data['gfyItem']['mp4Url'])
	return mp4url

def processUrl(downloadFolder, linkUrl, date, rid):
	print "  Processing:", linkUrl,
	def actuallyDownload(url=linkUrl, extension=None):
		filename = "{}/{}-{}-{}".format(downloadFolder, date, rid, getFilename(url))
		if extension:
			filename = os.path.splitext(filename)[0] + extension
			print "  Downloading as:", filename

		urlRetriever.retrieve(url, filename)
		print "Downloaded"

	def actuallyImgurAlbumDownload(url, i, albumId):
		filename = "{}/{}-{}-{}-{:04d}-{}".format(downloadFolder, date, rid, albumId, i, getFilename(url))
		urlRetriever.retrieve(url, filename)
		print "Downloaded"

	def processImgurAlbum():
		albumId = getFilename(linkUrl)
		links = getImgurAlbumLinks(albumId)
		for i, imageUrl in enumerate(links):
			actuallyImgurAlbumDownload(imageUrl, i, albumId)
			time.sleep(0.05)
		print "Downloaded album:", i

	try:
		if "i.imgur.com" in linkUrl:
			actuallyDownload()

		elif "imgur.com" in linkUrl and "/a/" in linkUrl:
			processImgurAlbum()

		elif "gfycat" in linkUrl:
			print "gfycat thing -------------"
			actuallyDownload(getGfycatUrl(linkUrl))

		elif linkUrl.endswith(".jpg"):
			actuallyDownload()

		elif linkUrl.endswith(".png"):
			actuallyDownload()

		else:
			return False, None
		return True, None
	except Exception, e:
		print ""
		return False, e

def getLastProcessed(user):
	latest = 0
	if os.path.exists("users-saved.txt"):
		with open("users-saved.txt", 'r') as f:
			for line in f:
				parts = line.split(",")
				if user == parts[0]:
					latest = max(latest, parts[1])
	return int(latest)

def updateLastProcessed(user, latestSeen):
	with open("users-saved.txt", 'a+') as f:
		f.write("{},{}\n".format(user, latestSeen))

baseSubmissions = "https://api.pushshift.io/reddit/submission/search/"

def buildSearch(base, author, size, fields, after):
	return "{}?author={}&size={}&fields={}&after={}".format(base, author, size, ','.join(fields), after)

def downloadUser(user):
	now = int(time.time())
	latestSeen = getLastProcessed(user)
	print "Starting from", latestSeen

	downloadFolder = "downloads-" + user
	if not os.path.exists(downloadFolder):
		print "Creating directory:", downloadFolder
		os.makedirs(downloadFolder)

	processed = set()
	while latestSeen <= now:
		print "Starting Batch ------------------------- "
		url = buildSearch(baseSubmissions, user, 500, ['id', 'url', 'created_utc'], latestSeen)
		print "         Url:", url
		data = json.loads(requests.get(url).text)['data']
		print "     Results:", len(data)

		if len(data) == 0:
			print "No more"
			updateLastProcessed(user, latestSeen)
			return

		numProcessed = 0
		for s in data:
			date = s['created_utc']
			url = s['url']
			rid = s['id']
			latestSeen = max(latestSeen, date)

			if "www.reddit.com/r/" in url:
				continue
			if url in processed:
				continue

			result, error = processUrl(downloadFolder, url, date, rid)
			if result:
				processed.add(url)
				numProcessed += 1
			else:
				if type(error).__name__ == "IOError" and error[1] == 404:
					continue

				if error:
					print "  " + str(error)
				else:
					print "  Unknown url"

		print "  Downloaded:", numProcessed
		print "Done with batch"

	print "Done with batches, last seen:", latestSeen
	updateLastProcessed(user, latestSeen)


if __name__ == "__main__":
	print "------------------------------------------------"
	print time.strftime("%c"), int(time.time())
	print "------------------------------------------------"

	args = parser.parse_args()
	if args.user == None:
		print "No user specified"
	else:
		if "," in args.user:
			print "Username has a comma"
		else:
			downloadUser(args.user)

	print "Done"
