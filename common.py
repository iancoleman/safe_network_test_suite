import os
import pathlib
import random
import re
import string
import subprocess

startupMsg = """
This assumes you have already got a network running and have logged in.
This is easiest to achieve by running ./start_network.sh

The tests will begin running now. Please wait they can be slow...
"""

xorurlRe = re.compile("safe://[a-z0-9]+")

def runCmd(cmd_arr):
    prettycmd = ["\"%s\"" % a if a.find(" ") > -1 else a for a in cmd_arr]
    print("Running command: %s" % " ".join(prettycmd))
    proc = subprocess.Popen(cmd_arr, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (stdout, ignore) = proc.communicate()
    return stdout.decode("utf-8")

def randStr(length):
    return "".join(random.choice(string.ascii_letters) for _ in range(length))

def createUser(passphrase, password):
    # create credentials
    filelocation = filelocationFromPP(passphrase, password)
    content = '{"passphrase":"%s","password":"%s"}' % (passphrase, password)
    f = open(filelocation, 'w')
    f.write(content)
    f.close()
    # create new user
    cmd = ["safe", "auth", "create", "--test-coins", "--config", filelocation]
    runCmd(cmd)

def login(passphrase, password):
    filelocation = filelocationFromPP(passphrase, password)
    cmd = ["safe", "auth", "unlock", "--self-auth", "--config", filelocation]
    runCmd(cmd)

def logout():
    cmd = ["safe", "auth", "lock"]
    runCmd(cmd)

def filelocationFromPP(passphrase, password):
    filename = "%s_%s.json" % (passphrase, password)
    filelocation = "/tmp/%s" % filename
    return filelocation

def getListOfNodeFiles():
    nodesDir = os.path.join(pathlib.Path.home(), ".safe", "node", "baby-fleming-nodes")
    filelist = []
    for root, dirs, filenames in os.walk(nodesDir):
        for filename in filenames:
            filelist.append(os.path.join(root, filename))
    return filelist
