# A simple Makefile to (un)install tweet.

PREFIX?=/usr/local
PYTHON?=python

all:
	@echo "Available targets:"
	@echo " install"
	@echo " uninstall"

check:
	@if ! echo "import tweepy" | ${PYTHON} 2>/dev/null ; then		\
		echo "Please install https://github.com/tweepy/tweepy" >&2 ;	\
		exit 1; 							\
	fi


install: check
	mkdir -p ${PREFIX}/bin
	mkdir -p ${PREFIX}/share/man/man1
	install -c -m 755 src/tweet.py ${PREFIX}/bin/tweet
	install -c -m 444 doc/tweet.1 ${PREFIX}/share/man/man1/tweet.1

uninstall:
	rm -f ${PREFIX}/bin/tweet ${PREFIX}/share/man/man1/tweet.1
