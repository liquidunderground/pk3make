import os
import zipfile

def add_marker(marker, pk3):
    with  zipfile.ZipFile(pk3, "a") as zfile:
        zfile.writestr(marker, "")

def copy_tree(srcdir, pk3, arcname):
    with  zipfile.ZipFile(pk3, "a") as zfile:
        srcroot = os.path.abspath(workdir)
        for root,dirs,files in os.walk(srcroot):
            zfile.write(root)
            for file in files:
                zfile.write(os.path.join(root,file))

def copy_file(srcfile, pk3, arcname):
    with zipfile.ZipFile(pk3, "a") as zfile:
        abssrc = os.path.abspath(srcfile)
        zfile.write(abssrc, arcname)
