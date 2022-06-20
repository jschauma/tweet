# A simple Makefile to (un)install tweet.

NAME=tweet

PREFIX?=/usr/local
PYTHON?=python

all:
	@echo "Available targets:"
	@echo " clean"
	@echo " install"
	@echo " uninstall"
	@echo " readme"

clean:
	rm -f src/${NAME}.py doc/${NAME}.1.txt

check:
	@if ! echo "import tweepy" | ${PYTHON} 2>/dev/null ; then		\
		echo "Please install https://github.com/tweepy/tweepy" >&2 ;	\
		exit 1; 							\
	fi
src/${NAME}.py: src/${NAME}.py.in
	sed -e "s/<PYTHON>/${PYTHON}/" $? > $@

install: check src/${NAME}.py
	mkdir -p ${PREFIX}/bin
	mkdir -p ${PREFIX}/share/man/man1
	install -c -m 755 src/${NAME}.py ${PREFIX}/bin/${NAME}
	install -c -m 444 doc/${NAME}.1 ${PREFIX}/share/man/man1/${NAME}.1

uninstall:
	rm -f ${PREFIX}/bin/${NAME} ${PREFIX}/share/man/man1/${NAME}.1

man: doc/${NAME}.1.txt

doc/${NAME}.1.txt: doc/${NAME}.1
	mandoc -c -O width=80 $? | col -b >$@

readme: man
	sed -n -e '/^NAME/!p;//q' README.md >.readme
	sed -n -e '/^NAME/,$$p' -e '/emailing/q' doc/${NAME}.1.txt >>.readme
	echo '```' >>.readme
	mv .readme README.md
