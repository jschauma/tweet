# tweet - a very simple command-line twitter client

`tweet(1)` is a very simple command-line tweeter. That is, it allows you to
send a twitter update to a given user account. It doesn't do anything
else. Well, actually, it also allows you to follow or unfollow accounts as
well as block and unblock users.  So there's that.  Also, this tool
suffers from feeping creatures and will (or already has) probably
spawn(ed) additional features making it not all that very simple anymore.

It's still _comparatively_ simple, I suppose.

Requirements:
	- python3
	- py-tweepy (http://code.google.com/p/tweepy/)

Questions/comments:
	jschauma@netmeister.org
	https://www.netmeister.org/apps/twitter/tweet/

Installation
============

To install the command and manual page somewhere
convenient, run `make install`; the Makefile defaults
to '/usr/local' but you can change the PREFIX:

```
$ make PREFIX=~ install
```

Documentation
=============

Please see the manual page for all details:

```
NAME
     tweet - send a twitter update

SYNOPSIS
     tweet [-hit] [-B user] [-F user] [-R id] [-a id] [-b user] [-c file]
	   [-d id] [-f user] [-l id] [-m media] [-r id] -u user

DESCRIPTION
     tweet is a very simple tool to send a twitter update to the given account -
     nothing else.  The message to send is read from STDIN; the user account to
     update needs to be configured in the file ~/.tweetrc.

OPTIONS
     The following options are supported by tweet:

     -B user   Unblock the given user.	Can be given multiple times to unblock
	       multiple users.

     -F user   Unfollow the given user.	 Can be given multiple times to unfollow
	       multiple users.

     -R id     Un-retweet the tweet with the given id.	Can be given multiple
	       times to un-retweet multiple messages.

     -a id     Answer (ie reply) to the given id.  That is, let the API sort the
	       new message as a reply to this message.

     -b user   Block the given user.  Can be given multiple times to block
	       multiple users.

     -c file   Read the configuration from the given file.

     -d id     Delete the given message.  Can be given multiple times to delete
	       multiple messages.

     -h	       Print a short usage statement and exit.

     -i	       Print the tweet ID of any new tweets.

     -f user   Follow the given user.  Can be given multiple times to follow
	       multiple users.

     -l id     Like the given tweet.  Can be given multiple times to like
	       multiple tweets.

     -m media  Upload the given media (picture or video).

     -r id     Retweet the tweet with the given id.  Can be given multiple times
	       to retweet multiple messages.

     -t	       Truncate messages that are too long.

     -u user   Update the given account.

DETAILS
     tweet requires you to specify the username of the twitter account to which
     to post the update.  After that, it will read input from STDIN.

     If the configuration file ~/.tweetrc contains information for exactly one
     username, then tweet will update that user's status.  If the file does not
     contain information for the user given on the command-line, then tweet will
     attempt to retrieve the access information for that account and ask the
     user to update the configuration file.

     If the resulting message contains 280 or fewer characters, tweet will post
     the message directly, otherwise, it will complain and exit (unless the -t
     flag is given).

     If the -r flag is given, tweet will not read anything from STDIN and simply
     retweet the messages with the given ID(s).

TWITTER AUTHORIZATION
     tweet uses OAuth for authentication with Twitter.	This means that in order
     to run the application, it needs a so-called "consumer key" and "consumer
     secret".  These are retrieved by registering an application with Twitter.

     Now for hopefully obvious reasons it's undesirable for an application to be
     distributed with its own key and secret; unfortunately that means that
     anybody wishing to run this tool would have to get their own consumer
     secret and key.

     Hence, if you wish to run this tool, please go to
     https://developer.twitter.com/ and register a new client.	Then store the
     key and secret in the configuration file (see below).

CONFIGURATION FILE
     tweet looks for user access information in ~/.tweetrc.  It will ignore all
     lines except for lines matching the patterns <user>_key=<key> and
     <user>_secret=<key>.  Those values need to be the access credentials
     created via OAuth (which tweet will generate for you and write to the file
     if not present for the given user).

     In addition to these, tweet also needs its own api credentials.  These are
     stored as (literally) "<api>_key" and "<api>_secret" (ie the username is
     "<api>", including the <>).

EXIT STATUS
     The tweet utility exits 0 on success, and >0 if an error occurs.

HISTORY
     tweet was originally written by Jan Schaumann <jschauma@netmeister.org> in
     January 2011.

BUGS
     Please file bugs and feature requests via GitHub pull requests and issues
     or by emailing the author.
```
