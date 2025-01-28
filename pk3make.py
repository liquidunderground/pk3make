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


def build(makefile):
    from modules import doompic, doomglob
    import shutil, os

    opts = makefile.get_options()

    if opts["palette"] == None:
        print("WARNING: Default color palette is not defined. Compiling graphics will lead to errors.")

    #playpal = compile_palette(opts["srcdir"], opts["workdir"], opts["palette"])

    pp_glob = doomglob.find_lump(opts["srcdir"], opts["palette"])

    if len(pp_glob) > 1:
        globlist = []
        for f in pp_glob:
            globlist.append(f[1])
        raise doomglob.DuplicateLumpError(f"Color palette {lumpname} is not unique.\n{globlist}")
    elif len(pp_glob) < 1:
        raise FileNotFoundError(f"Color palette {lumpname} not found.")

    playpal = doompic.Palette(os.path.join(opts["srcdir"],pp_glob[0][1]))

    # ======== #

    for lumpdef in makefile.get_lumpdefs():

        lumpglob = doomglob.find_lump(opts["srcdir"], lumpdef[0])
        print (f"DOOMGLOB FIND : {lumpglob}")

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

            bytedump = None

            match lumpdef[1]:
                case "graphic":
                    print(f'Converting Picture "{srcfile}"...')
                    bytedump = doompic.Picture(srcfile, playpal, offset=lumpdef[2]).tobytes()
                case "flat" | "fade":
                    print(f'Converting Flat "{srcfile}"...')
                    bytedump = doompic.Flat(srcfile, playpal).tobytes()
                case "udmf":
                    print(f'UDMF lumps conversion is currently not supported.')
                case "palette":
                    print(f'## Loading palette "{srcfile}"')
                    pal = playpal if lumpdef[0] == opts["palette"] else pal
                    bytedump = pal.tobytes()
                case "raw":
                    with open(srcfile, mode='rb') as s:
                        bytedump = s.read()


            if bytedump != None:
                print(f'## Writing {lumpdef[1]} "{destfile}"')
                os.makedirs(os.path.dirname(destfile), exist_ok=True)
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
