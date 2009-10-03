#!/usr/bin/env python

import couchdb, uuid

def readstanzas(file):
    lineno = 0
    sofar = []
    for line in file:
        lineno += 1
        line = line.decode("utf-8").rstrip("\n")
        if line == "":
            yield sofar
            sofar = []
        else:
            if line.startswith(" ") and sofar != []:
                sofar[-1][1] += "\n" + line
            elif ":" in line:
                sofar.append( line.split(":", 1) )
	    else:
		raise Exception("parse error at line %d: %s" % (lineno, line))

    if sofar != []:
        # final stanza isn't followed by a blank line
        yield sofar

def stanza2dict(s):
    return dict( (k.lower(), v.strip()) for k,v in s )
    
server = couchdb.client.Server("http://localhost:5984/")
if "debrepo" not in server:
    server.create("debrepo")
db = server["debrepo"]

splatter = uuid.uuid1(0)

for s in readstanzas(open("/var/lib/dpkg/available")):
    d = stanza2dict(s)
    control = sum(s, [])

    fileid = "file:deb:%s_%s_%s:%s" % (d["package"], d["version"], d["architecture"], "0")

    d["CONTROL"] = control

    if fileid in db:
        od = db[fileid]
        if od["CONTROL"] == d["CONTROL"]:
	    print "skipping %s because it's all good" % (fileid)
        else:
	    print od, d
	    assert False
    else:
        print "adding %s to db" % (fileid)
        db[fileid] = d

    change = "collchange:%s" % (uuid.uuid4())
    db[change] = {
	"suite": "suite:available-test",
        "file": fileid,
        "revision": 0,
        "present": "yes",
    }

print "done!"

