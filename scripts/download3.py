import argparse
import praw
import time

import downloaders3
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

logfile = open('output.log', 'a')
downloadFolder = "downloads-" + time.strftime("%Y-%m-%d")

skippedUrls = []
errorMessages = []
successSaved = 0
albumTransferred = 0

SUCCESS = 1
SKIPPED = 2

parser=argparse.ArgumentParser()
parser.add_argument('--file', help='File with urls')

def log(s):
	try:
		logfile.write(s + "\n")
	except:
		print("#####################################################")
	print(s)

def logP(s):
	s = "       - " + s
	log(s)

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

def tryProcessBatch(downloader):
	numSuccess = 0
	linksSkipped = []
	linksErrored = []

	print("------------------------------------------------------------------------")
	print("Starting batch")

	saved = reddit.user.me().saved(limit=500)

	print("Got batch of saved links")

	linksTried = 0
	for link in saved:
		linkId = link.id
		if type(link).__name__ == "Comment" and link.author is None:
			unsaveRemoved(link)
			continue


		if link.subreddit == "doujinshi":
			log(linkId + " - skipping doujinshi")
			linksSkipped.append(link.id + " - Skipping doujinshi")
			continue

		try:
			linkUrl = link.url
		except:
			log(linkId + " - not a link")
			linksSkipped.append(link.id + " - Not a link")
			continue

		log("")
		log(linkId + " - " + linkUrl)

		linksTried += 1
		downloaded, error = downloader.downloadUrl(linkUrl)

		if downloaded:
			logP("Success")
			unsave(link)
			numSuccess += 1
		elif error:
			logP("## error: " + str(error))
			linksErrored.append(link.id + " " + link.url + ": " + str(error))
		else:
			# skipped
			logP("Can't handle, skipped")
			linksSkipped.append(link.id + " " + link.url + " - Skipped")


	print("Done with batch, saved {} / {}".format(numSuccess, linksTried))

	for link in linksSkipped:
		print(link)

	return numSuccess, linksSkipped, linksErrored


if __name__ == "__main__":
	log("------------------------------------------------------------------------")
	log("---" + time.strftime("%c"))

	args=parser.parse_args()

	if args.file == None:
		downloader = downloaders3.Downloader(downloadFolder, dry = False, logMethod = logP)

		totalSaved = 0

		totalSkipped = set()
		totalErrored = set()

		while True:
			numSuccess, linksSkipped, linksErrored = tryProcessBatch(downloader)
			totalSkipped.update(linksSkipped)
			totalErrored.update(linksErrored)
			if numSuccess == 0:
				print("None saved in batch, stopping")
				break
			totalSaved += numSuccess

		print("#######################################################################")
		print("")
		print("Skipped", len(totalSkipped))
		print("")
		for link in sorted(list(totalSkipped), key=lambda s: str(s)[7:]):
			print(link)

		print("#######################################################################")
		print("")
		print("Errors", len(totalErrored))
		print("")
		for link in sorted(list(totalErrored), key=lambda s: str(s)[7:]):
			print(link)

		print("#######################################################################")
		print("")
		print("Saved", totalSaved)
		print("")

		print("#######################################################################")
		print("Done")
		logfile.close()

	else:
		urlfile = open(args.file, 'r')
		for url in urlfile:
			#print processUrl(url.strip())
			result = processUrlDry(url.strip())
			if result == SKIPPED:
				print(url)