#! /usr/bin/env python
#
# This little tool is a very simple command-line tweeter.  That is, it
# allows you to send a twitter update to a given user account.  It doesn't
# do anything else.
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

###
### Classes
###

class Tweet(object):
    """A very simple twitter updater."""

    EXIT_ERROR = 1
    EXIT_SUCCESS = 0

    MAXCHARS = 280

    # https://dev.twitter.com/docs/tco-link-wrapper/faq
    # Technically, we should query and retrieve the max length for t.co
    # links, but I'm gonna go ahead and just use the current (as of
    # 2012-04-18) value.
    SHORT_LENGTH = 21

    def __init__(self):
        """Construct a Tweet object with default values."""

        self.__opts = {
                    "cfg_file"   : os.path.expanduser("~/.tweetrc"),
                    "blockees"   : [],
                    "aid"        : None,
                    "dids"       : [],
                    "friends"    : [],
                    "foes"       : [],
                    "likes"      : [],
                    "media"      : None,
                    "pids"       : False,
                    "rtids"      : [],
                    "truncate"   : False,
                    "unblockees" : [],
                    "user"       : ""
                 }
        self.auth = None
        self.api = None
        self.api_credentials = {}
        self.users = {}
        self.msg = ""
        self.we_tweet = True


    class Usage(Exception):
        """A simple exception that provides a usage statement and a return code."""

        def __init__(self, rval):
            self.err = rval
            self.msg = 'Usage: %s [-hit] [-[BF] user] [-[adlr] id]\n' % os.path.basename(sys.argv[0])
            self.msg += '  [-[bf] user] -u user\n'
            self.msg += '\t-B user  unblock this user\n'
            self.msg += '\t-F user  unfollow this user\n'
            self.msg += '\t-a id    answer given message\n'
            self.msg += '\t-b user  block this user\n'
            self.msg += '\t-d id    delete given message\n'
            self.msg += '\t-f user  follow this user\n'
            self.msg += '\t-h       print this message and exit\n'
            self.msg += '\t-i       print the tweet ID of any new tweets\n'
            self.msg += '\t-l id    like given message\n'
            self.msg += '\t-r id    retweet given message\n'
            self.msg += '\t-t       truncate messages\n'
            self.msg += '\t-u user  tweet as this user\n'


    def block(self, blockees):
        """Block the given users."""

        for b in blockees:
            try:
                self.api.create_block(b)
            except tweepy.error.TweepError, e:
                sys.stderr.write("Error blocking %s: %s\n" % (f, e))
                return 1

        return 0


    def delete(self, ids):
        """Delete the given message."""

        for msg in ids:
            try:
                self.api.destroy_status(msg)
            except tweepy.error.TweepError, e:
                sys.stderr.write("Error deleting %s: %s\n" % (msg, e))
                return 1

        return 0

    def follow(self, friends):
        """Follow the given users."""

        for f in friends:
            try:
                self.api.create_friendship(f)
            except tweepy.error.TweepError, e:
                sys.stderr.write("Error following %s: %s\n" % (f, e))
                return 1

        return 0


    def favorite(self, ids):
        """Favorite^WLike the given tweets."""

        for msg in ids:
            try:
                self.api.create_favorite(msg)
            except tweepy.error.TweepError, e:
                sys.stderr.write("Error faving %s: %s\n" % (msg, e))
                return 1

        return 0


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
            "key" : self.auth.access_token,
            "secret" : self.auth.access_token_secret
        }

        cfile = self.getOpt("cfg_file")
        try:
            f = file(cfile, "a")
            f.write("%s_key = %s\n" % (user, self.auth.access_token))
            f.write("%s_secret = %s\n" % (user, self.auth.access_token_secret))
            f.close()
        except IOError, e:
            sys.stderr.write("Unable to write to config file '%s': %s\n" % \
                (cfile, e.strerror))
            raise


    def getLen(self, msg):
        """Return the length of the message, accounting for t.co link
        wrapping by Twitter."""

        pattern = re.compile('^(ftp|https?)://.+$')

        words = []
        length = 0

        for word in msg.split():
            if pattern.match(word):
                length += self.SHORT_LENGTH
            else:
                length += len(word)
            # whitespace
            length += 1

        return length


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
            opts, args = getopt.getopt(inargs, "B:F:a:b:c:d:f:hil:m:r:tu:")
        except getopt.GetoptError:
            raise self.Usage(self.EXIT_ERROR)

        for o, a in opts:
            if o in ("-B"):
                unblockees = self.getOpt("unblockees")
                unblockees.append(a)
                self.setOpt("unblockees", unblockees)
                self.we_tweet = False
            if o in ("-F"):
                foes = self.getOpt("foes")
                foes.append(a)
                self.setOpt("foes", foes)
                self.we_tweet = False
            if o in ("-a"):
                self.setOpt("aid", a)
            if o in ("-b"):
                blockees = self.getOpt("blockees")
                blockees.append(a)
                self.setOpt("blockees", blockees)
                self.we_tweet = False
            if o in ("-c"):
                self.setOpt("cfg_file", a)
            if o in ("-d"):
                dids = self.getOpt("dids")
                dids.append(a)
                self.setOpt("dids", dids)
                self.we_tweet = False
            if o in ("-h"):
                raise self.Usage(self.EXIT_SUCCESS)
            if o in ("-f"):
                friends = self.getOpt("friends")
                friends.append(a)
                self.setOpt("friends", friends)
                self.we_tweet = False
            if o in ("-i"):
                self.setOpt("pids", True)
            if o in ("-l"):
                likes = self.getOpt("likes")
                likes.append(a)
                self.setOpt("likes", likes)
                self.we_tweet = False
            if o in ("-m"):
                self.setOpt("media", a)
            if o in ("-r"):
                rtids = self.getOpt("rtids")
                rtids.append(a)
                self.setOpt("rtids", rtids)
                self.we_tweet = False
            if o in ("-t"):
                self.setOpt("truncate", True)
            if o in ("-u"):
                self.setOpt("user", a)

        if not self.getOpt("user") or args:
            raise self.Usage(self.EXIT_ERROR)


    def readInput(self):
        """Read the input from stdin.

        Arguments: none

        Returns:
            the given input, possibly modified

        Aborts:
            if given input is > MAXCHARS characters
        """

        msg = sys.stdin.readline().strip()
        l=self.getLen(msg)
        if l > self.MAXCHARS:
            if self.getOpt("truncate"):
                truncLen = self.MAXCHARS - 4
                msg = ' '.join(msg[:truncLen].split(' ')[0:-1]) + '...'
            else:
                sys.stderr.write("Message too long (%d). Trim by %d.\n" \
                    % (l, (l - self.MAXCHARS)))
                sys.exit(self.EXIT_ERROR)

        return msg


    def retweet(self, ids):
        """Re-Tweet the given message."""

        for msg in ids:
            try:
                self.api.retweet(msg)
            except tweepy.error.TweepError, e:
                sys.stderr.write("Error retweeting %s: %s\n" % (msg, e))
                return 1

        return 0


    def setOpt(self, opt, val):
        """Set the given option to the provided value"""

        self.__opts[opt] = val


    def setupApi(self, user):
        """Create the object's api"""

        key = self.users[user]["key"]
        secret = self.users[user]["secret"]
        self.auth.set_access_token(key, secret)

        self.api = tweepy.API(self.auth)


    def tweet(self):
        """Read and then tweet the message"""

        status = None
        media = self.getOpt("media")

        msg = self.readInput()

        try:

            if media:
                if not os.access(media, os.F_OK):
                    sys.stderr.write("No such file: %s\n" % media)
                    return 1
                if not os.access(media, os.R_OK):
                    sys.stderr.write("Unable to read: %s\n" % media)
                    return 1

                status = self.api.update_with_media(media, status=msg, in_reply_to_status_id=self.getOpt("aid"))
            else:
                status = self.api.update_status(msg, self.getOpt("aid"))

            if self.getOpt("pids"):
                print status.id

        except tweepy.error.TweepError, e:
            sys.stderr.write("Unable to tweet: %s\n" % e)
            return 1

        return 0


    def unblock(self, unblockees):
        """Unblock the given users."""

        for b in unblockees:
            try:
                self.api.destroy_block(b)
            except tweepy.error.TweepError, e:
                sys.stderr.write("Error un-blocking %s: %s\n" % (f, e))
                return 1

        return 0


    def unfollow(self, foes):
        """Un-Follow the given users."""

        for f in foes:
            try:
                self.api.destroy_friendship(f)
            except tweepy.error.TweepError, e:
                sys.stderr.write("Error un-following %s: %s\n" % (f, e))
                return 1

        return 0


    def verifyConfig(self):
        """Verify that we have api credentials."""

        if (not (self.api_credentials.has_key("key") and self.api_credentials.has_key("secret"))):
            sys.stderr.write("No API credentials found.  Please do the 'register-this-app' dance.\n")
            sys.stderr.write("See 'man tweet' for more information.\n")
            sys.exit(self.EXIT_ERROR)


###
### "Main"
###

if __name__ == "__main__":
    try:
        tweet = Tweet()
        try:
            rval = 0
            tweet.parseOptions(sys.argv[1:])
            tweet.parseConfig(tweet.getOpt("cfg_file"))
            tweet.verifyConfig()

            user = tweet.getOpt("user")

            tweet.getAccessInfo(user)
            tweet.setupApi(user)

            if tweet.we_tweet:
                sys.exit(tweet.tweet())

            # Many of the things we can do involve getting a list and
            # passing it to a function.  Let's map these, so we can more
            # easily iterate over them:
            actions = [ ("blockees", tweet.block),
                            ("unblockees", tweet.unblock),
                            ("dids", tweet.delete),
                            ("friends", tweet.follow),
                            ("foes", tweet.unfollow),
                            ("likes", tweet.favorite),
                            ("rtids", tweet.retweet) ]

            for (thing, func) in actions:
                things = tweet.getOpt(thing)
                rval += func(things)

            sys.exit(rval)

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
