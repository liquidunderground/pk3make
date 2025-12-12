class Palette:
    def __init__(self, filename):
        import os
        from PIL import Image

        self.colors = []
        self.color_lookup = {} # Color LUT to speed up rgb2index (before estimate: 25:16,32)

        # Colormath-based code commented out for future reference
        # Euclidean distance is 50x faster
        from colormath2.color_objects import sRGBColor, HSVColor, LabColor
        from colormath2.color_conversions import convert_color

        with Image.open(filename).convert("RGB") as img:
            # When it don't fit we make it fit
            rez_i = img.resize( (16,16), Image.Resampling.NEAREST)

            # Get pixels into self.colors
            width, height = rez_i.size # should be (16,16)
            for y in range(height):
                for x in range(width):
                    pixel = rez_i.getpixel((x,y))
                    #self.colors.append(pixel) # Tuple (R,G,B)

                    # Precalc color conversions to speed up rgb2index
                    px_srgb = sRGBColor(pixel[0], pixel[1], pixel[2], is_upscaled=True)
                    px_hsv = convert_color(px_srgb, HSVColor)
                    px_cielab = convert_color(px_srgb, LabColor)
                    
                    color_o = {
                        "id": y*height+x,
                        #"rgb": px_srgb, # COLORMATH STUB
                        "r": pixel[0],
                        "g": pixel[1],
                        "b": pixel[2],
                        "h": px_hsv.hsv_h,  # range: [0.0,360.0)
                        "s": px_hsv.hsv_s,  # range: [0.0,1.0]
                        "v": px_hsv.hsv_v,  # range: [0.0,1.0]
                        "cielab": px_cielab, # COLORMATH STUB
                    }

                    rgbcolor = (pixel[0] << 16) | (pixel[1] << 8) | (pixel[2])
                    self.colors.append(color_o) # Tuple (R,G,B)
                    self.color_lookup[rgbcolor] = color_o["id"]

    def rgb2index(self, color: tuple, color_conversion_method=None):
        
        if color_conversion_method not in ["euclidean_rgb"]:
            raise RuntimeError(f"RGB color conversion does not support method {color_conversion_method}. (How did we get here?)")       
        
        # Hot path O(1): Color matches exactly (most common if you know what you're doing)
        rgbcolor = (int(color[0]) << 16) | (int(color[1]) << 8) | int(color[2])
        
        if rgbcolor in self.color_lookup.keys():
            #print(f"Converting {color} => #{rgbcolor:X}")
            return self.colors[self.color_lookup[rgbcolor]]["id"]

        # Cold path: Linear search for the closest color
        min_delta_e = float('inf')
        min_idx = -1

        # Linear search w/ euclidean RGB distance
        # About 50x faster than LAB-distance, but very inaccurate
        for icolor in self.colors:
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


    def hsv2index(self, color: tuple, color_conversion_method=None):
        
        from colormath2.color_objects import AdobeRGBColor, HSVColor, LabColor
        from colormath2.color_conversions import convert_color
        from colormath2.color_diff import delta_e_cie2000
        
        if color_conversion_method not in ["cylindrical_hsv", "conical_hsv"]:
            raise RuntimeError(f"HSV color conversion does not support method {color_conversion_method}. (How did we get here?)")
        
        # Hot path O(1): Color matches exactly (most common if you know what you're doing)
        #color_lab = convert_color(HSVColor(color[0], color[1], color[2]), LabColor)
        color_rgb = convert_color(HSVColor(color[0], color[1], color[2]), AdobeRGBColor)
        rgbcolor = color_rgb.get_rgb_hex()

        # Hot path O(1): Color matches exactly (most common if you know what you're doing)
        if rgbcolor in self.color_lookup.keys():
            #print(f"Converting {color} => #{rgbcolor:X}")
            return self.colors[self.color_lookup[rgbcolor]]["id"]

        # Cold path: Linear search for the closest color
        min_delta_e = float('inf')
        min_idx = -1

        # Linear search w/ CIE 2000 LAB distance
        for icolor in self.colors:
            #print(f"ICOLOR {index}: {icolor}")

            """
            delta_e = ( \
                # Brightness
                (color[2]-icolor['r'])**2 + \
                # Chroma (saturation*brightness)
                (color[1]-icolor['g'])**2 + \
                # Hue (circular)
                (color[0]-icolor['b'])**2 \
            )**(1/2)

            delta_e = delta_e_cie2000(color_lab, icolor["cielab"])
            """
            
            # Normalize all values to range(0,1), then euclidean distance over the cylinder
            delta_e = ( \
                # Brightness
                (color[2]-icolor['v'])**2 + \
                # Saturation ("cylindrical_hsv") or Chroma ("conical_hsv")
                ( (color[1]-icolor['s'])**2
                    if color_conversion_method == "cylindrical_hsv"
                    else ((color[2]*color[1])-(icolor['v']*icolor['s']))**2 ) +
                # Hue (circular distance)
                ( min( abs(color[0]-icolor['h']), 360-abs(color[0]-icolor['h']) ) / 180.0 )**2 \
            )**(1/2)

            #delta_e = delta_e_cie2000(color_lab, icolor["cielab"])
            
            
            if delta_e < min_delta_e:
                min_delta_e = delta_e
                min_idx = icolor["id"]
            if delta_e == 0: # Exact match, no need to continue
                break

        return min_idx
    

    def lab2index(self, color: tuple, color_conversion_method=None):
        # Colormath-based code commented out for future reference
        # Euclidean distance is 50x faster
        from colormath2.color_objects import AdobeRGBColor, LabColor
        from colormath2.color_conversions import convert_color
        from colormath2.color_diff import delta_e_cie2000, delta_e_cie1976
        
        if color_conversion_method not in ["cie76", "cie2000"]:
            raise RuntimeError(f"L*a*b color conversion does not support method {color_conversion_method}. (How did we get here?)")

        # Hot path O(1): Color matches exactly (most common if you know what you're doing)
        color_rgb = convert_color(LabColor(color[0], color[1], color[2]), AdobeRGBColor)
        rgbcolor = color_rgb.get_rgb_hex()
        #rgbcolor = (int(color_rgb.rgb_r) << 16) | (int(color_rgb.rgb_g) << 8) | int(color_rgb.rgb_b)
        
        if rgbcolor in self.color_lookup.keys():
            print(f"Converting {color} => #{rgbcolor:X}")
            return self.colors[self.color_lookup[rgbcolor]]["id"]

        # Cold path: Linear search for the closest color
        #color_lab = convert_color(sRGBColor(color[0], color[1], color[2], is_upscaled=True), LabColor)
        min_delta_e = float('inf')
        min_idx = -1

        color_lab = LabColor(color[0], color[1], color[2])

        for icolor in self.colors:
            #print(f"ICOLOR {index}: {icolor}")

            delta_e = float("inf")

            match color_conversion_method:
                case "cie2000":
                    delta_e = delta_e_cie2000(color_lab, icolor["cielab"])
                case "cie76":
                    delta_e = delta_e_cie1976(color_lab, icolor["cielab"])
            
            
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


    def colormap_tobytes(self, color_conversion_method="conical_hsv"):
        from colormath2.color_objects import HSVColor, sRGBColor, LabColor
        from colormath2.color_conversions import convert_color
        from math import exp, log

        out = bytearray()
        levels = 32 # Default amount of brightness levels. Might be adjustable in the future for non-Weissblatt projects

        match color_conversion_method:
            case "euclidean_rgb":
                
                print("Using euclidean RGB interpolation")

                # Y/X coordinate loop because loop order matters
                for c,v in [(c,v) for v in range(levels) for c in range(256)]:
                    # Simple RGB squash
                    brightness = ( \
                                    self.colors[c]["r"] * (1-(v/(levels-1))), \
                                    self.colors[c]["g"] * (1-(v/(levels-1))), \
                                    self.colors[c]["b"] * (1-(v/(levels-1))) \
                                )
                    
                    out += self.rgb2index(brightness, color_conversion_method=color_conversion_method).to_bytes(1)

            case "cylindrical_hsv" | "conical_hsv":
                
                print("Using HSV interpolation")

                hsv_black = HSVColor(240, 0.0, 0.0)

                # Y/X coordinate loop because loop order matters
                for c,v in [(c,v) for v in range(levels) for c in range(256)]: # HSV-based interpolation
                    
                    """
                    input_hsv = convert_color( sRGBColor( \
                                self.colors[c]["r"], \
                                self.colors[c]["g"], \
                                self.colors[c]["b"] \
                                ), HSVColor)
                    """
                    
                    
                    """
                    input_hsv.hsv_h,
                    input_hsv.hsv_s,
                    # Squash [0.0;255.0] to [0.0;1.0] and apply brightness fade
                    (input_hsv.hsv_v/255.0) * (1.0-v/(levels-1))
                    """

                    # Simple linear brightness interpolation
                    output_hsv = HSVColor(
                                            #input_hsv.hsv_h * (1-v/(levels-1)) + hsv_black.hsv_h * v/(levels-1),
                                            #(((hsv_black.hsv_h-self.colors[c]["h"]) + 180) % 360 - 180)*v/(levels-1),
                                            self.colors[c]["h"],
                                            self.colors[c]["s"] * (1-v/(levels-1)) + hsv_black.hsv_s * v/(levels-1),
                                            self.colors[c]["v"] * (1-v/(levels-1)) + (hsv_black.hsv_v) * v/(levels-1)
                                        )

                    out += self.hsv2index(output_hsv.get_value_tuple(), color_conversion_method=color_conversion_method).to_bytes(1)

            case "cie76" | "cie2000":
                
                print("Using CIELAB interpolation")

                lab_black = convert_color(sRGBColor(0,0,0), LabColor)

                # Y/X coordinate loop because loop order matters
                for c,v in [(c,v) for v in range(levels) for c in range(256)]:
                    # LAB conversion
                    
                    input_lab = self.colors[c]["cielab"]
                    scale = v/(levels-1)
                    
                    # Actual LAB-based interpolation
                    if v == 32: # Full dark
                        print(f"RGB {(self.colors[c]["r"], self.colors[c]["g"], self.colors[c]["b"])} -> L*a*b color: {input_lab}\n")
                    output_lab = LabColor(
                                            input_lab.lab_l * (1-scale) + lab_black.lab_l * scale,
                                            input_lab.lab_a * (1-scale) + lab_black.lab_a * scale,
                                            input_lab.lab_b * (1-scale) + lab_black.lab_b * scale
                                        )

                    out += self.lab2index(output_lab.get_value_tuple(), color_conversion_method=color_conversion_method).to_bytes(1)


            case _:
                raise RuntimeError(f'Unknown color conversion method "{color_conversion_method}".')

        return out

    def tinttab_tobytes(self, factor:float, conversion="rgb"):
        if type(factor) != float or not (0 <= factor <= 1):
            raise RuntimeError(f"Invalid TINTTAB factor {factor}")

        out = bytearray()

        match conversion:
            case "rgb":
                for x,y in [(x,y) for x in range(256) for y in range(256)]:

                    tintcolor = ( \
                                    self.colors[x]["r"] * (1-factor) + self.colors[y]["r"] * factor, \
                                    self.colors[x]["g"] * (1-factor) + self.colors[y]["g"] * factor, \
                                    self.colors[x]["b"] * (1-factor) + self.colors[y]["b"] * factor \
                                )
                    out += self.rgb2index(tintcolor).to_bytes(1)
            case "hsv":
                for x,y in [(x,y) for x in range(256) for y in range(256)]:

                    tintcolor = ( \
                                    # Linearly interpolate the angle of the hue circle
                                    (((self.colors[y]["h"]-self.colors[x]["h"]) + 180) % 360 - 180)*factor, \
                                    self.colors[x]["s"] * (1-factor) + self.colors[y]["s"] * factor, \
                                    self.colors[x]["v"] * (1-factor) + self.colors[y]["v"] * factor \
                                )
                    out += self.hsv2index(tintcolor).to_bytes(1)
            case "lab":
                for x,y in [(x,y) for x in range(256) for y in range(256)]:

                    tintcolor = ( \
                                    self.colors[x]["cielab"].lab_l * (1-factor) + self.colors[y]["cielab"].lab_l * factor, \
                                    self.colors[x]["cielab"].lab_a * (1-factor) + self.colors[y]["cielab"].lab_a * factor, \
                                    self.colors[x]["cielab"].lab_b * (1-factor) + self.colors[y]["cielab"].lab_b * factor \
                                )
                    out += self.lab2index(tintcolor).to_bytes(1)
            case _:
                raise Exception(f"Invalid color conversion method \"{conversion}\". Check tinttab definition for <++>")
            
        return out


class Flat():
    def __init__(self, pngfile: str, palette: Palette):
        from PIL import Image

        self.pixelbuf = bytearray()
        with Image.open(pngfile).convert("RGBA") as img:

            # Get pixels into self.pixelbuf
            self.width, self.height = img.size # should be

            """# Removed to support FADEs
            if self.width != self.height:
                raise RuntimeError(f"Flat is not square. ({self.width},{self.height})")
            """

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

        tokens = re.match(r"\s*([^\s]+)\s*", offset)
        if not tokens:
            raise Exception(f'Offset "{offset}" not supported')

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
        # COLUMNS are arrays of POSTS separated by 0xFF
        # [POSTS]
        # uint8_t LE topdelta
        # uint8_t LE length
        # uint8_t LE padding
        # uint8_t* LE pixels
        # uint8_t LE padding


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
            # Post offset markers
            t_topdelta = -1
            t_topoffset = -1
            t_olddelta = -1
            t_postheight = 0
            dbg_postcounter = 0
            for y in range(self.height):

                ## Tall patch support ##

                if  y == 254: # Tall patch border
                    if  t_insidepost:
                        # Abort post now, restart as usual
                        t_cdata.extend(t_postheight.to_bytes(1, byteorder="little")) # Unused padding
                        t_cdata.extend(b'\x00') # Unused padding
                        t_cdata.extend(t_pdata) # Post data
                        t_cdata.extend(b'\x00') # Unused padding
                        t_pdata = bytearray() # Reset post data

                    # Insert Fake post
                    t_cdata.extend(b'\xfe\x00\x00\x00')
                    t_topdelta = y # Flush topdelta
                    t_postheight = 0
                    t_insidepost = False

                ## Actual algorithm ##

                current_pixel = self.pixelbuf[y*self.width+x]
                if (current_pixel == -1 or t_postheight == 254) and t_insidepost: # Post END
                    t_cdata.extend(t_postheight.to_bytes(1, byteorder="little")) # Unused padding
                    t_cdata.extend(b'\x00') # Unused padding
                    t_cdata.extend(t_pdata) # Post data
                    t_cdata.extend(b'\x00') # Unused padding
                    t_pdata = bytearray() # Reset post data
                    t_insidepost = False
                if current_pixel != -1 and not t_insidepost: # Post START

                    # Tall patch tracking
                    t_olddelta = t_topdelta
                    t_topdelta = y
                    t_topoffset = y if y < 254 else t_topdelta - t_olddelta

                    # Start new post
                    t_postheight = 1
                    t_cdata.extend((t_topoffset&0xFF).to_bytes(1, byteorder="little"))
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
