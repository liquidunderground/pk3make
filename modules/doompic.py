class Palette:
    colors = []
    def __init__(self, srcdir, lumpname):
    #def __init__(self, filename):
        import os
        from modules.doomglob import find_lump, DuplicateLumpError
        from PIL import Image

        filename = find_lump(srcdir, lumpname)
        print (f"DOOMGLOB FIND : {filename}")

        if len(filename) > 1:
            raise DuplicateLumpError(f"Color palette {lumpname} is not unique.")

        with Image.open(os.path.join(srcdir,filename[0][1])).convert("RGB") as img:
            # When it don't fit we make it fit
            rez_i = img.resize( (16,16), Image.Resampling.NEAREST)

            # Get pixels into self.colors
            width, height = rez_i.size # should be (16,16)
            for y in range(height):
                for x in range(width):
                    pixel = rez_i.getpixel((x,y))
                    self.colors.append(pixel) # Tuple (R,G,B)

    def rgb2index(self, color: tuple):
        from colormath2.color_objects import sRGBColor, LabColor
        from colormath2.color_conversions import convert_color
        from colormath2.color_diff import delta_e_cie2000

        color_lab = convert_color(sRGBColor(color[0], color[1], color[2], is_upscaled=True), LabColor)
        min_delta_e = float('inf')
        min_idx = int
        for index,icolor in enumerate(self.colors):
            #print(f"ICOLOR {index}: {icolor}")
            icolor_lab = convert_color(sRGBColor(icolor[0], icolor[1], icolor[2], is_upscaled=True), LabColor)
            delta_e = delta_e_cie2000(color_lab, icolor_lab)
            if delta_e < min_delta_e:
                min_delta_e = delta_e
                min_idx = index
            if delta_e == 0: # Exact match, no need to continue
                break
        #print(f"Found color {min_idx}:{self.colors[min_idx]} for image color {color}")
        return min_idx

    def generate_colormap(self):
        return

    def tobytes(self):
        # Convert self.colors to Doom Palette
        # Return as IOBytes for saving
        exbytes = bytearray()
        for page in range(14):
            for i in range(256):
                # Default unused palette: Grayscale
                r = 255-i
                g = 255-i
                b = 255-i

                if page == 0: # Regular palette
                    r = self.colors[i][0]
                    g = self.colors[i][1]
                    b = self.colors[i][2]
                elif 0 < page < 4: # Whiteout palettes => 75% white tint
                    r = self.colors[i][0] + (255 - self.colors[i][0]) * 0.75
                    g = self.colors[i][1] + (255 - self.colors[i][1]) * 0.75
                    b = self.colors[i][2] + (255 - self.colors[i][2]) * 0.75
                elif page == 4: # Nuke palette => 75% white tint + g,b = 113
                    r = self.colors[i][0] + (255 - self.colors[i][0]) * 0.75
                    g = 113
                    b = 113
                elif page == 5: # Inverted palette at 75% brightness
                    r = (255 - self.colors[i][0]) * 0.75
                    g = (255 - self.colors[i][1]) * 0.75
                    b = (255 - self.colors[i][2]) * 0.75
                # Add color idx.
                # NOTE: the int() cast is janky but hopefully works
                exbytes.append(int(r))
                exbytes.append(int(g))
                exbytes.append(int(b))
        return bytes(exbytes)

    def colormap_tobytes(self):
        return

class Flat():
    def __init__(self, pngfile: str, palette: Palette):
        from PIL import Image

        self.pixelbuf = bytearray()
        with Image.open(pngfile).convert("RGBA") as img:
            rawimg = img.load()

            # Get pixels into self.pixelbuf
            self.width, self.height = img.size # should be
            for y in range(self.height):
                for x in range(self.width):
                    pixel = rawimg[x,y]
                    # Flat = Raw paletted pixel dump
                    self.pixelbuf += palette.rgb2index(pixel).to_bytes(1,"little")

    def get_size(self):
        return (self.width, self.height)

    def tobytes(self):
        return bytes(self.pixelbuf)

class Picture():
    def __init__(self, pngfile: str, palette: Palette, *args):
        from PIL import Image

        if "offset" in args:
            self.set_offset(offset)

        self.palette = palette # Prolly unused but can't hurt

        with Image.open(pngfile) as img:
            # Get pixels into self.colors
            self.width, self.height = img.size # should be
            for y in range(self.height):
                for x in range(self.width):
                    pixel = img.getpixel( (x,y) )
                    print(f"PIXEL ({x},{y}) = {pixel}")
                    # Flat = Raw paletted pixel dump
                    self.pixelbuf[x,y] = palette.rgb2index(pixel[0], pixel[1], pixel[2], pixel[3])

        return bytes(flatout) # Doom flat lump

    def set_offset(offset: str):
        import re

        if re.match("[0-9]* [0-9]*"):
            tokens = re.search("([0-9]*) ([0-9]*)")
            self.offsetX = int(tokens.group(1))
            self.offsetY = int(tokens.group(2))
            return

        match offset:
            case "": # No offset given - default to "0 0"
                self.offsetX = 0
                self.offsetY = 0
            case "center":
                self.offsetX = self.width/2
                self.offsetY = self.height/2
            case "sprite":
                self.offsetX = self.width/2
                self.offsetY = self.height-4
            case _:
                raise Exception(f'Offset "{offset}" not supported')
        return

    def tobytes(self):
        # === Generate picture lump ===
        #
        # [HEADER]
        # uint16_t LE width
        # uint16_t LE height
        # uint16_t LE offsetX
        # uint16_t LE offsetY
        # uint32_t[width] LE toc
        # -----------------------------
        # [COLUMN]
        # uint8_t LE width
        # uint8_t LE width
        # uint8_t LE width
        # uint8_t LE width


        columns = []
        out = bytearray
        # --- Create Header ---
        # NOTE: All integers in a Picture header are LE uint16_t
        out.append(self.width.to_bytes(2, byteorder='little'))
        out.append(self.height.to_bytes(2, byteorder='little'))
        out.append(self.offsetX.to_bytes(2, byteorder='little'))
        out.append(self.offsetY.to_bytes(2, byteorder='little'))

        # Iterate Column-wise. Yes, Doom picture are column-oriented
        toc = bytearray() # Table of Columns
        t_fseek = len(out) + 4 * self.width # whXY + column TOC
        for x in range(width):
            t_cdata = bytearray # Column data
            t_pdata = bytearray # Post data
            t_insidepost = False
            t_topdelta = 0
            t_postheight = 0
            for y in range(column):
                # Yes. Doom pictures partition their columns into posts
                pixel_alpha = self.pixelbuf[x,y][3] 
                if pixel_alpha == 0 and insidepost: # Column END
                    t_cdata.append(t_postheight.to_bytes(1, byteorder="little")) # Unused padding
                    t_cdata.append(0x00) # Unused padding
                    t_cdata.append(t_pdata) # Post data
                    t_cdata.append(0xff) # Unused padding
                    t_insidepost = False
                elif pixel_alpha != 0 and not insidepost: # Column START
                    t_topdelta = y
                    t_postheight = 1
                    t_cdata.append(t_topdelta)
                    t_pdata.append(self.pixelbuf[x,y])
                    insidepost = True
                elif pixel_alpha != 0 and insidepost:
                    t_pdata.append(self.pixelbuf[x,y])
                    t_postheight = t_postheight + 1

                t_cdata.append(0xff) # Column terminator
            columns.append(t_cdata) # Save partitioned column whole

            out.append(toc) # Finish off header
            for col in columns: # Write column data block
                out.append(col)

        return bytes(out)

# ========================================= #

#def png2fade(pngfile, palette):
    #return png2flat(pngfile, palette) # Fade lump. Are Fades really just flats?
