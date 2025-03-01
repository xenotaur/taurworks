#!/usr/bin/python
import sys
import os
import time
import shutil

HOME_DIR = os.path.expanduser("~")
assert os.path.exists(HOME_DIR)

DOWNLOADS = os.path.join(HOME_DIR, "Pictures", "Downloads")
FILEPHOTO = os.path.join(HOME_DIR, "Pictures", "Photos")


def Error(message):
  print message
  sys.exit(1)

def IsValidDirectory(d):
  return os.path.exists(d) and os.path.isdir(d)

def ListDirectory(d, name="Directory"):
  if IsValidDirectory(d):
    print "%s Exists" % name
    for file in os.listdir(d):
      absolute = os.path.join(d, file)
      if os.path.isdir(absolute): 
        print "skipping %s: directory" % absolute
      else:
        MoveFile(absolute)
  else:
    Error("%s not found, exiting" % name)

def MoveFile(file):
  if os.path.exists(file) and not os.path.isdir(file):
    (year, month, day) = time.localtime(os.stat(file).st_mtime)[0:3]
    year = "%04d" % year
    month = "%02d" % month
    day = "%02d" % day
    basename = os.path.basename(file)
    target_path = os.path.join(FILEPHOTO, year, month, day)
    target_file = os.path.join(target_path, basename)
    if not os.path.exists(target_path):
      os.makedirs(target_path)
    if not os.path.isdir(target_path):
      print "skipping %s: target directory %s is a file" % (file, target_path)
    else:
      if os.path.exists(target_file):
        print "skipping %s: target file %s exists" % (file, target_file)
      else:
        print "moving %s: to target %s" % (file, target_file)
        shutil.move(file, target_file)
  else:
    print "skipping %s: not a valid file" % file

print IsValidDirectory(FILEPHOTO)
ListDirectory(DOWNLOADS)
