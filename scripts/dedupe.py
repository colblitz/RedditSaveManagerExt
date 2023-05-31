import argparse
import os
import shutil
from difPy import dif

parser = argparse.ArgumentParser()
parser.add_argument('--user', help='Username to dedupe')
parser.add_argument('--delete', help='set true to actually delete')

def dedupe_user(user, delete=False):
	downloadFolder = "downloads-" + user
	fpath = os.getcwd() + "/" + downloadFolder

	sizes = {}
	dupes = {}
	numd = 0
	numf = 0
	for f in os.listdir(fpath):
		numf += 1
		filepath = fpath + "/" + f
		size = os.path.getsize(filepath)

		if size == 503:
			os.remove(filepath)
			numd += 1
			continue

		if size in sizes:
			if delete:
				os.remove(filepath)
				numd += 1
				continue
			if size not in dupes:
				dupes[size] = set()
			# add original and dupe
			dupes[size].add(sizes[size])
			dupes[size].add(filepath)
		else:
			sizes[size] = filepath

	print(f"{numf} files checked, {numd} files deleted")

	totaldupes = sum(len(s) for s in dupes.values())
	print(f"dupes: {len(dupes)}, total files to move: {totaldupes}")

	if totaldupes == 0:
		return

	dupebase = fpath + "/dupe-check"
	if not os.path.exists(dupebase):
		os.makedirs(dupebase)

	i = 0
	for s in dupes:
		for f in dupes[s]:
			fname = os.path.basename(f)
			newname = dupebase + "/" + '{0:04d}'.format(i) + "-" + fname
			shutil.copyfile(f, newname)
		i += 1
		if i % 100 == 0:
			print(i)

	if not delete:
		print(f"Done - check dupe-check folder, re-run with --delete true")

	search = dif(downloadFolder, show_progress=True)
	print(search.result)


# downloadFolder = "downloads-" + user
# if not os.path.exists(downloadFolder):
#     print(f"Creating directory: {downloadFolder}")
#     os.makedirs(downloadFolder)

# base = 'C:/Joe/temp/asdf'
# for f in os.listdir(base):
# 	fpath = base + "/" + f
# 	if os.path.isdir(fpath):
# ##        print "make archive: ", fpath + ".zip"
# ##        shutil.make_archive(fpath + ".zip", 'zip', fpath)
# 		dedupe_folder(fpath)

# dupebase = 'C:/Joe/temp/asdf/dupe-check'
# i = 0
# for s in dupes:
# 	for f in dupes[s]:
# 		fname = os.path.basename(f)
# 		newname = dupebase + "/" + '{0:04d}'.format(i) + "-" + fname
# 		shutil.copyfile(f, newname)
# 	i += 1
# 	if i % 100 == 0:
# 		print i
# print "done"


if __name__ == "__main__":
	args = parser.parse_args()
	if args.user == None:
		print("No user specified")
	else:
		do_delete = False
		if args.delete != None and args.delete == "true":
			do_delete = True

		if "," in args.user:
			print("Username has a comma")
		else:
			dedupe_user(args.user, delete=do_delete)



	print("Done")
