from common import *
import os
import pathlib
import subprocess
import unittest

class File():

    def __init__(self):
        self.content = randStr(10)
        self.filename = "index.html"
        self.filedir = "/tmp/test_%s" % randStr(4)
        self.fileLocation = os.path.join(self.filedir, self.filename)
        pathlib.Path(self.filedir).mkdir(parents=True, exist_ok=True)
        f = open(self.fileLocation, 'w')
        f.write(self.content)
        f.close()

class TestNrs(unittest.TestCase):

    def setUp(self):
        # create some content
        self.files = []
        for i in range(0,2):
            f = File()
            # save it to the network
            cmd = ["safe", "files", "put", f.fileLocation]
            out = runCmd(cmd)
            xorurls = xorurlRe.findall(out)
            self.assertEqual(len(xorurls), 2)
            f.filescontainerXorurl = xorurls[0]
            f.linkxor = f.filescontainerXorurl + "?v=0"
            f.dataXorurl = xorurls[1]
            # keep the result for use in tests
            self.files.append(f)

    def test_basic_nrs(self):
        files = self.files
        # create an nrs
        nrsname = "my_nrs_name_%s" % randStr(4)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, nrsname]
        runCmd(cmd)
        # fetch from the nrs
        cmd = ["safe", "cat", "safe://%s/%s" % (nrsname, files[0].filename)]
        out = runCmd(cmd)
        self.assertEqual(out, files[0].content)
        # index.html will be fetched if no filename specified
        # seems to only be true for the browser
        """
        cmd = ["safe", "cat", "safe://%s" % nrsname]
        out = runCmd(cmd)
        self.assertEqual(out, files[0].content)
        """
        # add subname
        nrssubname = "www.%s" % nrsname
        cmd = ["safe", "nrs", "add", "--link", files[0].linkxor, nrssubname]
        runCmd(cmd)
        # fetch from the nrs subname
        cmd = ["safe", "cat", "safe://%s/%s" % (nrssubname, files[0].filename)]
        out = runCmd(cmd)
        self.assertEqual(out, files[0].content)
        # update link for name
        cmd = ["safe", "nrs", "add", "--link", files[1].linkxor, nrsname]
        runCmd(cmd)
        # check the nrs points to the new content
        cmd = ["safe", "cat", "safe://%s/%s" % (nrsname, files[1].filename)]
        out = runCmd(cmd)
        self.assertEqual(out, files[1].content)
        # remove name
        cmd = ["safe", "nrs", "remove", nrsname]
        out = runCmd(cmd)
        # content cannot be fetched from removed name
        # it throws an error
        cmd = ["safe", "cat", "safe://%s/%s" % (nrsname, files[1].filename)]
        out = runCmd(cmd)
        self.assertTrue(out.find("No link found for subname") > -1)
        # after removing name can still fetch subname
        cmd = ["safe", "cat", "safe://%s/%s" % (nrssubname, files[0].filename)]
        out = runCmd(cmd)
        self.assertEqual(out, files[0].content)
        # remove subname
        cmd = ["safe", "nrs", "remove", nrssubname]
        out = runCmd(cmd)
        # content cannot be fetched from removed subname
        # it throws an error
        cmd = ["safe", "cat", "safe://%s/%s" % (nrssubname, files[0].filename)]
        out = runCmd(cmd)
        self.assertTrue(out.find("Sub name not found in NRS Map Container") > -1)
        # cannot create duplicate name
        dupnrsname = "my_nrs_name_%s" % randStr(4)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, dupnrsname]
        runCmd(cmd)
        out = runCmd(cmd) # this tries to create a duplicate name
        self.assertTrue(out.find("NRS name already exists") > -1)
        # cannot create duplicate subname
        dupnrssubname = "www.%s" % dupnrsname
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, dupnrssubname]
        runCmd(cmd)
        out = runCmd(cmd)
        self.assertTrue(out.find("NRS name already exists") > -1)
        # can remove name then create same name again
        # must use 'add' instead of 'create'
        # reuse original nrsname which has previously been removed
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, nrsname]
        out = runCmd(cmd)
        self.assertTrue(out.find("NRS name already exists. Please use 'nrs add' command") > -1)
        cmd = ["safe", "nrs", "add", "--link", files[0].linkxor, nrsname]
        runCmd(cmd)
        cmd = ["safe", "cat", "safe://%s/%s" % (nrsname, files[0].filename)]
        out = runCmd(cmd)
        self.assertEqual(out, files[0].content)
        # TODO
        # calling nrs create for a subname without an existing name
        # normally this requires nrs create <name> then nrs add <subname>
        # unicode normalization

    def test_nrs_chars(self):
        files = self.files
        # space in name
        spacednrs = "my nrs name with spaces %s" % randStr(4)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, spacednrs]
        out = runCmd(cmd)
        self.assertTrue(out.find("The URL cannot contain whitespace") > -1)
        # slash in name
        slashednrs = "my/nrs/name"
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, slashednrs]
        out = runCmd(cmd)
        self.assertTrue(out.find("The NRS name/subname cannot contain a slash") > -1)
        # backslash in name
        backslashednrs = "my\\nrs\\name"
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, backslashednrs]
        out = runCmd(cmd)
        self.assertTrue(out.find("Problem parsing the URL") > -1)
        self.assertTrue(out.find("invalid domain character") > -1)
        # utf-8 in nrsname
        monkey = b'\xf0\x9f\x90\x92'
        monkeynrs = "%s_%s" % (monkey.decode("utf-8"), randStr(4))
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, monkeynrs]
        runCmd(cmd)
        cmd = ["safe", "cat", "safe://%s/%s" % (monkeynrs, files[0].filename)]
        out = runCmd(cmd)
        self.assertEqual(out, files[0].content)
        # homoglyphs in nrsname
        # https://www.unicode.org/reports/tr36/#TableMixedScriptSpoofing
        # Would be neat to do a visual comparison to show they look identical
        withascii = "top"
        withgreek = b't\xce\xbfp'.decode("utf-8") # tοp with o as greek omicron
        salt = randStr(4)
        original = "%s_%s" % (withascii, salt)
        spoofed = "%s_%s" % (withgreek, salt)
        self.assertTrue(original != spoofed)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, original]
        runCmd(cmd)
        cmd = ["safe", "nrs", "create", "--link", files[1].linkxor, spoofed]
        runCmd(cmd)
        cmd = ["safe", "cat", "safe://%s/%s" % (original, files[0].filename)]
        outOriginal = runCmd(cmd)
        self.assertEqual(outOriginal, files[0].content)
        cmd = ["safe", "cat", "safe://%s/%s" % (spoofed, files[1].filename)]
        outSpoofed = runCmd(cmd)
        self.assertEqual(outSpoofed, files[1].content)
        self.assertTrue(outOriginal != outSpoofed)
        # combining characters
        zstroke = b'\xc6\xb6'.decode("utf-8")
        combining = b'\xcc\xb5z'.decode("utf-8") # z + combining bar
        salt = randStr(4)
        original = "%s_%s" % (zstroke, salt)
        spoofed = "%s_%s" % (combining, salt)
        self.assertTrue(original != spoofed)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, original]
        runCmd(cmd)
        cmd = ["safe", "nrs", "create", "--link", files[1].linkxor, spoofed]
        runCmd(cmd)
        cmd = ["safe", "cat", "safe://%s/%s" % (original, files[0].filename)]
        outOriginal = runCmd(cmd)
        self.assertEqual(outOriginal, files[0].content)
        cmd = ["safe", "cat", "safe://%s/%s" % (spoofed, files[1].filename)]
        outSpoofed = runCmd(cmd)
        self.assertEqual(outSpoofed, files[1].content)
        self.assertTrue(outOriginal != outSpoofed)
        # zero width space
        zws = b'a\xE2\x80\x8Bb_%s'.decode("utf-8") % randStr(4)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, zws]
        out = runCmd(cmd)
        self.assertTrue(out.find("The URL cannot contain invalid characters") > -1)
        # nonbreaking space
        nbsp = b'a\xc2\xa0b_%s'.decode("utf-8") % randStr(4)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, nbsp]
        out = runCmd(cmd)
        self.assertTrue(out.find("The URL cannot contain whitespace") > -1)
        # tab
        tab = "a\x09b_%s" % randStr(4)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, tab]
        out = runCmd(cmd)
        self.assertTrue(out.find("The URL cannot contain whitespace") > -1)
        # newline
        nl = "a\x0ab_%s" % randStr(4)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, nl]
        out = runCmd(cmd)
        self.assertTrue(out.find("The URL cannot contain whitespace") > -1)
        # carriage return
        cr = "a\x0db_%s" % randStr(4)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, cr]
        out = runCmd(cmd)
        self.assertTrue(out.find("The URL cannot contain whitespace") > -1)
        # rtl chars
        arabic = b'\xd8\xb4\xd8\xa8\xd9\x83\xd8\xa9'.decode("utf-8")
        salt = randStr(4)
        rtl = "%s_%s" % (arabic, salt)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, rtl]
        runCmd(cmd)
        cmd = ["safe", "cat", "safe://%s/%s" % (rtl, files[0].filename)]
        out = runCmd(cmd)
        self.assertEqual(out, files[0].content)
        # rtl control chars
        # both names look like safe://,,! but the second one is rtl
        ltr = ",,!"
        rtl = b'\xe2\x80\xab!,,\xe2\x80\xac'.decode("utf-8")
        salt = randStr(4)
        original = "%s_%s" % (ltr, salt)
        spoofed = "%s_%s" % (rtl, salt)
        self.assertTrue(original != spoofed)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, original]
        runCmd(cmd)
        cmd = ["safe", "nrs", "create", "--link", files[1].linkxor, spoofed]
        runCmd(cmd)
        cmd = ["safe", "cat", "safe://%s/%s" % (original, files[0].filename)]
        outOriginal = runCmd(cmd)
        self.assertEqual(outOriginal, files[0].content)
        cmd = ["safe", "cat", "safe://%s/%s" % (spoofed, files[1].filename)]
        outSpoofed = runCmd(cmd)
        self.assertEqual(outSpoofed, files[1].content)
        self.assertTrue(outOriginal != outSpoofed)

    def test_nrs_length(self):
        files = self.files
        # Labels must be 63 characters or less.
        # see https://www.ietf.org/rfc/rfc1035.txt
        longname = ".".join([randStr(63) for i in range(0,4)]) # 255 chars
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, longname]
        runCmd(cmd)
        cmd = ["safe", "cat", "safe://%s/%s" % (longname, files[0].filename)]
        outOriginal = runCmd(cmd)
        self.assertEqual(outOriginal, files[0].content)
        # Label more than 64 characters gives an error
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, randStr(64)]
        out = runCmd(cmd)
        self.assertTrue(out.find("Label is 64 chars, must be no more than 63") > -1)
        # Names more than 255 characters throws an error
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, randStr(256)]
        out = runCmd(cmd)
        self.assertTrue(out.find("Name is 256 chars, must be no more than 255") > -1)
        # three good subnames, one subname too long
        longname = randStr(64) + "." + randStr(63) + "." + randStr(62) + "." + randStr(61) # 253 chars
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, longname]
        out = runCmd(cmd)
        self.assertTrue(out.find("Label is 64 chars, must be no more than 63") > -1)
        # maximum subnames
        # currently failing
        # waiting on https://github.com/maidsafe/sn_api/issues/704
        firstname = randStr(1)
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, firstname]
        runCmd(cmd)
        longname = ".".join([randStr(1) for i in range(0,42)]) + "." + firstname # 255 chars
        cmd = ["safe", "nrs", "add", "--link", files[0].linkxor, longname]
        runCmd(cmd)
        cmd = ["safe", "cat", "safe://%s/%s" % (longname, files[0].filename)]
        out = runCmd(cmd)
        self.assertEqual(out, files[0].content)
        # too many subnames
        # which is really just a special case of more than 255 chars
        # see https://github.com/maidsafe/sn_api/pull/701
        longname = ".".join([randStr(1) for i in range(0,129)]) # 257 chars
        cmd = ["safe", "nrs", "create", "--link", files[0].linkxor, longname]
        out = runCmd(cmd)
        self.assertTrue(out.find("Label is 257 chars, must be no more than 255") > -1)

    def test_nrs_link_validity(self):
        files = self.files
        # link with non-existing version
        # https://github.com/maidsafe/sn_api/issues/206
        # currently failing
        nrsname = "invalid_version_%s" % randStr(4)
        invalidVersion = 999
        cmd = ["safe", "nrs", "create", "--link", files[0].filescontainerXorurl + "?v=%s" % invalidVersion, nrsname]
        out = runCmd(cmd)
        self.assertTrue(out.find("? what is the error here ?") > -1)

    def test_nrs_ownership(self):
        # this test gave rise to
        # https://github.com/maidsafe/sn_api/pull/700
        # create users
        user1 = "user1_%s" % randStr(6)
        user2 = "user2_%s" % randStr(6)
        createUser(user1, user1)
        createUser(user2, user2)
        # register nrs as first user
        logout()
        login(user1, user1)
        f = File()
        cmd = ["safe", "files", "put", f.fileLocation]
        out = runCmd(cmd)
        xorurls = xorurlRe.findall(out)
        f.filescontainerXorurl = xorurls[0]
        f.linkxor = f.filescontainerXorurl + "?v=0"
        f.dataXorurl = xorurls[1]
        # create an nrs for this content
        nrsname = "my_nrs_name_%s" % randStr(4)
        cmd = ["safe", "nrs", "create", "--link", f.linkxor, nrsname]
        runCmd(cmd)
        # cannot update an nrsname that we don't own
        logout()
        login(user2, user2)
        cmd = ["safe", "nrs", "add", "--link", f.linkxor, nrsname]
        out = runCmd(cmd)
        self.assertTrue(out.find("Failed to append to Sequence: NetworkDataError(InvalidSignature)") > -1)
        # cannot delete nrsname that we don't own
        cmd = ["safe", "nrs", "remove", nrsname]
        out = runCmd(cmd)
        self.assertTrue(out.find("Failed to append to Sequence: NetworkDataError(InvalidSignature)") > -1)

if __name__ == '__main__':
    print(startupMsg)
    unittest.main()
