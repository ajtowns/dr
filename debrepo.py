#!/usr/bin/env python

import couchdb, uuid, time, sys

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

    if "suite:%s" % suite not in db:
        db["suite:%s" % suite] = {
            "name": suite,
            "files": []
        }
    files = set(db["suite:%s" % suite]["files"])

    for r in chsets[ [suite,None] : [suite,0] ]:
	if "del" in r.doc:
            files.difference_update( r.doc["del"] )
        if "add" in r.doc:
            files.update( r.doc["add"] )

    return files

def generate_Packages(db, suite, out=sys.stdout):
    all_files = list(suite_files(db, suite))
    all_files.sort()
    while all_files != []:
        files = all_files[:50]
	all_files = all_files[50:]

        v = db.view("_all_docs", keys=files, include_docs=True)
        for r in v:
            c = r.doc["CONTROL"]
	    for k,v in zip(c[::2], c[1::2]):
	        out.write(("%s:%s\n" % (k,v)).encode('utf-8'))
            out.write("\n")

def update_suite_from_Packages(db, suite, packages):
    count = 0

    current_files = suite_files(db, suite)
    not_seen_files = set(current_files)
    additional_files = []

    for s in readstanzas(packages):
        count += 1
        if False and count > 1300:
            print "count at %d, stopping" % (count)
            break

        d = stanza2dict(s)
        fileid = find_matching_deb_ids(db, d)

        if fileid is None:
            i = 0
            while True:
                fileid = "file:deb:%s_%s_%s:%s" % (d["package"], d["version"], d["architecture"], str(i))
                if fileid not in db: break
                i += 1
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

def find_package(db, pkgname, ignore_changes=False):
    debinfo = db.view("example/debinfo", include_docs=True)
    skey = [pkgname]
    ekey = [pkgname, {}]
    matches = []
    for r in debinfo[ skey:ekey ]:
        matches.append( (r.doc["version"], r.doc["architecture"], 
				r.doc["_id"]) )

    if ignore_changes:
        suiinfo = db.view("_all_docs", include_docs=True)
    else:
        suiinfo = db.view("_all_docs")
       
    for r in suiinfo[ "suite:":"suiteX" ]:
        suitename = r.key[6:]
        if ignore_changes:
            files = r.doc["files"]
        else:
            files = suite_files(db, suitename)

        for m in matches:
            if m[2] in files:
                print "%s | %s | %s | %s" % (pkgname, m[0], suitename, m[1])

if __name__ == "__main__":
    if len(sys.argv) < 2:
	print "Usage: %s [load|dump]" % (sys.argv[0])
	sys.exit(1)

    db = open_couchdb()

    if sys.argv[1] == "load":
	suitename, packages = "available-test", "/var/lib/dpkg/available"
        if len(sys.argv) >= 3:
            suitename = sys.argv[2]
        if len(sys.argv) >= 4:
            packages = sys.argv[3]
        update_suite_from_Packages(db, suitename, open(packages))
        print "done!"
    elif sys.argv[1] == "dump":
	suitename = "available-test"
        if len(sys.argv) >= 3:
            suitename = sys.argv[2]
        generate_Packages(db, suitename)
    elif sys.argv[1] == "ls":
        pkg = sys.argv[2]
        find_package(db, pkg)

