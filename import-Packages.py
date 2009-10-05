#!/usr/bin/env python

import couchdb, uuid, time

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
    d = dict( (k.lower(), v.strip()) for k,v in s )
    d["CONTROL"] = sum(s, [])
    return d

def open_couchdb(serverurl="http://localhost:5984/", dbname="debrepo"):
    server = couchdb.client.Server(serverurl)
    if dbname not in server:
        server.create(dbname)
    return server[dbname]

def find_matching_deb_ids(db, deb):
    debinfo = db.view("example/debinfo", include_docs=True)
    key = [deb["package"], deb["version"], deb["architecture"] ]
    for r in debinfo[ key ]:
        if deb["CONTROL"] == r.doc["CONTROL"]:
            return r.doc["_id"]
    return None

def suite_files(db, suite):
    chsets = db.view("example/suite_changes", include_docs=True)

    files = set(db["suite:%s" % suite]["files"])

    for r in chsets[ [suite,None] : [suite,0] ]:
	if "del" in r.doc:
            files.difference_update( r.doc["del"] )
        if "add" in r.doc:
            files.update( r.doc["add"] )

    return files

def update_suite_from_Packages(db, suite, packages):
    count = 0

    current_files = suite_files(db, suite)
    not_seen_files = set(current_files)
    additional_files = []

    for s in readstanzas(packages):
        count += 1
        if count > 1300:
            print "count at %d, stopping" % (count)
            break

        d = stanza2dict(s)
        fileid = find_matching_deb_ids(db, d)

        if fileid is None:
            fileid = "file:deb:%s_%s_%s:%s" % (d["package"], d["version"], d["architecture"], "0")
            print "adding %s to db" % (fileid)
            db[fileid] = d
        else:
            print "found %s already in db!!" % (fileid)

        if fileid in current_files:
            not_seen_files.remove(fileid)
        else:
            additional_files.append(fileid)

    additional_files.sort()
    remove_files = list(not_seen_files)
    remove_files.sort()

    chsetid = "chset:%s:%s" % (suite, uuid.uuid4())

    chset = {
      "suite": suite,
      "timestamp": time.time(),
    }

    if additional_files != []:
        chset["add"] = additional_files
    if remove_files != []:
        chset["del"] = remove_files

    if additional_files == [] and remove_files == []:
        print "no change!"
    else:    
        db[chsetid] = chset

if __name__ == "__main__":
    db = open_couchdb()
    pkgs = open("/var/lib/dpkg/available")
    update_suite_from_Packages(db, "available-test", pkgs)
    print "done!"

