import argparse
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
	try:
		logfile.write(s + "\n")
	except:
		print "#####################################################"
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
	# info = 'https://gfycat.com/cajax/get/' + gfyId
	info = 'https://api.gfycat.com/v1/gfycats/' + gfyId
	resp = requests.get(url=info)
	data = json.loads(resp.text)
	print data
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

def unsaveRemoved(link):
	logP("unsaving removed: " + link.id)
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

SUCCESS = 1
SKIPPED = 2

# console.log(document.getElementsByTagName("source")[0].src);

def processUrl(linkUrl):
	try:
		if "i.imgur.com" in linkUrl:
			if ".png" in linkUrl:
				actuallyDownload(linkUrl, ".jpg")
			elif ".gifv" in linkUrl:
				actuallyDownload(linkUrl.replace(".gifv", ".mp4"))
			else:
				actuallyDownload(linkUrl)
			return SUCCESS

		elif "imgur.com" in linkUrl and "/a/" in linkUrl:
			processImgurAlbum(linkUrl)
			return SUCCESS

		elif "imgur.com" in linkUrl and "/gallery/" in linkUrl:
			processImgurAlbum(linkUrl)
			return SUCCESS

		elif "imgur.com" in linkUrl and "." not in getFilename(linkUrl):
			actuallyDownload(linkUrl.replace("imgur.com", "i.imgur.com") + ".jpg")
			return SUCCESS

		elif "gfycat" in linkUrl:
			if linkUrl.endswith(".mp4"):
				actuallyDownload(linkUrl)
				return SUCCESS
			actuallyDownload(getGfycatUrl(linkUrl))
			return SUCCESS

		elif "eroshare" in linkUrl:
			processEroshareAlbum(linkUrl)
			return SUCCESS

		# https://i.reddituploads.com/1656217e668841e5b8cc202677de3b41?fit=max&h=1536&w=1536&s=da7a74bcf57c81979e6cbf2e9e4b25bf
		elif "i.reddituploads.com" in linkUrl:
			actuallyDownload(linkUrl, ".jpg")
			return SUCCESS

		elif linkUrl.endswith(".jpg"):
			actuallyDownload(linkUrl)
			return SUCCESS

		elif linkUrl.endswith(".png"):
			actuallyDownload(linkUrl)
			return SUCCESS

		elif linkUrl.endswith(".gif"):
			actuallyDownload(linkUrl)
			return SUCCESS

		elif linkUrl.endswith(".mp4"):
			actuallyDownload(linkUrl)
			return SUCCESS

		return SKIPPED
	except Exception, e:
		return e

# return (bool - success, string - skipped, exception - error)
def tryProcessLink(link):
	linkId = link.id
	linkUrl = ""

	if type(link).__name__ == "Comment" and link.author is None:
		unsaveRemoved(link)
		return

	log("")

	try:
		linkUrl = link.url
	except:
		log(linkId + " - not a link")
		return False, link, None

	log(linkId + " - " + linkUrl)

	result = processUrl(linkUrl)
	if result == SUCCESS:
		logP("success")
		unsave(link)
		return True, None, None
	elif result == SKIPPED:
		logP("can't handle, skipped")
		return False, link.id + " " + linkUrl, None
	else:
		logP("## error: " + str(result))
		return False, None, link.id + " " + link.url + ": " + str(result)


parser=argparse.ArgumentParser()
parser.add_argument('--file', help='File with urls')


def tryProcessBatch():
	linksSuccess = 0
	linksSkipped = []
	linksErrored = []

	print "------------------------------------------------------------------------"
	print "Starting batch"

	saved = reddit.user.me().saved(limit=500)

	print "Got batch of saved links"

	linksTried = 0
	for link in saved:
		success, skipped, error = tryProcessLink(link)
		linksTried += 1
		if success:
			linksSuccess += 1
		else:
			if skipped:
				linksSkipped.append(skipped)
			else:
				linksErrored.append(error)

	print "Done with batch, saved {} / {}".format(linksSuccess, linksTried)
	return linksSuccess, linksSkipped, linksErrored


if __name__ == "__main__":
	log("------------------------------------------------------------------------")
	log("---" + time.strftime("%c"))

	args=parser.parse_args()

	if args.file == None:
		totalSaved = 0

		totalSkipped = set()
		totalErrored = set()

		while True:
			linksSuccess, linksSkipped, linksErrored = tryProcessBatch()
			totalSkipped.update(linksSkipped)
			totalErrored.update(linksErrored)
			if linksSuccess == 0:
				print "None saved in batch, stopping"
				break
			totalSaved += linksSuccess

		print "#######################################################################3"
		print ""
		print "Skipped", len(totalSkipped)
		print ""
		for link in sorted(list(totalSkipped), key=lambda s: str(s)[7:]):
			print link

		print "#######################################################################3"
		print ""
		print "Errors", len(totalErrored)
		print ""
		for link in sorted(list(totalErrored)):
			print link

		print "#######################################################################3"
		print ""
		print "Saved", len(totalSaved)
		print ""

		print "#######################################################################3"
		print "Done"
		logfile.close()

	else:
		urlfile = open(args.file, 'r')
		for url in urlfile:
			print url.strip()
			print processUrl(url.strip())