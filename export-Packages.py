#!/usr/bin/env python

import couchdb, sys

server = couchdb.client.Server("http://localhost:5984/")
if "debrepo" not in server:
    server.create("debrepo")
db = server["debrepo"]

v = db.view("example/foo",group_level="2")
suite = "suite:available-test"
fa,fb = "file:deb:", "file:debX"
kv = list(v[[suite,fa]:[suite,fb]])
files = []
for r in kv:
    file = r.key[1]
    rev, present = r.value
    if present == "yes":
	files.append(file)

v = db.view("_all_docs", keys=files, include_docs=True)
for r in v:
    c = r.doc["CONTROL"]
    sys.stdout.write("".join("%s:%s\n" % (k,v) for k,v in zip(c[::2], c[1::2])).encode('utf-8'))
    sys.stdout.write("\n")
