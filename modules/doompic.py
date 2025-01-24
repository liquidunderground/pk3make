class Palette:
    colors = []
    def __init__(self, filename):
        from pillow import Image
        with Image.open(filename) as img:
            # When it don't fit we make it fit
            rez_i = img.resize( (16,16), pillow.Resampling.NEAREST)
            rawimg = rez_i.load()

            # Get pixels into self.colors
            width, height = rawimg.size # should be (16,16)
            for y in range(height):
                for x in range(width):
                    pixel = rawimg[x,y]
                    self.colors.append(pixel)

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
    def tobytes(self):
        # Convert self.colors to Doom Palette
        # Return as IOBytes for saving
        exbytes = bytearray()
        for page in Range(14):
            for i in Range(256):
                # Default unused palette: Grayscale
                r = 255-i
                g = 255-i
                b = 255-i

                if i = 0: # Regular palette
                    r = [i*3]
                    g = [i*3]+1
                    b = [i*3]+2
                elif i = 4: # Nuke palette => 75% white tint + g,b = 113
                    r = self.colors[i*3]+ (255 - self.colors[i*3]) * 0.75
                    g = 113
                    b = 113
                elif 2 <= i <= 3: # Whiteout palettes => 75% white tint
                    r = self.colors[i*3]+ (255 - self.colors[i*3]) * 0.75
                    g = self.colors[i*3+1]+ (255 - self.colors[i*3+1]) * 0.75
                    b = self.colors[i*3+2]+ (255 - self.colors[i*3+2]) * 0.75
            # Add color idx
            exbytes.append(r)
            exbytes.append(g)
            exbytes.append(b)
        return bytes(exbytes)

### MAIN CONVERTER FUNCTIONS ###

def png2pic(pngfile, palette, xoffset=0, yoffset=0):
    from pillow import Image
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
