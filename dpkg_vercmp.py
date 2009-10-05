#!/usr/bin/env python

import re

re_legal_epoch = re.compile("^\d+$")
re_legal_revision = re.compile("^[A-z0-9+.~]+$")
re_legal_version = re.compile("^[A-z0-9+:.~-]+$")

class IllegalVersion(Exception):
    pass

class Version(object):
    def __init__(self, version):
	self.epoch = 0
	self.revision = "0"

	if ":" in version:
	    self.epoch, version = version.split(":",1)
	    if not re_legal_epoch.match(self.epoch):
	        raise IllegalVersion("Bad epoch in version")
	    self.epoch = int(self.epoch)

	if "-" in version:
	    version, self.revision = version.rsplit("-",1)
	    if not re_legal_revision.match(self.revision):
	        raise IllegalVersion("Bad revision in version")

	self.version = version

	if not re_legal_version.match(self.version):
	    raise IllegalVersion("Bad upstream in version")

    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    ordering = "~" + "$" + alphabet + alphabet.lower() + "+-.:"
    al_num = re.compile("(\D*)(\d*)")

    @classmethod
    def rev_cmp(cls, left, right):
	for l,r in zip(cls.al_num.finditer(left), cls.al_num.finditer(right)):
            for tl,tr in zip(l.group(1)+"$", r.group(1)+"$"):
		if tl != tr:
                    return cmp(cls.ordering.index(tl), self.ordering.index(tr))
            nl, nr = int("0"+l.group(2)), int("0"+r.group(2))
	    if nl != nr:
                return cmp(nl, nr)
        return 0
	
    def __cmp__(self, other):
	return cmp(self.epoch, other.epoch) or \
           self.rev_cmp(self.version, other.version) or \
           self.rev_cmp(self.revision, other.revision)
       
    def __repr__(self):
        return "%d:%s-%s" % (self.epoch, self.version, self.revision)


