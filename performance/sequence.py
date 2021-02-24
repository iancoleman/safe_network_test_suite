# Measure the time to do 50 appends in a row

from common import *
import os
import math
import statistics
import sys
import time

total_appends = 50

def secondsForAppend(sequrl):
    val = randStr(4)
    start = time.time()
    cmd = ["safe", "seq", "append", val, sequrl]
    out = runCmd(cmd)
    end = time.time()
    xorurls = xorurlRe.findall(out)
    if len(xorurls) != 1:
        print("Error timing sequence append: %s" % out)
        return None
    return end - start

# print some preliminary info
try:
    print(runCmd([os.path.expanduser("~/.safe/node/sn_node"), "--version"]))
    print(runCmd(["safe", "--version"]))
except:
    print("Unable to print safe / sn_node versions")

# store append times in this variable
times = []

# create a new user
userid = "user_%s" % randStr(4)
createUser(userid, userid)
login(userid, userid)

# create initial sequence, do not time it as we only measure append ops
val = randStr(4)
cmd = ["safe", "seq", "store", val]
out = runCmd(cmd)
xorurls = xorurlRe.findall(out)
if len(xorurls) != 1:
    print("Error storing sequence: %s" % out)
    sys.exit(1)
sequrl = xorurls[0]

# do append operations, timing each one
for i in range(0, total_appends):
    print("Appending %s of %s" % (i+1, total_appends))
    t = secondsForAppend(sequrl)
    if time is not None:
        times.append(t)

# calculate some stats
quartiles = statistics.quantiles(times, n=4)
deciles = statistics.quantiles(times, n=10)

# report results

print("")
print("Full data")
print(",\n".join([str(t) for t in times]))

print("")

print("Time to append %s times" % total_appends)
print("measured in seconds.")
print("")
print("min,%s" % min(times))
print("tenth percential,%s" % deciles[0])
print("first quartile,%s" % quartiles[0])
print("median,%s" % statistics.median(times))
print("average,%s" % statistics.mean(times))
print("third quartile,%s" % quartiles[2])
print("nintieth percentile,%s" % deciles[8])
print("max,%s" % max(times))
print("total,%s" % sum(times))
print("\n\n")
