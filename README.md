# PVP2ACT

Convert Dreamcast `.PVP` palette files into `.ACT` (Adobe Color Table) which can be loaded by Photoshop.

Initial version:
- 565 / 555 palette support


![Image](https://i.imgur.com/4Oadlks.gif)


# How to Use:

Before using this program, you need to properly dump the target image without any palettes loaded in. I suggest to use PVRViewer .PNG export!

1) Open `PVP2ACT.exe` and select the `.PVP` file to convert, it will create 555/565 .ACT` palettes.


# How to load palettes in Photoshop:

1) Open the `.PNG` image, then set Color mode to `Indexed`.
2) In the palette menu choose `Custom` and load `16-col.ACT` or `256-col.ACT`. (according to palette)
3) Click on Color Table, load your `.ACT` as `Custom`
