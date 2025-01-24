# PK3Make

"Make" for Weissblatt PK3 files

## Installation

1. Set up a [virtual environment](https://docs.python.org/3/library/venv.html)
2. Install dependencies `pip install -r requirements.txt`

## How to use

PK3Make supplies multiple subcommands. To get an overview type:

    python pk3make.py help

To fully build your project akin to a makefile, simply type:

    python pk3make.py make ./PK3Makefile # Default PK3Makefile


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

# Weissblatt-flavored METAINFO reference

PK3Make uses it's own build definition language, inspired by the
`METAINFO` spec from
[Matt Tropiano's dImgConv](https://mtrop.github.io/DoomTools/dimgconv.html).
By default, PK3Make will attempt to load the file
Per-line, every character after `#` is treated as a comment.

## Build options

Build options are specified per-line and follow the pattern

    ?<OPTION> <PARAM>

PK3Make supports the following options:

`?srcdir <DIR>` specifies the directory to pull it's base assets from.
PK3Make will attempt to find all defined lumps within this folder and
mirror it's path within `?workdir` after compilation.

`?workdir <DIR>` specifies the temporary working directory. PK3Make will
check the timestamps between this and `?srcdir` and rebuild/copy any
outdated files into `?workdir` during the compilation process.

`?palette` defines the main color palette, by `LUMPNAME` (`PLAYPAL` by default)

`?destfile` describes a filepath to the destination PK3. This is where
`?workdir` will get copied to during packing.


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

- `raw`: Copy the file over as-is
- `fade`|`flat`: File is an image and should be converted to a flat. Only PNG images are supported.
- `graphic`: File is an image and should be converted to a Doom Picture
  using `OFFSET` (see below) as a picture offset. If missing, the offset is
  assumed to be `0 0`.
- `udmf`: Copy the file over as-is
- `palette`: File is a graphic and should be converted to a color palette. Only PNG images supported.

`OFFSET` defines the offset of doompictures. For convenience, these can be either:

- `<x> <y>`: Explicit X/Y-coordinates
- `center`: Sets the offset to the center of the image
- `sprite`: Sets the offset to `width/2 (height-4)`. This is a very common
  offset for sprites placed in the game world.
