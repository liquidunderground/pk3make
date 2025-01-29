#!/bin/env python3


def clean(workdir="build"):
    import os
    print("# Removing workdir '{}'".format(workdir))
    try:
        os.rmdir(workdir)
    except FileNotFoundError:
        pass
    return

def prepare(workdir="build"):
    import os
    print("# Creating WORKDIR '{}'".format(workdir))
    os.makedirs(workdir, exist_ok=True)

def cr_build_lump(lock, lumpdef, context):
    import shutil,os
    from modules import doompic

    bytedump = None

    print(f'Building {lumpdef[1]} "{context["srcfile"]}"...')

    match lumpdef[1]:
        case "graphic":
            print(f'Converting Picture "{context["srcfile"]}"...')
            bytedump = doompic.Picture(context['srcfile'], context["playpal"], offset=lumpdef[2]).tobytes()
        case "flat" | "fade":
            print(f'Converting Flat "{context["srcfile"]}"...')
            bytedump = doompic.Flat(context['srcfile'], context["playpal"]).tobytes()
        case "udmf":
            print(f'UDMF lumps conversion is currently not supported.')
        case "palette":
            print(f'## Loading palette "{context['srcfile']}"')
            pal = get_palette(lock, lumpdef[0], context["opts"], context["pdict"])
            print(f'## Dumping palette "{context["srcfile"]}"')
            bytedump = pal.tobytes()
        case "tinttab" | "colormap" as paltype:
            palparams = re.match(r"\s*([A-Ta-z0-9./\\]+)\s*([0-9]\.[0-9]f?)?", lumpdef[2])
            print(f'## Dumping {paltype} "{context["srcfile"]}"')
            pal = get_palette(lock, palparams.groups(1), context["opts"], context["pdict"])
            match paltype:
                case "tinttab":
                    palweight = float(palparams.groups(2))
                    bytedump = pal.tinttab_tobytes(palweight)
                case "colormap":
                    bytedump = pal.colormap_tobytes()
        case "raw":
            with open(context['srcfile'], mode='rb') as s:
                bytedump = s.read()

    if bytedump != None:
        print(f'## Writing {lumpdef[1]} "{context["destfile"]}"')
        os.makedirs(os.path.dirname(context["destfile"]), exist_ok=True)
        with lock:
            with open(context["destfile"], "wb") as ofile:
                ofile.write(bytedump)

def get_palette(lock, lumpname, opts, pdict):
    from modules import doompic, doomglob
    import os

    p_glob = doomglob.find_lump(opts["srcdir"], lumpname)

    if len(p_glob) > 1:
        globlist = []
        for f in p_glob:
            globlist.append(f[1])
        raise doomglob.DuplicateLumpError(f"Color palette {lumpname} is not unique.\n{globlist}")
    elif len(p_glob) < 1:
        raise FileNotFoundError(f"Color palette {lumpname} not found.")

    with lock:
        pdict[lumpname] = pdict.get(lumpname, \
            doompic.Palette(os.path.join(opts["srcdir"],p_glob[0][1])) )
    return pdict[lumpname] 


def build(makefile):
    from modules import doompic, doomglob
    import shutil, os
    import asyncio, concurrent.futures, multiprocessing

    opts = makefile.get_options()
    palettes = {}

    print(f'# Building {opts["srcdir"]} => {opts["workdir"]}')

    if opts["palette"] == None:
        print("WARNING: Default color palette is not defined. Compiling graphics will lead to errors.")

    ppx_man = multiprocessing.Manager()
    ppx_lock = ppx_man.Lock()
    ppx_futures = []

    playpal = get_palette(ppx_lock, opts["palette"], opts, palettes)

    with concurrent.futures.ProcessPoolExecutor() as ppx:

        for lumpdef in makefile.get_lumpdefs():

            lumpglob = doomglob.find_lump(opts["srcdir"], lumpdef[0])
            for lump in lumpglob:
                lump_dcheck = doomglob.find_lump(opts["srcdir"], lump[0])

                # Error check
                if len(lump_dcheck) > 1:
                    globlist = []
                    for f in lump_dcheck:
                        globlist.append(f[1])
                    raise doomglob.DuplicateLumpError(f"Lump {lump[0]} is not unique.\n{globlist}")


                srcfile = opts["srcdir"] + '/' + lump[1]
                destfile = opts["workdir"] + lump[2]

                # Out-Of-Date check
                if os.path.exists(destfile) and os.path.getmtime(srcfile) < os.path.getmtime(destfile):
                    continue
                ppx_context = {
                    "playpal" :  playpal,
                    "srcfile" :  srcfile,
                    "destfile" :  destfile,
                    "opts" :  opts,
                    "pdict": palettes,
                    }
                ppx_futures.append( ppx.submit(cr_build_lump, ppx_lock, lumpdef, ppx_context ) )

        # Did anything actually work?
        for f in ppx_futures:
            result = f.result()
    return

def pack(makefile):
    from modules import pk3zip, doomglob
    import os, pathlib

    opts = makefile.get_options()
    if opts["destfile"] == None:
        raise FileNotFoundError("destfile is not defined")

    if not os.path.isdir(os.path.dirname(opts["destfile"])):
        print(f'# Creating directory {os.path.dirname(opts["destfile"])}')
        os.mkdir(os.path.dirname(opts["destfile"]))

    print("# Packing")

    for lumpdef in makefile.get_lumpdefs():
        match lumpdef[1]:
            case "marker":
                print(f"## Adding marker {lumpdef[0]}")
                pk3zip.add_marker(lumpdef[0], opts["destfile"])
            case _:
                doomname = pathlib.Path(lumpdef[0]).stem[:8]
                wf_glob = doomglob.find_lump(opts["workdir"], doomname)
                for workfile in wf_glob:
                    wf_path = opts["workdir"] + workfile[2]
                    print(f'## Packing lump {workfile[2]}')
                    pk3zip.copy_file(wf_path, opts["destfile"], workfile[2])
    return

def main():
    from modules import pk3makefile

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
        case "all":
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
        build(pk3mf)
    if step_pack:
        pack(pk3mf)

    #clean()
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


    ap_main.add_argument('verb' , help='Action to perform.', choices=verbs)
    ap_main.add_argument('makefile', nargs='?', const='./PK3Makefile', help='PK3Makefile to referebce')

    args = ap_main.parse_args()

    main()
