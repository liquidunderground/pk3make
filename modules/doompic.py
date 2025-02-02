class Palette:
    colors = []
    def __init__(self, filename):
        import os
        from modules.doomglob import find_lump, DuplicateLumpError
        from PIL import Image

        # Colormath-based code commented out for future reference
        # Euclidean distance is 50x faster
        """
        from colormath2.color_objects import sRGBColor, LabColor
        from colormath2.color_conversions import convert_color
        from colormath2.color_diff import delta_e_cie2000
        """

        with Image.open(filename).convert("RGB") as img:
            # When it don't fit we make it fit
            rez_i = img.resize( (16,16), Image.Resampling.NEAREST)

            # Get pixels into self.colors
            width, height = rez_i.size # should be (16,16)
            for y in range(height):
                for x in range(width):
                    pixel = rez_i.getpixel((x,y))
                    #self.colors.append(pixel) # Tuple (R,G,B)

                    # Precalc color conversions to speed up rgb2index - UPDATE: No bc fuck colormath
                    #px_srgb = sRGBColor(pixel[0], pixel[1], pixel[2], is_upscaled=True) # COLORMATH STUB
                    #px_cielab = convert_color(px_srgb, LabColor) # COLORMATH STUB
                    color_o = {
                        "id": y*height+x,
                        #"rgb": px_srgb, # COLORMATH STUB
                        "r": pixel[0],
                        "g": pixel[1],
                        "b": pixel[2],
                        #"cielab": px_cielab, # COLORMATH STUB
                    }
                    self.colors.append(color_o) # Tuple (R,G,B)

    def rgb2index(self, color: tuple):
        # Colormath-based code commented out for future reference
        # Euclidean distance is 50x faster
        """
        from colormath2.color_objects import sRGBColor, LabColor
        from colormath2.color_conversions import convert_color
        from colormath2.color_diff import delta_e_cie2000
        """

        #color_lab = convert_color(sRGBColor(color[0], color[1], color[2], is_upscaled=True), LabColor)
        min_delta_e = float('inf')
        min_idx = -1
        for icolor in self.colors:
            """
            #print(f"ICOLOR {index}: {icolor}")
            #icolor_lab = convert_color(sRGBColor(icolor[0], icolor[1], icolor[2], is_upscaled=True), LabColor)
            delta_e = delta_e_cie2000(color_lab, icolor["cielab"])
            """
            # Simple euclidean distance
            delta_e = ( \
                (color[0]-icolor['r'])**2 + \
                (color[1]-icolor['g'])**2 + \
                (color[2]-icolor['b'])**2 \
            )**(1/2)
            if delta_e < min_delta_e:
                min_delta_e = delta_e
                min_idx = icolor["id"]
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
            for i,pcolor in enumerate(self.colors):
                # Default unused palette: Grayscale
                r = 255-i
                g = 255-i
                b = 255-i

                if page == 0: # Regular palette
                    r = pcolor["r"]
                    g = pcolor["g"]
                    b = pcolor["b"]
                elif 0 < page < 4: # Whiteout palettes => 75% white tint
                    r = pcolor["r"] + (255 - pcolor["r"]) * 0.75
                    g = pcolor["g"] + (255 - pcolor["g"]) * 0.75
                    b = pcolor["b"] + (255 - pcolor["b"]) * 0.75
                elif page == 4: # Nuke palette => 75% white tint + g,b = 113
                    r = pcolor["r"] + (255 - pcolor["r"]) * 0.75
                    g = 113
                    b = 113
                elif page == 5: # Inverted palette at 75% brightness
                    r = (255 - pcolor["r"]) * 0.75
                    g = (255 - pcolor["g"]) * 0.75
                    b = (255 - pcolor["b"]) * 0.75
                # Add color idx.
                # NOTE: the int() cast is janky but hopefully works
                exbytes.append(int(r))
                exbytes.append(int(g))
                exbytes.append(int(b))
        return bytes(exbytes)

    def colormap_tobytes(self):
        """
        from colormath.color_objects import HSVColor, sRGBColor
        from colormath.color_conversions import convert_color
        """

        out = bytearray()
        # Y/X coordinate loop because loop order matters
        for c,v in [(c,v) for v in range(32) for c in range(256)]:

            """
            input_hsv = convert_color( sRGBColor( \
                        self.colors[c][0], \
                        self.colors[c][1], \
                        self.colors[c][2] \
                    , HSVColor)
            output_hsv = ( input_hsv[0], input_hsv[1], input_hsv[2] * (1-v/32) )
            output_rgb = sRGBColor()

            out += self.rgb2index(output_rgb.value_tuple())
            """

            # Simple RGB squash for now
            # TODO: Add HSV/LAB-conversion after testing
            brightness = ( \
                            self.colors[c]["r"] * (1-(v/32)), \
                            self.colors[c]["g"] * (1-(v/32)), \
                            self.colors[c]["b"] * (1-(v/32)) \
                        )
            out += self.rgb2index(brightness).to_bytes(1)
        return out

    def tinttab_tobytes(self, factor:float):
        if type(factor) != float or not (0 <= factor <= 1):
            raise RuntimeError(f"Invalid TINTTAB factor {factor}")

        out = bytearray()
        for x,y in [(x,y) for x in range(256) for y in range(256)]:
            tintcolor = ( \
                            self.colors[x]["r"] * (1-factor) + self.colors[y]["r"] * factor, \
                            self.colors[x]["g"] * (1-factor) + self.colors[y]["g"] * factor, \
                            self.colors[x]["b"] * (1-factor) + self.colors[y]["b"] * factor \
                        )
            out += self.rgb2index(tintcolor).to_bytes(1)
        return out


class Flat():
    def __init__(self, pngfile: str, palette: Palette):
        from PIL import Image

        self.pixelbuf = bytearray()
        with Image.open(pngfile).convert("RGBA") as img:

            # Get pixels into self.pixelbuf
            self.width, self.height = img.size # should be

            if self.width != self.height:
                raise RuntimeError(f"Flat is not square. ({self.width},{self.height})")

            for y in range(self.height):
                for x in range(self.width):
                    pixel = img.getpixel((x,y))
                    # Flat = Raw paletted pixel dump
                    self.pixelbuf += palette.rgb2index(pixel).to_bytes(1,"little")

    def get_size(self):
        return (self.width, self.height)

    def tobytes(self):
        return bytes(self.pixelbuf)

class Picture():
    def __init__(self, pngfile: str, palette: Palette, **kwargs):
        from PIL import Image

        self.palette = palette # Prolly unused but can't hurt

        self.pixelbuf = []
        with Image.open(pngfile).convert("RGBA") as img:

            # Get pixels into self.pixelbuf
            self.width, self.height = img.size # should be
            for y in range(self.height):
                for x in range(self.width):
                    pixel = img.getpixel((x,y))
                    # Save picture as indexed image (-1 = transparent)
                    if pixel[3] == 0:
                        self.pixelbuf.append( -1 )
                    else:
                        self.pixelbuf.append( palette.rgb2index(pixel) )

        if "offset" in kwargs:
            new_offset = self.set_offset(kwargs["offset"])


    def set_offset(self, offset: str):
        import re
        if offset == None or re.match(r"^\s*$", offset):
            self.offsetX = 0
            self.offsetY = 0
            return (self.offsetX, self.offsetY)

        tokens = re.match(r"\s*(-?[0-9]+)\s+(-?[0-9]+)\s*", offset)
        if tokens:
            self.offsetX = int(tokens.group(1))
            self.offsetY = int(tokens.group(2))
            return (self.offsetX, self.offsetY)

        tokens = re.match(r"\s+([^\s]+)\s*", offset)
        match tokens.group(1):
            case "": # No offset given - default to "0 0"
                self.offsetX = 0
                self.offsetY = 0
            case "center":
                self.offsetX = int(self.width/2)
                self.offsetY = int(self.height/2)
            case "sprite":
                self.offsetX = int(self.width/2)
                self.offsetY = int(self.height-4)
            case _:
                raise Exception(f'Offset "{offset}" not supported')
        return (self.offsetX, self.offsetY)

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


        columns = bytearray()
        # --- Create Header ---
        # NOTE: All integers in a Picture header are LE uint16_t
        out = bytearray( \
            self.width.to_bytes(2, byteorder='little') + \
            self.height.to_bytes(2, byteorder='little') + \
            self.offsetX.to_bytes(2, byteorder='little', signed=True) + \
            self.offsetY.to_bytes(2, byteorder='little', signed=True) \
            )

        # Iterate Column-wise. Yes, Doom picture are column-oriented
        toc = bytearray() # Table of Columns
        t_fseek = len(out) + 4 * self.width # whXY + column TOC
        for x in range(self.width):
            t_cdata = bytearray() # Column data
            t_pdata = bytearray() # Setup/Reset Post data
            t_insidepost = False
            t_topdelta = 0
            t_postheight = 0
            for y in range(self.height):
                # Yes. Doom pictures partition their columns into posts
                #print(f"Current Pixel ({x},{y}): {self.pixelbuf[y*self.width+x]}")
                current_pixel = self.pixelbuf[y*self.width+x]
                if ( current_pixel == -1 or y%255 >= 254 ) and t_insidepost: # Post END
                    t_cdata.extend(t_postheight.to_bytes(1, byteorder="little")) # Unused padding
                    t_cdata.extend(b'\x00') # Unused padding
                    t_cdata.extend(t_pdata) # Post data
                    t_cdata.extend(b'\x00') # Unused padding
                    #t_cdata.extend(b'\xff') # Column Terminator
                    t_pdata = bytearray() # Reset post data
                    t_insidepost = False
                elif current_pixel != -1 and not t_insidepost: # Post START
                    t_topdelta = y % 255 # Format seems to rely on overflow
                    t_postheight = 1
                    t_cdata.extend(t_topdelta.to_bytes(1, byteorder="little"))
                    t_pdata.extend(current_pixel.to_bytes(1, byteorder="little"))
                    t_insidepost = True
                elif current_pixel != -1 and t_insidepost:
                    t_pdata.extend(current_pixel.to_bytes(1, byteorder="little"))
                    t_postheight = t_postheight + 1

            if t_insidepost: # Finish last post if End Of Column
                t_cdata.extend(t_postheight.to_bytes(1, byteorder="little")) # Unused padding
                t_cdata.extend(b'\x00') # Unused padding
                t_cdata.extend(t_pdata) # Post data
                t_cdata.extend(b'\x00') # Unused padding
            t_cdata.extend(b'\xff') # Column Terminator

            columns.extend(t_cdata) # Save partitioned column whole

            # Add TOC column offset
            toc.extend(t_fseek.to_bytes(4, byteorder='little'))
            t_fseek = t_fseek+len(t_cdata)

        out.extend(toc) # Finish off header
        out.extend(columns) # Write column data block

        return bytes(out)
