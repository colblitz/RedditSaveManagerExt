import praw
import re
import urllib
import os
import time
import requests
import json

import config as Config

REDDITUSERAGENT    = Config.redditUserAgent
REDDITAPPID        = Config.redditAppId
REDDITAPPSECRET    = Config.redditAppSecret
REDDITUSERNAME     = Config.redditUsername
REDDITPASSWORD     = Config.redditPassword
REDDITUSERNAME2    = Config.redditUsername2
REDDITPASSWORD2    = Config.redditPassword2
IMGURCLIENTID      = Config.imgurClientId

reddit = praw.Reddit(
	user_agent=REDDITUSERAGENT,
	client_id=REDDITAPPID,
	client_secret=REDDITAPPSECRET,
	username=REDDITUSERNAME,
	password=REDDITPASSWORD)

reddit2 = praw.Reddit(
	user_agent=REDDITUSERAGENT,
	client_id=REDDITAPPID,
	client_secret=REDDITAPPSECRET,
	username=REDDITUSERNAME2,
	password=REDDITPASSWORD2)

# urllib.URLopener.version = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36 SE 2.X MetaSr 1.0'
urllib.URLopener.version = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

logfile = open('output.log', 'a')

def log(s):
	logfile.write(s + "\n")
	print s

def logP(s):
	s = "       - " + s
	log(s)


downloadFolder = "downloads-" + time.strftime("%Y-%m-%d") + "/"
downloadAlbumFolder = downloadFolder + "albums/"
if not os.path.exists(downloadFolder):
	log("Creating directory: " + downloadFolder)
	os.makedirs(downloadFolder)

if not os.path.exists(downloadAlbumFolder):
	log("Creating directory: " + downloadAlbumFolder)
	os.makedirs(downloadAlbumFolder)

def getFilename(url):
	return url.split('/')[-1].split('#')[0].split('?')[0]

def actuallyDownload(url, extension=None):
	filename = getFilename(url)
	if extension:
		filename = os.path.splitext(filename)[0]+extension
		logP("downloading as: " + filename)

	testfile = urllib.URLopener()
	testfile.retrieve(url, downloadFolder + filename)

def actuallyImgurAlbumDownload(url, i, albumId):
	filename = getFilename(url)
	testfile = urllib.URLopener()
	testfile.retrieve(url, downloadAlbumFolder + albumId + "-" +  ('%04d' % i) + "-" + filename)

def actuallyEroshareDownload(eItem, albumId):
	position = eItem[0]
	url = eItem[1]
	filename = getFilename(url)
	testfile = urllib.URLopener()
	testfile.retrieve(url, downloadAlbumFolder + albumId + "-" +  ('%04d' % position) + "-" + filename)

def getGfycatUrl(linkUrl):
	# https://gfycat.com/ForsakenThinDromedary
	gfyId = linkUrl.split('/')[-1]
	info = 'https://gfycat.com/cajax/get/' + gfyId
	resp = requests.get(url=info)
	data = json.loads(resp.text)
	mp4url = str(data['gfyItem']['mp4Url'])
	logP("mp4url: " + mp4url)
	return mp4url

def getImgurAlbumLinks(albumId):
	info = 'https://api.imgur.com/3/album/' + albumId + '/images'
	resp = requests.get(url=info, headers={'Authorization': 'Client-ID ' + IMGURCLIENTID})
	data = json.loads(resp.text)
	links = []
	for image in data['data']:
		links.append(image['link'])
	return links

def processImgurAlbum(albumUrl):
	albumId = getFilename(albumUrl)
	links = getImgurAlbumLinks(albumId)
	for i, imageUrl in enumerate(links):
		actuallyImgurAlbumDownload(imageUrl, i, albumId)
		time.sleep(0.05)
	logP("downloaded " + str(len(links)))


def getEroshareAlbumLinks(albumId):
	info = 'https://api.eroshare.com/api/v1/albums/' + albumId
	resp = requests.get(url = info)
	data = json.loads(resp.text)
	links = []
	for item in data['items']:
		if item['type'] == 'Video':
			links.append((item['position'], item['url_mp4']))
		else:
			links.append((item['position'], 'https:' + item['url_full']))
	print links
	return links

def processEroshareAlbum(albumUrl):
	albumId = getFilename(albumUrl)
	links = getEroshareAlbumLinks(albumId)
	for eItem in links:
		actuallyEroshareDownload(eItem, albumId)
		time.sleep(0.05)
	logP("downloaded " + str(len(links)))

def unsave(link):
	logP("unsaving: " + link.id + " " + link.url)
	link.unsave()

def transfer(link):
	logP("transferring: " + link.id + " " + link.url)
	other = reddit2.submission(id=link.id)
	other.save()
	link.unsave()

skippedUrls = []
errorMessages = []
successSaved = 0
albumTransferred = 0

def tryProcessLink(link):
	linkId = link.id
	linkUrl = ""
	try:
		linkUrl = link.url
	except:
		logP("skipped - not link")
		skippedUrls.append(link)
		return

	log("")
	log(linkId + " - " + linkUrl)

	def success():
		global successSaved
		successSaved += 1
		logP("success")
		unsave(link)
	def skipped():
		logP("skipped")
		skippedUrls.append(link.id + " " + linkUrl)
	def error(e):
		logP("## error: " + str(e))
		errorMessages.append(link.id + " " + link.url + ": " + str(e))

	try:
		if "i.imgur.com" in linkUrl:
			if ".png" in linkUrl:
				actuallyDownload(linkUrl, ".jpg")
			elif ".gifv" in linkUrl:
				actuallyDownload(linkUrl.replace(".gifv", ".mp4"))
			else:
				actuallyDownload(linkUrl)
			return success()

		elif "imgur.com" in linkUrl and "/a/" in linkUrl:
			processImgurAlbum(linkUrl)
			return success()

		elif "imgur.com" in linkUrl and "/gallery/" in linkUrl:
			processImgurAlbum(linkUrl)
			return success()

		elif "imgur.com" in linkUrl and "." not in getFilename(linkUrl):
			actuallyDownload(linkUrl.replace("imgur.com", "i.imgur.com") + ".jpg")
			return success()

		elif "gfycat" in linkUrl:
			actuallyDownload(getGfycatUrl(linkUrl))
			return success()

		elif "eroshare" in linkUrl:
			processEroshareAlbum(linkUrl)
			return success()

		# https://i.reddituploads.com/1656217e668841e5b8cc202677de3b41?fit=max&h=1536&w=1536&s=da7a74bcf57c81979e6cbf2e9e4b25bf
		elif "i.reddituploads.com" in linkUrl:
			actuallyDownload(linkUrl, ".jpg")
			return success()

		elif linkUrl.endswith(".jpg"):
			actuallyDownload(linkUrl)
			return success()

		elif linkUrl.endswith(".png"):
			actuallyDownload(linkUrl)
			return success()

		elif linkUrl.endswith(".gif"):
			actuallyDownload(linkUrl)
			return success()

		return skipped()
	except Exception, e:
		return error(e)

saved = reddit.user.me().saved(limit=500)

log("------------------------------------------------------------------------")
log("---" + time.strftime("%c"))

for link in saved:
	tryProcessLink(link)

print "------------------------------------------------------------------------"
print "Errors", len(errorMessages)
print ""
for link in sorted(errorMessages):
	print link

print ""
print "------------------------------------------------------------------------"
print "Skipped", len(skippedUrls)
print ""
for link in sorted(skippedUrls, key=lambda s: str(s)[7:]):
	print link

print "------------------------------------------------------------------------"
print "Success: ", successSaved
print "Transferred: ", albumTransferred

logfile.close()
print "done"