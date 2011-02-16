#! /usr/bin/env python
#
# This little tool is a very simple command-line tweeter.  That is, it
# allows you to send a twitter update to a given user account.  It doesn't
# do anything else.  Well, actually, it also shortens any links
# automatically in the message you submit, but that's all.
#
# Copyright (c) 2011, Jan Schaumann. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL <COPYRIGHT HOLDER> OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Originally written by Jan Schaumann <jschauma@netmeister.org> in January 2011.

import getopt
import os
import re
import sys
import tweepy
import urllib

###
### Classes
###

class Tweet(object):
    """A very simple twitter updater."""

    EXIT_ERROR = 1
    EXIT_SUCCESS = 0

    MAXCHARS = 140

    URL_SHORTENER = "http://is.gd/api.php?longurl="

    def __init__(self):
        """Construct a Tweet object with default values."""

        self.__opts = {
                    "cfg_file" : os.path.expanduser("~/.tweetrc"),
                    "shorten" : True,
                    "truncate" : False,
                    "ids" : [],
                    "user" : ""
                 }
        self.auth = None
        self.api = None
        self.api_credentials = {}
        self.users = {}
        self.msg = ""


    class Usage(Exception):
        """A simple exception that provides a usage statement and a return code."""

        def __init__(self, rval):
            self.err = rval
            self.msg = 'Usage: %s [-Sht] [-r id] -u user\n' % os.path.basename(sys.argv[0])
            self.msg += '\t-S       do not shorten links\n'
            self.msg += '\t-h       print this message and exit\n'
            self.msg += '\t-r id    retweet given message\n'
            self.msg += '\t-t       truncate messages\n'
            self.msg += '\t-u user  tweet as this user\n'


    def getAccessInfo(self, user):
        """Initialize OAuth Access Info (if not found in the configuration file)."""

        self.auth = tweepy.OAuthHandler(self.api_credentials['key'], self.api_credentials['secret'])

        if self.users.has_key(user):
            return

        auth_url = self.auth.get_authorization_url(True)
        print "Access credentials for %s not found in %s." % (user, self.getOpt("cfg_file"))
        print "Please log in on twitter.com as %s and then go to: " % user
        print "  " + auth_url
        verifier = raw_input("Enter PIN: ").strip()
        self.auth.get_access_token(verifier)

        self.users[user] = {
            "key" : self.auth.access_token.key,
            "secret" : self.auth.access_token.secret
        }

        cfile = self.getOpt("cfg_file")
        try:
            f = file(cfile, "a")
            f.write("%s_key = %s\n" % (user, self.auth.access_token.key))
            f.write("%s_secret = %s\n" % (user, self.auth.access_token.secret))
            f.close()
        except IOError, e:
            sys.stderr.write("Unable to write to config file '%s': %s\n" % \
                (cfile, e.strerror))
            raise


    def getOpt(self, opt):
        """Retrieve the given configuration option.

        Returns:
            The value for the given option if it exists, None otherwise.
        """

        try:
            r = self.__opts[opt]
        except ValueError:
            r = None

        return r


    def parseConfig(self, cfile):
        """Parse the configuration file and set appropriate variables.

        This function may throw an exception if it can't read or parse the
        configuration file (for any reason).

        Arguments:
            cfile -- the configuration file to parse

        Aborts:
            if we can't access the config file
        """

        try:
            f = file(cfile)
        except IOError, e:
            sys.stderr.write("Unable to open config file '%s': %s\n" % \
                (cfile, e.strerror))
            sys.exit(self.EXIT_ERROR)

        key_pattern = re.compile('^(?P<username>[^#]+)_key\s*=\s*(?P<key>.+)')
        secret_pattern = re.compile('^(?P<username>[^#]+)_secret\s*=\s*(?P<secret>.+)')
        for line in f.readlines():
            line = line.strip()
            key_match = key_pattern.match(line)
            if key_match:
                user = key_match.group('username')
                if user == "<api>":
                    self.api_credentials['key'] = key_match.group('key')
                else:
                    if self.users.has_key(user):
                        self.users[user]['key'] = key_match.group('key')
                    else:
                        self.users[user] = {
                            "key" : key_match.group('key')
                        }

            secret_match = secret_pattern.match(line)
            if secret_match:
                user = secret_match.group('username')
                if user == "<api>":
                    self.api_credentials['secret'] = secret_match.group('secret')
                else:
                    if self.users.has_key(user):
                        self.users[user]['secret'] = secret_match.group('secret')
                    else:
                        self.users[user] = {
                            "secret" : secret_match.group('secret')
                        }


    def parseOptions(self, inargs):
        """Parse given command-line options and set appropriate attributes.

        Arguments:
            inargs -- arguments to parse

        Raises:
            Usage -- if '-h' or invalid command-line args are given
        """

        try:
            opts, args = getopt.getopt(inargs, "Shr:tu:")
        except getopt.GetoptError:
            raise self.Usage(self.EXIT_ERROR)

        for o, a in opts:
            if o in ("-S"):
                self.setOpt("shorten", False)
            if o in ("-h"):
                raise self.Usage(self.EXIT_SUCCESS)
            if o in ("-r"):
                ids = self.getOpt("ids")
                ids.append(a)
                self.setOpt("ids", ids)
            if o in ("-t"):
                self.setOpt("truncate", True)
            if o in ("-u"):
                self.setOpt("user", a)

        if not self.getOpt("user") or args:
            raise self.Usage(self.EXIT_ERROR)


    def readInput(self):
        """Read the input from stdin; if appropriate, shorten URLs.

        Arguments: none

        Returns:
            the given input, possibly modified

        Aborts:
            if given input is > 140 characters
        """

        msg = sys.stdin.readline().strip()
        if self.getOpt("shorten"):
            msg = self.shorten(msg)
        l=len(msg)
        if l > self.MAXCHARS:
            if self.getOpt("truncate"):
                msg = ' '.join(msg[:136].split(' ')[0:-1]) + '...'
            else:
                sys.stderr.write("Message too long (%d). Trim by %d.\n" \
                    % (l, (l - self.MAXCHARS)))
                sys.exit(self.EXIT_ERROR)

        return msg


    def setOpt(self, opt, val):
        """Set the given option to the provided value"""

        self.__opts[opt] = val


    def shorten(self, msg):
        """Shorten any URLs found in the given string using is.gd"""

        pattern = re.compile('^(ftp|https?)://.+$')

        words = []

        for word in msg.split():
            if pattern.match(word):
                quoted = urllib.quote(word)
                short = urllib.urlopen(self.URL_SHORTENER + quoted).read()
                words.append(short)
            else:
                words.append(word)

        return " ".join(words)


    def setupApi(self, user):
        """Create the object's api"""

        key = self.users[user]["key"]
        secret = self.users[user]["secret"]
        self.auth.set_access_token(key, secret)

        self.api = tweepy.API(self.auth)



    def retweet(self, ids):
        """Re-Tweet the given message."""

        for msg in ids:
            self.api.retweet(msg)


    def tweet(self):
        """Read and then tweet the message"""

        msg = self.readInput()
        self.api.update_status(msg)


    def verifyConfig(self):
        """Verify that we have api credentials."""

        if (not (self.api_credentials.has_key("key") and self.api_credentials.has_key("secret"))):
            sys.stderr.write("No API credentials found.  Please do the 'register-this-app' dance.\n")
            sys.exit(self.EXIT_ERROR)


###
### "Main"
###

if __name__ == "__main__":
    try:
        tweet = Tweet()
        try:
            tweet.parseOptions(sys.argv[1:])
            tweet.parseConfig(tweet.getOpt("cfg_file"))
            tweet.verifyConfig()

            user = tweet.getOpt("user")

            tweet.getAccessInfo(user)
            tweet.setupApi(user)

            ids = tweet.getOpt("ids")
            if ids:
                tweet.retweet(ids)
            else:
                tweet.tweet()
        except tweet.Usage, u:
            if (u.err == tweet.EXIT_ERROR):
                out = sys.stderr
            else:
                out = sys.stdout
            out.write(u.msg)
            sys.exit(u.err)
	        # NOTREACHED

    except KeyboardInterrupt:
        # catch ^C, so we don't get a "confusing" python trace
        sys.exit(Tweet.EXIT_ERROR)
