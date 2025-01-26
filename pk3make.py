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
    try:
        os.mkdir(workdir)
    except FileExistsError:
        pass

    return

def compile_palette(srcdir, workdir, lumpname):
    from modules import doompic,doomglob
    import os

    print("# Compiling Assets")
    print("## Loading main palette")
    pal = doompic.Palette(srcdir, lumpname)

    palglob = doomglob.find_lump(srcdir, lumpname)

    if len(palglob) > 1:
        raise DuplicateLumpError(f"Duplicate {palglob}")

    dest = workdir + '/' + \
        os.path.dirname(palglob[0][1]) + \
        palglob[0][0]


    print(f'## Writing palette "{dest}"')
    with open(dest, "wb") as ofile:
        ofile.write(pal.tobytes())
    return pal

def build(makefile):
    from modules import doompic, doomglob
    import shutil

    opts = makefile.get_options()

    if opts["palette"] == None:
        print("WARNING: Default color palette is not defined. Compiling graphics will lead to errors.")

    playpal = compile_palette(opts["srcdir"], opts["workdir"], opts["palette"])


    for lumpdef in makefile.get_lumpdefs():

        lumpglob = doomglob.find_lump(opts["srcdir"], lumpdef[0])

        for lump in lumpglob:

            srcfile = opts["srcdir"] + '/' + lump[1]
            destfile = opts["workdir"] + lump[2]

            bytedump = None

            match lumpdef[1]:
                case "graphic":
                    print(f'Converting Picture "{srcfile}"...')
                    bytedump = doompic.Picture(srcfile, playpal, lumpdef[2]).tobytes()
                case "flat" | "fade":
                    print(f'Converting Flat "{srcfile}"...')
                    bytedump = doompic.Flat(srcfile, playpal).tobytes()
                case "udmf":
                    print(f'UDMF lumps conversion is currently not supported.')
                case "raw":
                    shutil.copy2(srcfile, destfile)

            if bytedump != None:
                with open(destfile, "wb") as ofile:
                    ofile.write(bytedump)

    return

def pack(makefile):
    from modules import pk3zip, doomglob
    import os

    opts = makefile.get_options()
    if opts["destfile"] == None:
        raise FileNotFoundError("destfile is not defined")

    if not os.path.isdir(os.path.dirname(opts["destfile"])):
        print(f'# Creating directory {os.path.dirname(opts["destfile"])}')
        os.mkdir(os.path.dirname(opts["destfile"]))

    print("# Packing")

    for lumpdef in makefile.get_lumpdefs():

        if lumpdef[1] != "marker":
            # wf_ = Workfile
            print(f'packing lump {opts["workdir"]}, {lumpdef}')
            wf_glob = doomglob.find_lump(opts["workdir"], lumpdef[0])
            wf_path = opts["workdir"] + '/' + \
                os.path.dirname(wf_glob[0][1]) + \
                wf_glob[0][0]

        match lumpdef[1]:
            case "marker":
                pk3zip.add_marker(lumpdef[0], opts["destfile"])
            case _:
                pk3zip.copy_file("", opts["destfile"], lumpdef[0].stem[:8])
    return

def main():
    from modules import pk3makefile

    # Step switches
    step_prepare = False
    step_compile = False
    step_pack = False
    step_workdir = False
    step_workdir = False

    try:
        pk3mf_name = "./PK3Makefile"
        if args.makefile != None:
            pk3mf_name = args.makefile
        pk3mf = pk3makefile.PK3Makefile(pk3mf_name)

        print(f"MAKEOPTS: = {pk3mf.get_options()}")

        make_workdir(pk3mf.get_options("workdir"))
        compile_assets(pk3mf.get_options("srcdir"), pk3mf.get_options("workdir"))
        pack(pk3mf.get_options("workdir"), pk3mf.get_options("destfile"))

    except FileNotFoundError as e:
        print(f"An error occured. Exiting...\n{e}")
        exit

    #clean()
    return

if __name__ == "__main__":
    import argparse
    import pathlib

    # Shell argument API
    verbs = [
        'clean', # Delete workdir
        'prepare', # Make workdir tree etc.
        'compile', # Convert formats & copy files to workdir according to METAINFO
        'pack', # Pack existing workdir into pk3. (May be used for music packs?)
        'make', # Do everything
    ]
    ap_main = argparse.ArgumentParser(
            prog='pk3make',
            description='PK3Make - Make for (Weissblatt) PK3s',
            epilog='Type `pk3make --help` for more info.')


    ap_main.add_argument('verb' , help='Action to perform.', choices=verbs)
    ap_main.add_argument('makefile', nargs='?', const='./PK3Makefile', help='PK3Makefile to referebce')

    args = ap_main.parse_args()

    main()
