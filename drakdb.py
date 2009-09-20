#!/usr/bin/env python

from docdb import Derivation, Relation, Document, String, Integer, Array, Dict

class File(Document):
    name = String()
    content = String()
    type = String()

    groups = Array(Integer())       # references other files keys

    size = Integer()
    hash = Dict(String(), String()) # md5, sha1, etc keys; str values

    attributes = Dict(String(), String())  # "Package" -> "ifupdown", etc

    total_count = Derivation(sum=1)
    total_size = Derivation(sum=size)

class Collection(Document):
    owner = String()           # debian.org
    group = String()           # main / security / backports
    suite = String()           # sid / squeeze / ...
    component = String()       # main / contrib / non-free

    types = Array(String())    # .dsc, .deb, ...

class CollectionFiles(Relation):
    relationship = (File, Collection)
    derivations = {
        File: {
            "member_of":     Derivation(list=Collection._id),
            "n_collections": Derivation(sum=1),
        },
        Collection: {
            "members":      Derivation(list=File._id),
            "member_count": Derivation(sum=1),
            "member_size":  Derivation(sum=File.size),
        },
    }

if __name__ == "__xmain__":
    import gae_datastore_db
    db = gae_datastore_db.init()

    fs = db.get(File, name="ifupdown_0.7.0-1.deb")
    print [f.n_collections for f in fs]

