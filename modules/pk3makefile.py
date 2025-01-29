class PK3MakeConfigurationError(Exception):
    """To be raised when a lump should really be unique"""
    pass

class PK3MakeDependencyError(Exception):
    """To be raised when a lump should really be unique"""
    pass

class PK3Makefile():
    #def __init__(self):
        #pass

    def __init__(self, filename):
        import re

        self.options = {
            "srcdir": None,
            "workdir": None,
            "destfile": None,
            "palette": None,
        }

        self.lumps = []

        # List of tuples ( LUMPNAME, TYPE, OFFSET )
        # OFFSET may either be an interger tuple or a string

        with open(filename) as file:
            for line in file:
                re_buildopt = r"^\?([^\s]*): ([^\s]*)"
                re_lumpdef = r"^([^\s]+)\s*([^\s]+)(?:\s*(.+))?"

                workline = re.sub(r"#.*","", line) # Clean out comments
                tokens = re.match(re_buildopt, workline)
                if tokens: # Is it a Buildopt?
                    match tokens.group(1):
                        case "srcdir" | "workdir" | "destfile" | "palette" as cmd:
                            self.options[cmd] = tokens.group(2)
                tokens = re.match(re_lumpdef, workline)
                if tokens: # Is it a Lumpdef?
                    match tokens.group(2):
                        case "flat" | "fade" | "graphic" | "raw" | "colormap"| "tinttab" | "palette" | "marker" as cmd:
                            self.lumps.append( tokens.group(1,2,3) )
                        case "udmf":
                            print(f'Lump type "udmf" is not supported yet. Ignored')
                        case _ as lumptype:
                            print(f'Invalid lumptype "{lumptype}". Ignored')

    def get_options(self, option=None):
        if option == None:
            return self.options
        else:
            return self.options[option]

    def get_lumpdefs(self):
        return self.lumps
