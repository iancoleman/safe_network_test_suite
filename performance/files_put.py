from common import *
import os
import math
import statistics
import time

total_tests = 100
file_size_in_bytes = 2000

def secondsForPut(size_in_bytes):
    fname = "/tmp/data_%s.bin" % randStr(10)
    f = open(fname, 'w')
    content = randStr(size_in_bytes)
    f.write(content)
    f.close()
    start = time.time()
    cmd = ["safe", "files", "put", fname]
    out = runCmd(cmd)
    end = time.time()
    xorurls = xorurlRe.findall(out)
    if len(xorurls) != 2:
        print("Error timing files put: %s" % out)
        return None
    return end - start

times = []
for i in range(0, total_tests):
    print("Putting %s of %s" % (i+1, total_tests))
    t = secondsForPut(file_size_in_bytes)
    times.append(t)
quartiles = statistics.quantiles(times, n=4)
deciles = statistics.quantiles(times, n=10)

# report results

print("")
print("Full data")
print(",\n".join([str(t) for t in times]))

# Calculate slowdown
# How much do uploads slow down over time?
# Ideally no slowdown at all.
# slowdown = avg(last ten uploads) / avg(first ten uploads)
# avoid overlap; if less than 20 uploads, use
# avg(last ten percent) / avg(first ten percent)
sd_start_index = 10
sd_mid_index = math.floor(len(times)/2)-5
sd_mid_size = 10
if len(times) < 20:
    sd_start_index = math.ceil(len(times)*0.1)
    sd_mid_index = math.floor((len(times)-sd_start_index)/2)
    sd_mid_size = sd_start_index
sd_end_index = -1 * sd_start_index
early_avg = statistics.mean(times[:sd_start_index])
mid_avg = statistics.mean(times[sd_mid_index:sd_mid_index+sd_mid_size])
late_avg = statistics.mean(times[sd_end_index:])
slowdown = late_avg / early_avg
slowdown_type = "unknown"
slowdown_msg = "unknown whether slowdown gets better/worse/same over time"
shape_factor = (late_avg - mid_avg) / (mid_avg - early_avg)
if shape_factor > 2:
    slowdown_type = "exponential"
    slowdown_msg = "uploads are getting slower at an increasing rate over time"
elif shape_factor <= 2 and shape_factor > 0.5:
    slowdown_type = "linear"
    slowdown_msg = "uploads are getting progressively slower at a steady rate"
elif shape_factor <= 0.5 and shape_factor > 0.1:
    slowdown_type = "logarithimic"
    slowdown_msg = "uploads are getting slower, but less dramatically over time"
else:
    slowdown_type = "no slowdown"
    slowdown_msg = "uploads are not getting slower"

# report results

print("")
try:
    print(runCmd([os.path.expanduser("~/.safe/node/sn_node"), "--version"]))
    print(runCmd(["safe", "--version"]))
except:
    print("Unable to print safe / sn_node versions")

print("Time to upload %s files" % total_tests)
print("of size %s bytes" % file_size_in_bytes)
print("measured in seconds.")
print("Ideally they should all take about the same amount of time.")
print("")
print("min,%s" % min(times))
print("tenth percential,%s" % deciles[0])
print("first quartile,%s" % quartiles[0])
print("median,%s" % statistics.median(times))
print("average,%s" % statistics.mean(times))
print("third quartile,%s" % quartiles[2])
print("nintieth percentile,%s" % deciles[8])
print("max,%s" % max(times))
print("")
print("slowdown factor: %s" % slowdown)
print("more than 1 indicates network slows down over time.")
print("less than 1 indicates network speeds up over time.")
print("slowdown type: %s" % slowdown_type)
print("%s" % slowdown_msg)
print("slowdown factor is calculated using:")
print("avg(late uploads) / avg(early uploads)")
print("using last ten uploads and first ten uploads")
print("or one tenth of the uploads if less than total 20 uploads")
