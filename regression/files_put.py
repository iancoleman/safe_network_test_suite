from common import *
import subprocess
import time
import unittest

class TestFilesPut  (unittest.TestCase):

    def test_basic_put(self):
        xorurls, localContent = safeFilesPut(5000)
        # two xorurls
        # first is the filescontainer
        # second is the file
        self.assertEqual(len(xorurls), 2)
        filescontainerXorurl = xorurls[0]
        fileXorurl = xorurls[1]
        # check the content matches
        remoteContent = safeCat(fileXorurl)
        self.assertEqual(localContent, remoteContent)

def safeFilesPut(size_bytes):
    filename = "/tmp/data_%s.bin" % size_bytes
    cmd = ["dd", "if=/dev/urandom", "of=%s" % filename, "bs=%s" % size_bytes, "count=1"]
    out = runCmd(cmd)
    cmd = ["safe", "files", "put", filename]
    out = runCmd(cmd)
    xorurls = xorurlRe.findall(out)
    f = open(filename, 'rb')
    content = f.read()
    f.close()
    return xorurls, content

def safeCat(xorurl):
    cmd = ["safe", "cat", xorurl]
    # can't use runCmd here because output is bytes, cannot decode as utf-8
    out = subprocess.check_output(cmd)
    return out

if __name__ == '__main__':
    print(startupMsg)
    unittest.main()
