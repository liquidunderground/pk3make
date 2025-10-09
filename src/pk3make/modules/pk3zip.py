import os, io, re
import zipfile, pathlib
#from binaryornot.check import is_binary

class PK3File(zipfile.ZipFile):
    """This class is basically a deterministic ZIP file.
    Four attributes need to be controlled:
    1. Order of files follows programmatic order
    2. Timestamp is set to 1980-01-01 00:00:00
    3. All files are set to permissions (d)rw-rw-rw-
    4. Create system is set to 03/Unix
    """

    ### Inherited/overwritten ZipFile functions ###
    def mkdir(self, zinfo_or_directory, mode=511):
        # Force metadata
        if isinstance(zinfo_or_arcname, zipfile.ZipInfo):
            zinfo = zinfo_or_directory
        else:
            zinfo = zipfile.ZipInfo(filename=(zinfo_or_directory.rstrip('/')+'/'))
        
        # Force deterministic metadata
        zinfo.date_time = (1980, 1, 1, 0, 0, 0)
        zinfo.create_system = 3
        zinfo.external_attr = (0o40744 << 16) | 0x10  # Octal encoding for drwxr--r--
            
        # Mode is overwritten to achieve determinism
        zipfile.ZipFile.mkdir(self, zinfo, 511)
    
    def write(self, filename, arcname, compress_type=None, compresslevel=None):
        
        nodename = pathlib.Path(filename).stem + pathlib.Path(filename).suffix
        zinfo = zipfile.ZipInfo.from_file(filename, arcname)
        
        # Force deterministic metadata
        zinfo.create_system = 3
        zinfo.date_time = (1980, 1, 1, 0, 0, 0)
        zinfo.external_attr = 0o0744 << 16  # Octal encoding for -rwxr--r--
        if zinfo.is_dir():
            zinfo.external_attr = (0o40744 << 16) | 0x10  # Octal encoding for drwxr--r--
        
        # Plain text file -> chain into writestr to convert line breaks
        #if not is_binary(filename):
        p = re.compile('(SOC_.*)|' \
            '(.*\.soc)|' \
            '(TEXTURES)|' \
            '(ANIMDEFS)|' \
            '(MUSICDEF)|' \
            '(L_.*)|' \
            '(lua_.*)|' \
            '(.*\.lua)|' \
            '(.*\.txt)|' \
            '(S_SKIN)|' \
            '(SPRTINFO)')
        if p.match(nodename):
            # Force LF line breaks for text files
            with open(filename, mode='r', encoding='utf-8') as f:
                raw_file = f.read().replace('\r\n','\n')
        else:
            with open(filename, mode='rb') as f:
                raw_file = f.read()


        self.writestr(arcname, raw_file,compress_type, compresslevel)
        
        return
        
        
        #zipfile.ZipFile.write(self, filename, arcname, compress_type, compresslevel)

    def writestr(self, zinfo_or_arcname, data, compress_type=None, compresslevel=None):
        if isinstance(zinfo_or_arcname, zipfile.ZipInfo):
            zinfo = zinfo_or_arcname
        else:
            zinfo = zipfile.ZipInfo(filename=zinfo_or_arcname)
            
        # Force deterministic metadata
        zinfo.filename = zinfo.filename.lstrip('/')
        zinfo.date_time = (1980, 1, 1, 0, 0, 0)
        zinfo.create_system = 3
        zinfo.external_attr = 0o0744 << 16  # Octal encoding for -rwxr--r--
        
        # Force LF line breaks to guarantee determinism
        zipfile.ZipFile.writestr(self, zinfo, data, compress_type, compresslevel)