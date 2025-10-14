# PK3Make - Build system for Weissblatt PK3 files

[PK3] is a package format for game mods based on ZIP. Although originally introduced by Quake III Arena, it has been adopted by modern source ports of Doom and by extension Weissblatt.

[PK3]: https://doomwiki.org/wiki/PK3

PK3Make lets you automatically convert Textures, Flats, FADEs, color palettes, COLORMAPs and TINTTABs into lumps for Weissblatt and package them into a tidy PK3. Additional features include:

- Deterministic PK3s - make sure that your project's PK3s are byte-for-byte reproducible
- [METAINFO]-inspired syntax with support for sprite offsets, marker definitions and Glob-based LUMPDEFs
- Bring your own PK3Makefile - Build different PK3s from the same asset tree
- Multi-threaded building
- Timestamp-based version checks - only build what's necessary as you develop

[METAINFO]: https://mtrop.github.io/DoomTools/dimgconv.html

## Installation

0. Set up a [virtual environment](https://docs.python.org/3/library/venv.html)
1. Install PK3Make: `pip install pk3make`
2. ???
3. Profits

## How to use

To fully build your project, simply run:

    pk3make
	
To get an overview of options for PK3Make, type:

    pk3make --help
	
	
By default, will use `./PK3Makefile` for it's PK3Makefile. Other can be given through `pk3make [PK3MAKEFILE]`. More on PK3Makefiles in the PK3Makefile reference below.

### Build steps

PK3Makefile defines four subcommands, each with their own unique options:

1. `pk3make clean`: Clean & remove the build directory
2. `pk3make build`: Compile the build directory.
3. `pk3make pack`: Assemble a PK3 file from the build directory's contents
4. `pk3make all`: Build and pack (Default).


### Notes, Tips and Caveats

All text files are assumed to be UTF-8 encoded. PK3Make will automatically attempt to convert CRLF to LF newlines but using LF newlines is recommended.

PK3Make will not find hidden files. To avoid `DuplicateLumpError`s, place
  your workfiles in a hidden directory, for example `.local/`.

Should your project contain custom palettes,  place it's corresponding
  LUMPDEF before any `graphic`, `flat` or `fade`. That way, PK3Make can
  cache your palettes and speed up build times by reducing thread idle.


## But why?

To put it bluntly: No other tools suited Weissblatt.

Although the PK3 specification for Weissblatt's engine is based on
[ZDoom PK3](https://zdoom.org/wiki/Using_ZIPs_as_WAD_replacement),
it's directory namespaces are very different. This made Doom's usual
autobuild toolkit [DoomTools](https://mtrop.github.io/DoomTools/) a
poor fit for development. Due to the size of the Weissblatt project, manual
assembly using SLADE was also out of the question.

I chose Python as the basis for PK3Make because it is platform-independent,
easy-to-read and ubiquitous and although some Doom/Weissblatt-specific
modules needed to be written from scratch for PK3Make, Python's vast
standard library and otherwise mature PyPI repository helped stem some
of the heavy lifting for things such as image processing.

# PK3Makefile reference

PK3Make uses it's own build definition language called `PK3Makefile`, inspired by the `METAINFO` spec from
[Matt Tropiano's dImgConv](https://mtrop.github.io/DoomTools/dimgconv.html).

`PK3Makefile`s are processed line-by-line with everything following `#`
being treated as a comment. Otherwise it is split into *Build Options*,
which define PK3Make's general behavior and *LUMPDEFS*, which define what
files to put into your PK3 and how to build them.

## Build options

Build options are specified per-line and follow the pattern

    ?<OPTION>: <PARAM>

PK3Make supports the following options:

`?srcdir: <DIR>` specifies the directory to pull it's base assets from.
PK3Make will attempt to find all defined lumps within this folder and
mirror it's path within `?workdir` after compilation.

`?workdir: <DIR>` specifies the temporary working directory. PK3Make will
check the timestamps between this and `?srcdir` and rebuild/copy any
outdated files into `?workdir` during the compilation process.

`?palette:` defines the main color palette, by `LUMPNAME` (`PLAYPAL` by default)

`?destfile: <PATH>` describes a filepath to the destination PK3. This is where `?workdir` will get copied to during packing.

`?compression: <TYPE>` and `?compression_level: <INT>` define file the destination PK3's compression method and level respectively. The following compression types are supported:

1. `none | uncompressed`: Used to create uncompressed PK3s (default)
2. `zlib`: zlib/DEFLATE-based compression.  (valid compression levels: `0...9`)
3. `bzip2`: bzip2-based compression. (valid compression levels: `1...9`)
4. `lzma`: LZMA compression.
5. `zstd`: Zstandard compression (Python 3.14+; valid compression levels: `-131072...22`).


## Lump definitions

Lump definitions follow the following pattern:

    <LUMPNAME> <TYPE> <OFFSET>

`LUMPNAME` describes the filename as used in-engine. Just like the engine,
it is matched against the first eight characters of the basename in a
case-insensitive manner.  [Globbing] such as `D_*.mid` is allowed, in which
case `TYPE` and `OFFSET` are applied to all matching lumps.  `LUMPNAME`s
starting with a "/" are treated as explicit file paths and match against
the full file path, starting at the source directory.

[Globbing]: <https://en.wikipedia.org/wiki/Glob_(programming)>

`TYPE` determines how the file is treated during compilation. It can be one
of the following:

- `colormap`: File is a Colormap. OFFSET specifies the lump name for the palette from which it is generated
- `fade`|`flat`: File is an image and should be converted to a flat. Only PNG images are supported.
- `graphic`: File is an image and should be converted to a Doom Picture using `OFFSET` (see below) as a picture offset. If missing, the offset is assumed to be `0 0`.
- `marker`: File does not exist and is a 0-byte marker. Explicit path definition required.
- `palette`: File is a graphic and should be converted to a color palette. Only PNG images supported.
- `raw`: Copy the file over as-is. When `preserve_filename` is given in the offset, the original filename will be preserved.
- `tinttab`: File is a TINTTAB. OFFSET is defined as `<PALETTE> <WEIGHT>`. Upon generation, `PALETTE` orthogonally maps each color index against one another, `WEIGHT` specifies a bias towards horizontal/vertical colors between 0 and 1.
- `udmf`: (Not supported yet.) File is a UDMF TEXTMAP. PK3Make will generate a directory named LUMPNAME featuring:
  - `<LUMPNAME>`: Marker
  - `TEXTMAP`: Original TEXTMAP file (renamed)
  - `ZNODES`: UDMF BSP tree generated by PK3Make
  - `ENDMAP`: Marker

`OFFSET` defines the offset of doom pictures. For convenience, these can be either:

- `<x> <y>`: Explicit X/Y-coordinates
- `center`: Sets the offset to the center of the image
- `sprite`: Sets the offset to `width/2 (height-4)`. This is a very common
  offset for sprites placed in the game world.
