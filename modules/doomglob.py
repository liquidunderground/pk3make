class DuplicateLumpError(Exception):
    """To be raised when a lump should really be unique"""
    pass


def find_lump(srcdir, lumpname):
    import os, glob
    from pathlib import Path
    out = list()

    if srcdir == None:
        raise FileNotFoundError(f'doomglob.find_lump(): No srcdir given')
    if lumpname == None:
        raise FileNotFoundError(f'doomglob.find_lump(): No lumpname given')

    #searchstr = srcdir+"/**/"+lumpname
    #if lumpname[0] != '/':
        #searchstr = srcdir+lumpname

    #for path in glob.glob(searchstr, root_dir=srcdir):
    for path in glob.iglob('**/'+lumpname+'*', root_dir=srcdir, recursive=True):
        doomname = Path(path).stem[:8]
        arcpath = '/'+os.path.dirname(path).lstrip('/').rstrip('/')+'/'+doomname
        out.append( (doomname, path, arcpath) )

    return out # List of tuples (LUMPNAME, PATH, ARCPATH)

def fake_lump(lumpname):
    # Only for use with generated lumps, such as COLORMAPs or TINTTABs
    from pathlib import Path
    ln_short = Path(lumpname).stem[:8]
    arcpath = '/'+ln_short.lstrip('/')
    return [ (ln_short, lumpname, arcpath) ]
