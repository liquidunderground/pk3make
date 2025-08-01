class DuplicateLumpError(Exception):
    """To be raised when a lump should really be unique"""
    pass


def find_lump(srcdir, lumpname):
    import os, glob
    import pathlib
    out = list()

    if srcdir == None:
        raise FileNotFoundError(f'doomglob.find_lump(): No srcdir given')
    if lumpname == None:
        raise FileNotFoundError(f'doomglob.find_lump(): No lumpname given')

    #for path in glob.glob(searchstr, root_dir=srcdir):
    for path in glob.iglob('**/'+lumpname+'*', root_dir=srcdir, recursive=True):
        posixpath = pathlib.Path(path).as_posix()
        doomname = pathlib.Path(path).stem[:8]
        arcpath = (os.path.dirname(posixpath)+'/'+doomname).lstrip('/').rstrip('/')
        if  pathlib.Path(srcdir.rstrip('/')+'/'+posixpath).is_file(): # Filter out directories
            out.append( (doomname, posixpath, arcpath) )

    # Deduplicate out
    out = [x for n,x in enumerate(out) if x not in out[:n] ]
                    
    return out # List of tuples (LUMPNAME, PATH, ARCPATH)

def fake_lump(lumpname):
    # Only for use with generated lumps, such as COLORMAPs or TINTTABs
    from pathlib import Path
    ln_short = Path(lumpname).stem[:8]
    arcpath = '/'+ln_short.lstrip('/')
    return [ (ln_short, lumpname, arcpath) ]
