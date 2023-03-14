# PVP2ACT v2.0

Convert PowerVR (Dreamcast/Naomi) `.PVP` palette files into `.ACT` (Adobe Color Table) which can be loaded by Photoshop.

If a `.PVP` and `.PVR` file are in the same folder, the program will also export a palettized `.png`!

![Image](https://i.imgur.com/4Oadlks.gif)


# How to Use:

Open `PVP2ACT.exe` and select the `.PVP` file(s) to convert!

`.ACT` files will be created in the application folder: `Extracted/ACT`
`.png` images will be created in the application folder: `Extracted`


# How to load palettes in Photoshop:

1) Open the `.png` image
2) Method --> Color Table, load your `.ACT`


# Changelog:

V2.0

- Support for auto 4bpp / 8bpp palette
- PVR read (8888/4444,555,565, twiddle, stride)
- .png conversion (4bpp/8bpp)
- Batch conversion for multiple files
