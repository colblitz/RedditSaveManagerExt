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


def getFilename(url):
	return url.split('/')[-1].split('#')[0].split('?')[0]

def actuallyDownload(url, extension=None):
	filename = getFilename(url)
	if extension:
		filename = os.path.splitext(filename)[0]+extension
		logP("downloading as: " + filename)

	testfile = urllib.URLopener()
	testfile.retrieve(url, "downloads/" + filename)

def getGfycatUrl(linkUrl):
	# https://gfycat.com/ForsakenThinDromedary
	gfyId = linkUrl.split('/')[-1]
	info = 'https://gfycat.com/cajax/get/' + gfyId
	resp = requests.get(url=info)
	data = json.loads(resp.text)
	mp4url = str(data['gfyItem']['mp4Url'])
	logP("mp4url: " + mp4url)
	return mp4url

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
		successSaved += 1
		logP("success")
		unsave(link)
	def skipped():
		logP("skipped")
		skippedUrls.append(linkUrl)
	def album():
		albumTransferred += 1
		logP("transfer")
		transfer(link)
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
			return album()

		elif "imgur.com" in linkUrl and "/gallery/" in linkUrl:
			return album()

		elif "imgur.com" in linkUrl and "." not in getFilename(linkUrl):
			actuallyDownload(linkUrl.replace("imgur.com", "i.imgur.com") + ".jpg")
			return success()

		elif "gfycat" in linkUrl:
			actuallyDownload(getGfycatUrl(linkUrl))
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
for link in sorted(skippedUrls):
	print link

print "------------------------------------------------------------------------"
print "Success: ", successSaved
print "Transferred: ", albumTransferred

logfile.close()
print "done"