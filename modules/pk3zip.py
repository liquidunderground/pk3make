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
    """
    def mkdir(self, zinfo_or_directory, mode=511):
        # Mode is overwritten to achieve determinism
        zipfile.ZipFile.mkdir(self, zinfo_or_directory, 511)
    """
    
    def write(self, filename, arcname, compress_type=None, compresslevel=None):
        
        nodename = pathlib.Path(filename).stem + pathlib.Path(filename).suffix
        
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
            with open(filename, mode='r') as f:
                raw_file = f.read()
            self.writestr(arcname, raw_file,compress_type, compresslevel)
            return
            
        zipfile.ZipFile.write(self, filename, arcname, compress_type, compresslevel)

    def writestr(self, zinfo_or_arcname, data, compress_type=None, compresslevel=None):
        # Force LF line breaks to guarantee determinism
        zipfile.ZipFile.writestr(self, zinfo_or_arcname, data.replace(f'\r\n',f'\n'), compress_type, compresslevel)
        
    def close(self):
        """PK3Files are lazy - they overwrite the metadata upon closure. Why? Because Windows
        """
        
        for metadata in self.infolist():
           
            metadata.create_system = 3
            metadata.date_time = (1980, 1, 1, 0, 0, 0)
            
            metadata.external_attr = 0o0744 << 16  # Octal encoding for -rwxr--r--
            if metadata.is_dir():
                metadata.external_attr = (0o40744 << 16) | 0x10  # Octal encoding for drwxr--r--
            
        zipfile.ZipFile.close(self)