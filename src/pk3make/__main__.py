#!/bin/env python3


def clean(workdir="build"):
    import shutil
    print("# Removing workdir '{}'".format(workdir))
    try:
        shutil.rmtree(workdir)
    except FileNotFoundError:
        pass
    return

def prepare(workdir="build"):
    import os
    print("# Creating WORKDIR '{}'".format(workdir))
    os.makedirs(workdir, exist_ok=True)

def cr_build_lump(lock, lumpdef, context):
    import shutil,os,re
    from .modules import doompic

    bytedump = None

    print(f'## Building {lumpdef[1]} "{context["srcfile"]}"...')

    match lumpdef[1]:
        case "graphic":
            pal = get_palette(lock, context["opts"]["palette"], context["opts"], context["pdict"])
            print(f'Converting Picture "{context["srcfile"]}"...')
            bytedump = doompic.Picture(context['srcfile'], pal, offset=lumpdef[2]).tobytes()
        case "flat" | "fade":
            pal = get_palette(lock, context["opts"]["palette"], context["opts"], context["pdict"])
            print(f'Converting Flat "{context["srcfile"]}"...')
            bytedump = doompic.Flat(context['srcfile'], pal).tobytes()
        case "udmf":
            print(f'UDMF lumps conversion is currently not supported.')
        case "palette":
            print(f'Loading palette "{context["srcfile"]}"')
            pal = get_palette(lock, lumpdef[0], context["opts"], context["pdict"])
            print(f'Dumping palette "{context["srcfile"]}"')
            bytedump = pal.tobytes()
        case "tinttab" | "colormap" as paltype:
            palparams = re.match(r"\s*([\w]+)\s*([0-9]\.[0-9]f?)?", lumpdef[2])
            pal = get_palette(lock, palparams.group(1), context["opts"], context["pdict"])
            print(f'Generating {paltype} "{context["destfile"]}" with {palparams.group(1,2)}')
            match paltype:
                case "tinttab":
                    palweight = float(palparams.group(2))
                    bytedump = pal.tinttab_tobytes(palweight)
                case "colormap":
                    bytedump = pal.colormap_tobytes()
        case "raw":
            with open(context['srcfile'], mode='rb') as s:
                bytedump = s.read()

    if bytedump != None:
        print(f'Writing {lumpdef[1]} "{context["destfile"]}"')
        os.makedirs(os.path.dirname(context["destfile"]), exist_ok=True)
        with lock:
            with open(context["destfile"], "wb") as ofile:
                ofile.write(bytedump)

def get_palette(lock, lumpname, opts, pdict):
    from .modules import doompic, doomglob
    import os

    lock.acquire()
    if not lumpname in pdict:

        p_glob = doomglob.find_lump(opts["srcdir"], lumpname)
        if len(p_glob) > 1:
            globlist = []
            for f in p_glob:
                globlist.append(f[1])
            raise doomglob.DuplicateLumpError(f"Color palette {lumpname} is not unique.\n{globlist}")
        elif len(p_glob) < 1:
            raise FileNotFoundError(f"Color palette {lumpname} not found.")

        print(f'Caching Palette "{lumpname}"')
        pdict[lumpname] = doompic.Palette(os.path.join(opts["srcdir"],p_glob[0][1]))
    lock.release()
    return pdict[lumpname] 


def build(makefile):
    from .modules import doompic, doomglob
    from natsort import natsorted, ns
    import shutil, os, re
    import asyncio, concurrent.futures, multiprocessing

    opts = makefile.get_options()

    print(f'# Building {opts["srcdir"]} => {opts["workdir"]}')

    if opts["palette"] == None:
        print("WARNING: Default color palette is not defined. Compiling graphics will lead to errors.")

    ppx_man = multiprocessing.Manager()
    ppx_lock = ppx_man.Lock()
    palettes = ppx_man.dict()
    ppx_futures = []

    with concurrent.futures.ThreadPoolExecutor() as ppx:

        for lumpdef in makefile.get_lumpdefs():
            match lumpdef[1]:
                case "colormap" | "tinttab" as ltype: # Hardcoded exceptions, eww
                    lumpglob = doomglob.fake_lump(lumpdef[0])
                case _:
                    lumpglob = doomglob.find_lump(opts["srcdir"], lumpdef[0])



            for lump in natsorted(lumpglob, alg=ns.PATH):
                lump_dcheck = doomglob.find_lump(opts["srcdir"], lump[0])

                srcfile = opts["srcdir"] + '/' + lump[1]
                destfile = opts["workdir"] + '/' + lump[2]

                params = re.match(r"\s*([\w]+)\s*", lumpdef[2] or '')
                if params != None and "preserve_filename" in params.groups():
                    destfile = opts["workdir"] +'/'+ lump[1]

                # Out-Of-Date check
                if lumpdef[1] in ["colormap", "tinttab"]:
                    palbase_name = re.match(r"\s*([\w]+)\s*", lumpdef[2]).group(1)
                    ood_target = doomglob.find_lump(opts["srcdir"],palbase_name)
                    srcfile = opts["srcdir"] + '/' + ood_target[0][1]

                if os.path.exists(destfile) and os.path.getmtime(srcfile) < os.path.getmtime(destfile):
                    continue
                fake_lumpdef = (lump[0],lumpdef[1],lumpdef[2])
                ppx_context = {
                    "srcfile" :  srcfile,
                    "destfile" :  destfile,
                    "opts" :  opts,
                    "pdict": palettes,
                    }
                ppx_futures.append( ppx.submit(cr_build_lump, ppx_lock, fake_lumpdef, ppx_context ) )
                #cr_build_lump(ppx_lock, fake_lumpdef, ppx_context ) # For testing single-threadedly

        # Did anything actually work?
        for f in ppx_futures:
            result = f.result()
    return

def pack(makefile):
    from .modules import pk3zip, doomglob
    from natsort import natsorted, ns
    import io, os, hashlib, pathlib, re

    opts = makefile.get_options()
    if opts["destfile"] == None:
        raise FileNotFoundError("destfile is not defined")

    print("# Packing")
    
    # Keep PK3 file in memory to avoid Windows' file access locks
    pk3buf = io.BytesIO()
    
    for lumpdef in makefile.get_lumpdefs():
        
        if args.verbose:
            print(f'# Packing lumpdef {lumpdef}')
            
        match lumpdef[1]:
            case "marker":
                
                if args.verbose:
                    print(f"## Adding marker {lumpdef[0]}")
                with pk3zip.PK3File(pk3buf, "a") as pk3:
                    pk3.writestr(lumpdef[0], "")
            case _:
                params = re.match(r"\s*([\w]+)\s*", lumpdef[2] or '')
                searchname = os.path.dirname(lumpdef[0])+'/'+pathlib.Path(lumpdef[0]).stem[:8]
                if params != None and "preserve_filename" in params.groups():
                    searchname = lumpdef[0]
                
                with pk3zip.PK3File(pk3buf, "a") as pk3:

                    wf_glob = doomglob.find_lump(opts["workdir"], searchname)
                    wf_glob = natsorted(wf_glob, alg=ns.PATH)

                    #print(f'\nGLOB: {wf_glob}\n')
                    #print(f'NAMELIST: {pk3.namelist()}\n')

                    wf_unique = [x for x in wf_glob if x[2].lstrip('/').rstrip('/') not in pk3.namelist() ]
                    if params != None and "preserve_filename" in params.groups():
                        wf_unique = [x for x in wf_glob if x[1].lstrip('/').rstrip('/') not in pk3.namelist() ]

                    #print(f'\nUNIQUE GLOB: {wf_unique}\n')

                    for lump,srcfile,arcpath in wf_unique:
                        wf_path = opts["workdir"] + '/' + srcfile

                        if params != None and "preserve_filename" in params.groups():
                            wf_path = opts["workdir"]+'/'+srcfile
                            arcpath = os.path.dirname(arcpath)+'/'+os.path.basename(srcfile)

                        
                        if args.verbose:
                            print(f'## Packing lump {arcpath}')    

                        pk3.write(wf_path, arcpath)

    
    # Commit in-memory PK3 file to disk
    
    if not os.path.isdir(os.path.dirname(opts["destfile"])):
        print(f'## Creating directory {os.path.dirname(opts["destfile"])}')
        os.mkdir(os.path.dirname(opts["destfile"]))

    if os.path.isfile(opts["destfile"]):
        print(f'## Deleting {opts["destfile"]} for recreation')
        os.remove(opts["destfile"])
    
    with open(opts["destfile"], "wb") as f:
        print(f'## Writing {opts["destfile"]}')
        f.write(pk3buf.getvalue())
    
    md5hash = hashlib.md5(pk3buf.getvalue())
    print(f'\nMD5 Hash of {opts["destfile"]}: {md5hash.hexdigest()}')

    return

def main():
    from .modules import pk3makefile

    # Step switches
    step_prepare = False
    step_build = False
    step_pack = False

    match args.verb:
        case "prepare":
            step_prepare = True
        case "build":
            step_build = True
        case "pack":
            step_pack = True
        case None | "all":
            step_prepare = True
            step_build = True
            step_pack = True

    if args.verb == "clean":
        clean()

    pk3mf_name = "./PK3Makefile"
    if args.makefile != None:
        pk3mf_name = args.makefile
    pk3mf = pk3makefile.PK3Makefile(pk3mf_name)

    print(f"MAKEOPTS: = {pk3mf.get_options()}")

    # TODO: Add resolve for missing dependencies
    if step_prepare:
        prepare(pk3mf.get_options("workdir"))
    if step_build:
        if args.verb == "build" and args.target != None:
            pk3mf = pk3mf.filter_lumpdefs(args.target)
        build(pk3mf)
    if step_pack:
        pack(pk3mf)

    return

if __name__ == "__main__":
    import argparse
    import pathlib

    # Shell argument API
    verbs = [
        'clean', # Delete workdir
        'prepare', # Make workdir tree etc.
        'build', # Convert formats & copy files to workdir according to METAINFO
        'pack', # Pack existing workdir into pk3. (May be used for music packs?)
        'all', # Do everything
    ]
    ap_main = argparse.ArgumentParser(
            prog='pk3make',
            description='PK3Make - Make for (Weissblatt) PK3s',
            epilog='Type `pk3make --help` for more info.')
    ap_sub = ap_main.add_subparsers(title='Build steps', dest='verb', metavar="")
    
    ap_clean = ap_sub.add_parser('clean', help='Delete the build directory')
    ap_build = ap_sub.add_parser('build', help='Compile assets into the build directory')
    ap_pack = ap_sub.add_parser('pack', help='Assemble a PK3 file from the build directory')

    ap_main.add_argument('-v', '--verbose' , action='store_true', help='Verbose log output')
    ap_build.add_argument('target', nargs='?', help='Target LUMPDEF')
    
    ap_main.add_argument('makefile', nargs='?', const='./PK3Makefile', help='PK3Makefile to reference')
    
    args = ap_main.parse_args()

    main()
