# PVP2ACT

Convert palettized PowerVR images (Dreamcast/Naomi) into `png` / `.ACT` (Adobe Color Table) which can be loaded in Photoshop.

If `.PVP` and `.PVR` files are in the same folder, `.png` will have palette colors!

![Image](https://i.imgur.com/4Oadlks.gif)


# How to Use:

1) Extract `PVP2ACT_V2_1.zip` content to a dedicate folder.

2) Open `PVP2ACT.exe` and select `.PVP` / `.PVR` file(s) to convert!

3) Converted `.pngs` will be saved in application `Extracted` folder,
`.ACT` files in `Extracted/ACT`.

# How to manually load .ACT palettes in Photoshop:

1) Open the `.png` image
2) Method --> Color Table, load your `.ACT`


# Changelog:

V2.1

- .PVR Pal4 / Pal8 mips support
- File dialog selection for multiple .PVR / .PVP at once
- If a palettized .PVR doesn't have .PVP in same folder, will save it as grayscale png.

V2.0
- Support for auto 4bpp / 8bpp palette
- PVR read (8888/4444,555,565, twiddle, stride)
- .png conversion (4bpp/8bpp)
- Batch conversion for multiple files
