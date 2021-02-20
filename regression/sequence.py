from common import *
import json
import unittest
import time

class TestSequence  (unittest.TestCase):

    def setUp(self):
        self.firstValue = "my value"
        self.secondValue = "my second value"
        # store data in sequence
        cmd = ["safe", "seq", "store", self.firstValue]
        out = runCmd(cmd)
        # get safe url
        self.sequrl = xorurlRe.findall(out)[-1]
        # append to safe url
        cmd = ["safe", "seq", "append", self.secondValue, self.sequrl]
        out = runCmd(cmd)

    def test_url_is_valid(self):
        msg = "%s does not start with safe://" % self.sequrl
        self.assertTrue(self.sequrl.startswith("safe://"), msg)

    def test_cat_defaults_to_latest_version(self):
        # version starts at zero
        cmd = ["safe", "cat", self.sequrl]
        out = runCmd(cmd)
        hasVersion = out.find("version 1") > -1
        self.assertTrue(hasVersion)

    def test_cat_value_is_correct(self):
        # returns correct value
        cmd = ["safe", "cat", self.sequrl]
        out = runCmd(cmd)
        hasValue = out.find(self.secondValue) > -1
        self.assertTrue(hasValue)

    def test_seq_v0(self):
        # fetching ?v=0
        cmd = ["safe", "cat", self.sequrl + "?v=0"]
        out = runCmd(cmd)
        hasVersion = out.find("version 0") > -1
        self.assertTrue(hasVersion)
        hasValue = out.find("my value") > -1
        self.assertTrue(hasValue)

    def test_seq_v1(self):
        # fetching ?v=1
        cmd = ["safe", "cat", self.sequrl + "?v=1"]
        out = runCmd(cmd)
        hasVersion = out.find("version 1") > -1
        self.assertTrue(hasVersion)
        hasValue = out.find("my second value") > -1
        self.assertTrue(hasValue)

    def test_json_flag(self):
        # check --json format flag
        cmd = ["safe", "cat", "--json", self.sequrl]
        out = runCmd(cmd)
        self.assertEqual(out, expectedJson % self.sequrl)

    def test_hexdump_flag(self):
        # check --hexdump format flag
        cmd = ["safe", "cat", "--hexdump", self.sequrl]
        out = runCmd(cmd)
        self.assertEqual(out, expectedHex % self.sequrl)

    def test_x_flag(self):
        # check -x format flag
        cmd = ["safe", "cat", "-x", self.sequrl]
        out = runCmd(cmd)
        self.assertEqual(out, expectedHex % self.sequrl)

    def test_o_json_flag(self):
        # check -o json format option
        cmd = ["safe", "cat", "-o", "json", self.sequrl]
        out = runCmd(cmd)
        self.assertEqual(out, expectedJson % self.sequrl)

    def test_o_jsoncompact_flag(self):
        # check -o jsoncompact format option
        cmd = ["safe", "cat", "-o", "jsoncompact", self.sequrl]
        out = runCmd(cmd)
        self.assertEqual(out, expectedJsonCompact % self.sequrl)

    def test_o_yaml_flag(self):
        # check -o yaml format option
        cmd = ["safe", "cat", "-o", "yaml", self.sequrl]
        out = runCmd(cmd)
        self.assertEqual(out, expectedYaml % self.sequrl)

    @unittest.skip("causes panic, https://github.com/maidsafe/sn_api/issues/674")
    def test_large_total_seq_size(self):
        # To get a sequence up over 1 MB in data we must do a large
        # value repeatedly. Values are limited in size by the OS.
        # More info here:
        # https://www.in-ulm.de/~mascheck/various/argmax/
        # xargs --show-limits
        # 99 * 131071 = 12976029 = 12.37 MiB
        loops = 99
        size = 131072-1
        for i in range(0,loops):
            largestAllowedArg = (("%s." % i)*size)[:size]
            print("Running %s of %s large appends" % (i+1, loops))
            cmd = ["safe", "seq", "append", largestAllowedArg, self.sequrl]
            out = runCmd(cmd)
            hasNoError = out.find("rror") == -1
            self.assertTrue(hasNoError)
            #time.sleep(60)

    def test_public_seq_not_encrypted(self):
        self.seq_encryption(False)

    @unittest.skip("private data is not encrypted yet")
    def test_private_seq_is_encrypted(self):
        self.seq_encryption(True)

    def seq_encryption(self, isPrivate):
        # count files stored by nodes
        oldfilelist = set(getListOfNodeFiles())
        self.assertTrue(len(oldfilelist) > 0)
        # store data in sequence
        seqentry = randStr(25)
        cmd = ["safe", "seq", "store", seqentry]
        if isPrivate:
            cmd.append("--private")
        out = runCmd(cmd)
        # get the filename
        sequrl = xorurlRe.findall(out)[-1]
        cmd = ["safe", "dog", "--json", sequrl]
        out = runCmd(cmd)
        j = json.loads(out)
        key = "PublicSequence"
        if isPrivate:
            key = "PrivateSequence"
        xornamelist = j[1][0][key]["xorname"]
        xorname = "".join(["%0.2x" % x for x in xornamelist])
        # check there are new files stored by the nodes
        newfilelist = set(getListOfNodeFiles())
        newfiles = newfilelist.difference(oldfilelist)
        self.assertTrue(len(newfiles) > 0)
        # check the new files includes the new sequence xorname
        newfilenameHasXorname = False
        for filename in newfiles:
            if filename.find(xorname) > -1:
                newfilenameHasXorname = True
                break
        self.assertTrue(newfilenameHasXorname)
        # check if any file contains the data.
        bseqentry = str.encode(seqentry)
        for filename in newfiles:
            if filename.find(xorname) == -1:
                continue
            f = open(filename, 'rb')
            content = f.read()
            f.close()
            valueIsInContent = content.find(bseqentry) > -1
            if isPrivate:
                # If it's private the data should be encrypted and not be
                # found in the node file content.
                self.assertFalse(valueIsInContent)
            else:
                self.assertTrue(valueIsInContent)

expectedJson = """[
  "%s",
  [
    109,
    121,
    32,
    115,
    101,
    99,
    111,
    110,
    100,
    32,
    118,
    97,
    108,
    117,
    101
  ]
]
"""

expectedJsonCompact = """["%s",[109,121,32,115,101,99,111,110,100,32,118,97,108,117,101]]
"""

expectedHex = """Public Sequence (version 1) at "%s":
Length: 15 (0xf) bytes
0000:   6d 79 20 73  65 63 6f 6e  64 20 76 61  6c 75 65      my second value
"""

expectedYaml = """---
- "%s"
- - 109
  - 121
  - 32
  - 115
  - 101
  - 99
  - 111
  - 110
  - 100
  - 32
  - 118
  - 97
  - 108
  - 117
  - 101

"""

if __name__ == '__main__':
    print(startupMsg)
    unittest.main()
