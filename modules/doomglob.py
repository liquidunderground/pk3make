class DuplicateLumpError(Exception):
    """To be raised when a lump should really be unique"""
    pass


def find_lump(srcdir, lumpname):
    import os, glob
    out = list()
    #searchstr = srcdir+"/**/"+lumpname
    #if lumpname[0] != '/':
        #searchstr = srcdir+lumpname

    #for path in glob.glob(searchstr, root_dir=srcdir):
    for path in glob.glob(lumpname+'*', root_dir=srcdir):
        doomname = os.path.basename(path)[:8]
        out.append( (doomname, path) )

    return out # List of tuples (LUMPNAME, PATH)
