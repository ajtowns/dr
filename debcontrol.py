#!/usr/bin/env python

import tarfile, os, StringIO

def parsear(arfile):
    global_header = arfile.read(8)
    if global_header != "!<arch>\n":
        raise Exception("not an ar file")
    while True:
        file_header = arfile.read(60)
        if len(file_header) == 0: break

        if len(file_header) != 60:
            raise Exception("short ar file")

        filename = file_header[0:16]
        mod_time = file_header[16:28]
        owner    = file_header[28:34]
        group    = file_header[34:40]
        mode     = file_header[40:48]
        size     = int(file_header[48:58])
        magic    = file_header[58:60]

	filename = filename.rstrip(" ")

        if magic != "\140\012":
            raise Exception("ar file has bad magic in header (%s)" % ",".join(str(ord(i)) for i in magic))

        yield (filename, mod_time, owner, group, mode, size)

        arfile.seek(size+size%2, os.SEEK_CUR)

def read_control(deb):
    controlinfo = None
    for filename, _, _, _, _, size in parsear(deb):
	if filename.startswith("control.tar."):
	    compression = filename[12:]  # tarfile copes with gz, bz2

            contents = StringIO.StringIO(deb.read(size))
            deb.seek(-size, os.SEEK_CUR)

	    controltar = tarfile.open(fileobj=contents, mode="r")
	    controlinfo = controltar.extractfile("./control").read()
    return controlinfo

if __name__ == "__main__":
    import sys
    for debname in sys.argv[1:]:
        print "====%s====" % debname
        print read_control(open(debname,"rb"))


