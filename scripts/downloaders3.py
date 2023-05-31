import json
import os
import requests
import time
import urllib
from urllib.request import urlopen
#import urllib2
import shutil

from bs4 import BeautifulSoup
import traceback


import config as Config
IMGURCLIENTID = Config.imgurClientId
ALBUMSLEEP = 0.05

# urllib.URLopener.version = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
# opener = urllib2.build_opener()
# opener.addheaders = [('User-Agent', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36")]

import os.path

# open any redgif, search for api call with header
# REDGIF_TOKEN = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJodHRwczovL3d3dy5yZWRnaWZzLmNvbS8iLCJpYXQiOjE2NzI0NzYxNDcsImV4cCI6MTY3MjU2MjU0Nywic3ViIjoiY2xpZW50LzE4MjNjMzFmN2QzLTc0NWEtNjU4OS0wMDA1LWQ4ZThmZTBhNDRjMiIsInNjb3BlcyI6InJlYWQiLCJ2YWxpZF9hZGRyIjoiNjkuMTE1LjEyNi4xMjgiLCJ2YWxpZF9hZ2VudCI6Ik1vemlsbGEvNS4wIChYMTE7IExpbnV4IHg4Nl82NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzk2LjAuNDY2NC40NSBTYWZhcmkvNTM3LjM2In0.o_exS8cVZ3kuByKYLrZwkag2LI4_3DvoEc4VVQX3wIkViRpLtIg1NAwx3imHnlujuk4v3cDXCVDhZYl7F8hRjHW-wHJ4g3qS_8rMbdv-o5ZBujEdN7L6DS0gLkaCcAifRuPGy4n6T6eTHLluQsYzSZuQgP5D-zKWHGFcu8oU0WFnEq8PXsLwQbKm5VFiydyRAiEQ7qRYhFnG4ERMU2YZf5gm1JtVOBZfnqNQSK3h7obPfxUZ3aaSIgDWx_iAcl65y1k52Xv0Ah8560cJX21_gKMkDUgcYkwRerxgqRBreZZJToZfZEfG50jJGNTU7AgoDYEm6yA1vZtA37Wh7WorOA"
# REDGIF_TOKEN = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJodHRwczovL3d3dy5yZWRnaWZzLmNvbS8iLCJpYXQiOjE2NzI0NzYxNDcsImV4cCI6MTY3MjU2MjU0Nywic3ViIjoiY2xpZW50LzE4MjNjMzFmN2QzLTc0NWEtNjU4OS0wMDA1LWQ4ZThmZTBhNDRjMiIsInNjb3BlcyI6InJlYWQiLCJ2YWxpZF9hZGRyIjoiNjkuMTE1LjEyNi4xMjgiLCJ2YWxpZF9hZ2VudCI6Ik1vemlsbGEvNS4wIChYMTE7IExpbnV4IHg4Nl82NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzk2LjAuNDY2NC40NSBTYWZhcmkvNTM3LjM2In0.o_exS8cVZ3kuByKYLrZwkag2LI4_3DvoEc4VVQX3wIkViRpLtIg1NAwx3imHnlujuk4v3cDXCVDhZYl7F8hRjHW-wHJ4g3qS_8rMbdv-o5ZBujEdN7L6DS0gLkaCcAifRuPGy4n6T6eTHLluQsYzSZuQgP5D-zKWHGFcu8oU0WFnEq8PXsLwQbKm5VFiydyRAiEQ7qRYhFnG4ERMU2YZf5gm1JtVOBZfnqNQSK3h7obPfxUZ3aaSIgDWx_iAcl65y1k52Xv0Ah8560cJX21_gKMkDUgcYkwRerxgqRBreZZJToZfZEfG50jJGNTU7AgoDYEm6yA1vZtA37Wh7WorOA"
REDGIF_TOKEN = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJodHRwczovL3d3dy5yZWRnaWZzLmNvbS8iLCJpYXQiOjE2NzgxNTAzMjIsImV4cCI6MTY3ODIzNjcyMiwic3ViIjoiY2xpZW50LzE4MjNjMzFmN2QzLTc0NWEtNjU4OS0wMDA1LWQ4ZThmZTBhNDRjMiIsInNjb3BlcyI6InJlYWQiLCJ2YWxpZF9hZGRyIjoiNjkuMTI0Ljk2LjE3NyIsInZhbGlkX2FnZW50IjoiTW96aWxsYS81LjAgKFgxMTsgTGludXggeDg2XzY0KSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvOTYuMC40NjY0LjQ1IFNhZmFyaS81MzcuMzYiLCJyYXRlIjotMX0.PGKIeYkha6DXYBByG-02tTDwILZ2jn7WP9Qa3z7_enl0UOuTptr6v1SW_VmtUj6POaApT3qWGV5QORse5XLMKqcTdfwpGuj76gBmsCXy_iSCUzetkm5Tyiv6i3xQzIE47SDcy1zVckirNDX0yrB4dI90HMnm5Weow24EhCA0tjUAIPi55CEQPwsTVF9riaETBiOmKm_OomzuuW3eWs-5oLDbcghjoRIysbQzG1ZFefht8lob7FMASnKq9fvtN1aMRF0ZE4QY6DMKVWaC7DcdUC4EmB_9O1jPFHO4GO3BerhEaY9N56p3XJXOpvEjAstkpJlkQoGy9XNm1gtBczVLFQ"


def getRequest(url):
	if "redgifs" in url:
		return urllib.request.Request(
			url, 
			data=None, 
			headers={
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
				'Authorization': REDGIF_TOKEN
			}
		)	
	return urllib.request.Request(
		url, 
		data=None, 
		headers={
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
		}
	)

def urlRead(url):
	return urlopen(getRequest(url)).read()

def urlDownload(url, filepath):
	if os.path.isfile(filepath):
		print("file exists, skipping")
		return 
	with urllib.request.urlopen(getRequest(url)) as response, open(filepath, 'wb') as out_file:
		shutil.copyfileobj(response, out_file)


def NOOP(s):
	pass

def getFilename(url):
	return url.split('/')[-1].split('#')[0].split('?')[0]

def getAlbumFilename(albumId, i, url):
	return albumId + "-" +  ('%04d' % i) + "-" + getFilename(url)

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
	return links


def getRedgifUrl(linkUrl):
	gif_id = linkUrl.split("/")[-1]
	info = f"https://api.redgifs.com/v2/gifs/{gif_id}?views=yes&users=yes"
	resp = requests.get(url = info, headers={'Authorization': REDGIF_TOKEN})
	data = json.loads(resp.text)
	# print(data)

	url = data.get("gif", {}).get("urls", {}).get("hd", None)
	print(url)
	return url

	# data['gif']['urls']['hd']

	# return None
	# soup = BeautifulSoup(urlRead(linkUrl), "html.parser")
	# print(soup)
	# attributes = {"type":"application/ld+json"}
	# content = soup.find("script",attrs=attributes)

	# if content:
	# 	return json.loads(content.contents[0])["video"]["contentUrl"]
	# return None

def getGdnUrl(linkUrl):
	soup = BeautifulSoup(urlRead(linkUrl), "html.parser")
	return soup.find(id="mp4Source").get("src")




import requests, traceback, json, io, os, urllib.request, sys

API_URL_REDGIFS = 'https://api.redgifs.com/v2/gifs/'

class Downloader:
	def __init__(self, downloadFolder, dry = False, logMethod = NOOP):
		self.base = downloadFolder
		#self.opener = urllib.URLopener()
		self.dry = dry
		self.logMethod = logMethod

		if not os.path.exists(self.base):
			print("Creating directory: " + self.base)
			os.makedirs(self.base)

		albums = os.path.join(self.base, "albums")
		if not os.path.exists(albums):
			print("Creating directory: " + albums)
			os.makedirs(albums)

		print("Downloader initialized")

	def getFilepath(self, url, filename = None, extension = None, album = False, prefix = None):
		filename = filename if filename else getFilename(url)
		if prefix:
			filename = prefix + "-" + filename
		if extension:
			filename = os.path.splitext(filename)[0] + extension
			self.logMethod("Downloading as: " + filename)

		folder = self.base
		if album:
			folder = os.path.join(folder, "albums")
		filepath = os.path.join(folder, filename)
		return filepath

	def actuallyDownload(self, url, filename = None, extension = None, album = False, prefix = None):
		filepath = self.getFilepath(url, filename = filename, extension = extension, album = album, prefix = prefix)
		if not self.dry:
			urlDownload(url, filepath)
			# self.opener.retrieve(url, filepath)

	def downloadRedgifUrl(self, redgifs_url):
		self.logMethod(f"redgifs_url = {redgifs_url}")
		redgifs_id = redgifs_url.split("/")[-1]
		self.logMethod(f"redgifs_id = {redgifs_id}")

		sess = requests.Session()

		#Get RedGifs Video Meta
		# request = requests.get(API_URL_REDGIFS + redgifs_id)
		request = sess.get(API_URL_REDGIFS + redgifs_id, headers={'Authorization': REDGIF_TOKEN})
		
		if request is None:
			raise Exception("No response from api")
		else:
			rawData = request.json()
			# print(f"rawData = {rawData}")

			#Get HD video url
			hd_video_url = rawData['gif']['urls']['hd']
			self.logMethod(f"hd_video_url = {hd_video_url}")


			filepath = self.getFilepath(hd_video_url)
			self.logMethod(f"saving as {filepath}")

			with sess.get(hd_video_url, stream=True) as r:
				with open(filepath, 'wb') as f:
					for chunk in r.iter_content(chunk_size=8192): 
						# If you have chunk encoded response uncomment 
						# if and set chunk_size parameter to None.
						# if chunk: 
						f.write(chunk)

			# return hd_video_url

	def processImgurAlbum(self, albumUrl):
		albumId = getFilename(albumUrl)
		links = getImgurAlbumLinks(albumId)
		for i, imageUrl in enumerate(links):
			filename = getAlbumFilename(albumId, i, imageUrl)
			self.actuallyDownload(imageUrl, filename = filename, album = True)
			time.sleep(ALBUMSLEEP)
		self.logMethod("Downloaded imgur album of size " + str(len(links)))

	def processEroshareAlbum(self, albumUrl):
		albumId = getFilename(albumUrl)
		links = getEroshareAlbumLinks(albumId)
		for eItem in links:
			position = eItem[0]
			url = eItem[1]
			filename = getAlbumFilename(albumId, position, url)
			self.actuallyDownload(url, filename = filename, album = True)
			time.sleep(ALBUMSLEEP)
		self.logMethod("Downloaded eroshare album of size " + str(len(links)))

	def downloadUrl(self, linkUrl, prefix=None):
		result, error = False, None
		try:
			if "i.imgur.com" in linkUrl:
				if ".png" in linkUrl:
					self.actuallyDownload(linkUrl, extension = ".jpg")
				elif ".gifv" in linkUrl:
					self.actuallyDownload(linkUrl.replace(".gifv", ".mp4"))
				else:
					self.actuallyDownload(linkUrl)
				result = True

			elif "imgur.com" in linkUrl and "/a/" in linkUrl:
				self.processImgurAlbum(linkUrl)
				result = True

			elif "imgur.com" in linkUrl and "/gallery/" in linkUrl:
				self.processImgurAlbum(linkUrl)
				result = True

			elif "imgur.com" in linkUrl and "." not in getFilename(linkUrl):
				self.actuallyDownload(linkUrl.replace("imgur.com", "i.imgur.com") + ".jpg")
				result = True

			elif "gfycat" in linkUrl:
				if linkUrl.endswith(".mp4"):
					self.actuallyDownload(linkUrl)
				else:
					try:
						mp4Url = getGfycatUrl(linkUrl)
						self.logMethod("mp4Url for gfycat " + linkUrl + ": " + mp4Url)
						self.actuallyDownload(mp4Url)
					except:
						gdnUrl = linkUrl.replace("gfycat.com", "www.gifdeliverynetwork.com")
						mp4Url = getGdnUrl(gdnUrl)
						self.logMethod("mp4Url for gdn gfycat " + linkUrl + ": " + mp4Url)
						self.actuallyDownload(mp4Url)

				result = True

			elif "redgifs" in linkUrl:
				if not self.dry:
					self.downloadRedgifUrl(linkUrl)
					result = True
				# print("trying to get url")
				# mp4Url = getRedgifUrl(linkUrl)
				# print("mp4Url for redgif " + linkUrl + ": " + mp4Url)
				# self.logMethod("mp4Url for redgif " + linkUrl + ": " + mp4Url)
				# self.actuallyDownload(mp4Url)
				# result = True

			elif "eroshare" in linkUrl:
				self.processEroshareAlbum(linkUrl)
				result = True

			# https://i.reddituploads.com/1656217e668841e5b8cc202677de3b41?fit=max&h=1536&w=1536&s=da7a74bcf57c81979e6cbf2e9e4b25bf
			elif "i.reddituploads.com" in linkUrl:
				self.actuallyDownload(linkUrl, extension = ".jpg")
				result = True

			# https://preview.redd.it/8r8nf3acdzv81.png?width=1074&format=png&auto=webp&s=5e2c7bbc7fa1bc3bb8431a341d4ac2f278ccc1c3
			elif "preview.redd.it" in linkUrl:
				if ".png" in linkUrl:
					self.actuallyDownload(linkUrl, extension = ".jpg", prefix=prefix)
				else:
					self.actuallyDownload(linkUrl, prefix=prefix)
				result = True

			elif "reddit.com/gallery" in linkUrl:
				self.processRedditGallery(linkUrl)
				result = True

			elif linkUrl[-4:] in [".jpg", ".png", ".gif", ".mp4"]:
				self.actuallyDownload(linkUrl)
				result = True

			else:
				self.logMethod("Unhandled: " + linkUrl)
		except Exception as e:
			# traceback.print_exc()
			error = e

		return result, error


if __name__ == "__main__":
	# testUrl = "https://redgifs.com/ifr/breakableidleduckling"
	# testUrl = "https://redgifs.com/watch/viciousweakbonobo"
	testUrl = "https://redgifs.com/watch/beautifulopulentsaiga"
	# testUrl = "https://www.reddit.com/gallery/wj30e1"
	downloader = Downloader("test")
	result, error = downloader.downloadUrl(testUrl)
	print("Downloaded: ", result)
	print("Error: ", error)



# hd2gx4 - https://www.redgifs.com/watch/hollowabandonedarchaeopteryx
#        - ## error: 'gfyItem'

# hec9y3 - https://redgifs.com/watch/tendersmugcassowary
#        - ## error: 'gfyItem'
