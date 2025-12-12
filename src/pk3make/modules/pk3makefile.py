import warnings

class PK3MakeConfigurationError(Exception):
    """To be raised when a lump should really be unique"""
    pass

class PK3MakeDependencyError(Exception):
    """To be raised when a lump should really be unique"""
    pass

import enum,zipfile

Compression = {
    "none"            :   zipfile.ZIP_STORED,
    "uncompressed"    :   zipfile.ZIP_STORED,
    "lzma"            :   zipfile.ZIP_LZMA,
    "bzip2"           :   zipfile.ZIP_BZIP2,
    "zlib"            :   zipfile.ZIP_DEFLATED,
    "zstd"            :   zipfile.ZIP_ZSTANDARD
}

color_conversion_methods = [
    "euclidean_rgb",
    "cylindrical_hsv",
    "conical_hsv",
    "cie76",
    "cie2000",
]

class PK3Makefile():
    #def __init__(self):
        #pass

    def __init__(self, filename):
        import re

        self.options = {}
        self.lumps = []

        # List of tuples ( LUMPNAME, TYPE, OFFSET )
        # OFFSET may either be an interger tuple or a string

        with open(filename) as file:

            re_lumpdef = r"^\s*([^\s$#]+)\s*([^\s$#]+)(?:\s*([^\$#]+))?"
            re_buildopt = r"^\s*\$(\S+)\s*=\s*(.+)"
            re_lumpdef_kwargs = r"(?::(\S+)=(\S+))"

            #re_lumpdef = r"^\s*([^\s\?#]+)\s*([^\s\?#]+)(?:\s*([^\?#]+))?"
            #re_buildopt = r"^\s*\?(\S+)\s*:\s*(.+)"
            
            for line in file:
                """
                re_buildopt = r"^\?([^\s]*): ([^\s]*)"
                re_lumpdef = r"^([^\s]+)\s*([^\s]+)(?:\s*(.+))?"
                """
                workline = re.sub(r"#.*","", line).strip() # Clean out comments
                
                tokens = re.match(re_buildopt, workline)
                if tokens: # Is it a Buildopt?
                    self.options[tokens.group(1)] = tokens.group(2).rstrip()
                
                tokens = re.match(re_lumpdef, workline)
                if tokens: # Is it a Buildopt?
                    
                    print(f"TOKENS: {tokens}")

                    lumpdef_kwargs = {}

                    #parameters_raw = tokens.group(3).split()
                    if tokens.group(3) != None:
                        lumpdef_kwargs = {m.group(1):m.group(2) for m in re.finditer(re_lumpdef_kwargs, tokens.group(3))}

                    self.lumps.append( (tokens.group(1),tokens.group(2), lumpdef_kwargs) )

                """
                tokens = re.match(re_buildopt, workline)
                if tokens: # Is it a Buildopt?
                    match tokens.group(1):
                        case "srcdir" | "workdir" | "destfile" | "palette" | "compression" | "compression_level" as cmd:
                            self.options[cmd] = tokens.group(2).rstrip('/')
                tokens = re.match(re_lumpdef, workline)
                if tokens: # Is it a Lumpdef?
                    match tokens.group(2):
                        case "flat" | "fade" | "graphic" | "raw" | "colormap"| "tinttab" | "palette" | "marker" as cmd:
                            self.lumps.append( tokens.group(1,2,3) )
                        case "udmf":
                            warnings.warn(f'Lump type "udmf" is not supported yet. Ignored')
                        case _ as lumptype:
                            warnings.warn(f'Invalid lumptype "{lumptype}". Ignored')
                """

            print(f"BUILDOPTS: {self.options}")
            print(f"HEAD OF LUMPDEFS: {self.lumps[:10]}")

            # Throw a bunch of exceptions for things we care about before stuff can go wrong.
            if "srcdir" not in self.options.keys():
                raise RuntimeError("No srcdir specified. Add a valid path to your PK3Makefile's buildopt.")
            if "workdir" not in self.options.keys():
                raise RuntimeError("No workdir specified. Add a valid path to your PK3Makefile's buildopt.")
            if "destfile" not in self.options.keys():
                raise RuntimeError("No destfile specified. Add a valid path to your PK3Makefile's buildopt.")
            
            if "compression" not in self.options.keys():
                raise RuntimeError("No compression scheme specified. Add a valid path to your PK3Makefile's buildopt.")
            if "compression_level" not in self.options.keys():
                raise RuntimeError("No compression level specified. Add a valid path to your PK3Makefile's buildopt.")
            
            if "palette" not in self.options.keys():
                raise RuntimeError("No default color palette specified. Add $palette to your PK3Makefile.")
            

            # Data-based exceptions
            if self.options["compression"] not in Compression.keys():
                raise RuntimeError(f'Invalid compression scheme "{self.options["compression"]}". Valid compression schemes include {Compression.keys()}.')
            
            if self.options["default_color_conversion_method"] not in color_conversion_methods:
                raise RuntimeError(f'Invalid color conversion method "{self.options["default_color_conversion_method"]}". Valid compression schemes include {color_conversion_methods}.')

                
                

    def get_options(self, option=None):
        if option == None:
            return self.options
        else:
            return self.options[option]

    def get_lumpdefs(self):
        return self.lumps
    
    def filter_lumpdefs(self, pattern):
        import re,fnmatch

        glob_re = re.compile(fnmatch.translate(pattern))

        self.lumps = [x for x in self.lumps if glob_re.match(x[0])]

        return self
