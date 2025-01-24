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

def compile_assets(srcdir, workdir):
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
    # Step switches
    step_prepare = False
    step_compile = False
    step_pack = False
    step_workdir = False
    step_workdir = False

    make_workdir()
    compile_assets()
    pack()
    clean()
    return

if __name__ == "__main__":
    import argparse
    import pathlib

    # Shell argument API
    verbs = [
        'help', # Print help
        'clean', # Delete workdir
        'prepare', # Make workdir tree etc.
        'compile', # Convert formats & copy files to workdir according to METAINFO
        'pack', # Pack existing workdir into pk3. (May be used for music packs?)
        'make', # Do everything
    ]
    ap_main = argparse.ArgumentParser(
            prog='pk3make',
            description='Weissblatt PK3 compiler',
            epilog='Type help, -h or --help for more info.')


    ap_main.add_argument('verb' , help='Action to perform.', choices=verbs)
    ap_main.add_argument('-f', '--force-recreate' , help='Recreate temp tree even when unneeded')
    ap_main.add_argument('-p', '--palette' , help='Palette to use for converting PNG-based types')

    args = ap_main.parse_args()

    main()
