#!/bin/env python3


def clean(workdir="build"):
    import os
    print("# Removing workdir '{}'".format(workdir))
    try:
        os.rmdir(workdir)
    except FileNotFoundError:
        pass
    return

def make_workdir(workdir="build"):
    import os
    print("# Creating WORKDIR '{}'".format(workdir))
    try:
        os.mkdir(workdir)
    except FileExistsError:
        pass

    return

def compile_assets(srcdir="src/", workdir="build/"):
    from modules import doompic
    print("# Compiling Assets")
    print("## Loading main palette")
    playpal = doompic.Palette(srcdir+"/PLAYPAL.png")
    with open(workdir+"PLAYPAL", "w") as ofile:
        ofile.write(playpal.tobytes)
    return

def pack(workdir="build", pk3="bin/out.pk3"):
    from modules import pk3zip
    print("# Packing")
    pk3zip.add_marker("S_SUPER", pk3)
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

        make_workdir(pk3mf.get_options().workdir)
        compile_assets(pk3mf.get_options().srcdir, pk3mf.get_options().workdir)
        pack(pk3mf.get_options().workdir, pk3mf.get_options().destfile)

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
