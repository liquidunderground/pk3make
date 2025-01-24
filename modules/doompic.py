class Palette:
    colors = []
    def __init__(self, srcdir, lumpname):
    #def __init__(self, filename):
        import os
        from modules import doomglob
        from PIL import Image
        filename = doomglob.find_lump(srcdir, lumpname)
        print (f"DOOMGLOB FIND : {filename}")

        if len(filename) > 1:
            raise Exception("Lump name is not unique")

        with Image.open(os.path.join(srcdir,filename[0][1])) as img:
            # When it don't fit we make it fit
            rez_i = img.resize( (16,16), Image.Resampling.NEAREST)
            rawimg = rez_i.load()

            # Get pixels into self.colors
            width, height = rez_i.size # should be (16,16)
            for y in range(height):
                for x in range(width):
                    pixel = rawimg[x,y]
                    self.colors.append(pixel[0]) # Red
                    self.colors.append(pixel[1]) # Green
                    self.colors.append(pixel[2]) # Brue

    def rgb2index(self, color):
        import colormath
        print("rgb2index is not implemented yet ;p")
        # TODO: Return closest index using colormath
        col_needle = colormath.color_conversions.convert_color(colormath.sRGBColor(color), colormath.LabColor)
        min_delta_e = float('inf')
        for index in self.colors:
            sRGBColor
            delta_e = delta_e_cie2000(col_needle)
            if delta_e < min_delta_e:
                min_delta_e = delta_e
        return 

    def generate_colormap(self):
        return

    def tobytes(self):
        # Convert self.colors to Doom Palette
        # Return as IOBytes for saving
        exbytes = bytearray()
        for page in range(14):
            print(f"GENERATING PAGE {page}")
            for i in range(256):
                # Default unused palette: Grayscale
                r = 255-i
                g = 255-i
                b = 255-i

                if page == 0: # Regular palette
                    r = self.colors[i*3]
                    g = self.colors[i*3+1]
                    b = self.colors[i*3+2]
                elif 0 < page < 4: # Whiteout palettes => 75% white tint
                    r = self.colors[i*3]+ (255 - self.colors[i*3]) * 0.75
                    g = self.colors[i*3+1]+ (255 - self.colors[i*3+1]) * 0.75
                    b = self.colors[i*3+2]+ (255 - self.colors[i*3+2]) * 0.75
                elif page == 4: # Nuke palette => 75% white tint + g,b = 113
                    r = self.colors[i*3]+ (255 - self.colors[i*3]) * 0.75
                    g = 113
                    b = 113
                elif page == 5: # Inverted palette at 75% brightness
                    r = (255 - self.colors[i*3]) * 0.75
                    g = (255 - self.colors[i*3+1]) * 0.75
                    b = (255 - self.colors[i*3+2]) * 0.75
                # Add color idx.
                # NOTE: the int() cast is janky but hopefully works
                exbytes.append(int(r))
                exbytes.append(int(g))
                exbytes.append(int(b))
        return bytes(exbytes)

    def colormap_tobytes(self):
        return

### MAIN CONVERTER FUNCTIONS ###

def png2pic(pngfile, palette, xoffset=0, yoffset=0):
    from PIL import Image
    # TODO: PNG IN -> DOOM Pic OUT
    print("png2pic is not implemented yet ;p")
    picout = bytearray()
    with Image.open(filename) as img:
        # When it don't fit we make it fit
        rawimg = img.load()

        # Get pixels into self.colors
        width, height = rawimg.size # should be (16,16)
        for y in range(height):
            for x in range(width):
                pixel = rawimg[x,y]
                # Flat = Raw paletted pixel dump
                self.colors.append(palette.rgb2index(pixel))
    return # Pic lump

def png2flat(pngfile, palette):
    # TODO: PNG IN -> DOOM Flat OUT
    print("png2flat is not implemented yet ;p")
    flatout = bytearray
    with Image.open(filename) as img:
        # When it don't fit we make it fit
        rawimg = img.load()

        # Get pixels into self.colors
        width, height = rawimg.size # should be
        for y in range(height):
            for x in range(width):
                pixel = rawimg[x,y]
                # Flat = Raw paletted pixel dump
                self.colors.append(palette.rgb2index(pixel))
    return bytes(flatout) # Doom flat lump

def png2fade(pngfile, palette):
    return png2flat(pngfile, palette) # Fade lump. Are Fades really just flats?
