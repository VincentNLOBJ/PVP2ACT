from PIL import Image,ImagePalette
import os
import easystruct as bin
import tkinter as tk
from tkinter import filedialog

debug = False

def read_col(mode, color, act_buffer):

    if mode == 4444:
        red = ((color >> 8) & 0xf) << 4
        green = ((color >> 4) & 0xf) << 4
        blue = (color & 0xf) << 4
        alpha = '-'

    if mode == 555:
        red = ((color >> 10) & 0x1f) << 3
        green = ((color >> 5) & 0x1f) << 3
        blue = (color & 0x1f) << 3
        alpha = '-'

    elif mode == 565:
        red = ((color >> 11) & 0x1f) << 3
        green = ((color >> 5) & 0x3f) << 2
        blue = (color & 0x1f) << 3
        alpha = '-'

    elif mode == 8888:
        blue = (color >> 0) & 0xFF
        green = (color >> 8) & 0xFF
        red = (color >> 16) & 0xFF
        alpha = (color >> 24) & 0xFF

    act_buffer += bytes([red, green, blue])

    if debug:
        bits = [(color >> i) & 1 for i in range(16)]

        if mode == 4444:
            d_blue = f"{bits[0:4]}"
            d_green = f"{bits[4:8]}"
            d_red = f"{bits[8:12]}"

        if mode == 565:
            d_blue = f"{bits[0:5]}"
            d_green = f"{bits[5:11]}"
            d_red = f"{bits[11:16]}"

        elif mode == 555:
            d_blue = f"{bits[0:5]}"
            d_green = f"{bits[5:10]}"
            d_red = f"{bits[11:16]}"

        elif mode == 8888:
            d_blue = ""
            d_green = ""
            d_red = ""

        print(
            f"Palette {int(len(act_buffer)/3)} Blue:{blue} {d_blue},Green:{green} {d_green},Red:{red} {d_red},Alpha:{alpha}")
    return act_buffer

    """
    Get bit data:
    bit0 = ((color >> 0) & 1)
    ...
    bit15 = ((color >> 15) & 1)
    """


def read_pvp(f):
    global act_buffer

    f.seek(0x08)
    pixel_type = bin.read_uint8_buff(f)
    if pixel_type == 1:
        mode = 565
    elif pixel_type == 2:
        mode = 4444
    elif pixel_type == 6:
        mode = 8888
    else:
        mode = 555
    if debug: print(mode)

    f.seek(0x0e)
    ttl_entries = bin.read_uint16_buff(f)

    f.seek(0x10)  # Start palette data
    current_offset = 0x10
    act_buffer = bytearray()

    for counter in range(0, ttl_entries):
        if mode != 8888:
            color = bin.read_uint16_buff(f)
            act_buffer = read_col(mode, color, act_buffer)
            current_offset += 0x2
        else:
            color = bin.read_uint32_buff(f)
            act_buffer = read_col(mode, color, act_buffer)
            current_offset += 0x4

    return act_buffer, mode, ttl_entries


def write_act(act_buffer):

    with open((app_dir + '\Extracted\ACT/' + file_name[:-4] + ".ACT"), 'w+b') as n:
        if debug:(app_dir + '\Extracted\ACT/' + file_name[:-4] + ".ACT")

        # Pad file with 0x00 if 16-color palette

        if len(act_buffer) < 768:
            act_file = bytes(act_buffer) + bytes(b'\x00' * (768 - len(act_buffer)))
        else:
            act_file = bytes(act_buffer)
        n.write(act_file)


def decode_pvr(f,w, h, offset=None,px_format=None):

    # Initialize variables

    index = 0
    pat2, h_inc, arr, h_arr = [], [], [], []

    # Build Twiddle index table

    seq = [2, 6, 2, 22, 2, 6, 2]
    pat = seq + [86] + seq + [342] +seq + [86] +seq

    for i in range(4):
        pat2 += [1366, 5462, 1366, 21846]
        pat2 += [1366, 5462, 1366, 87382] if i % 2 == 0 else [1366, 5462, 1366, 349526]

    for i in range(len(pat2)):
        h_inc.extend(pat + [pat2[i]])
    h_inc.extend(pat)

    # Rectangle (horizontal)

    if w > h:
        ratio = int(w/h)
        if debug:print(f'width is {ratio} times height!')

        if w % 32 == 0 and w & (w - 1) != 0 or h & (h - 1) != 0:
            if debug: print('h and w not power of 2. Using Stride format')
            n = h*w
            for i in range (n):
                arr.append(i)

        else:
            # Single block h_inc lenght
            cur_h_inc = {w: h_inc[0:h - 1] + [2]}  # use height size to define repeating block h_inc

            # define the first horizontal row of image pixel array:

            for j in range(ratio):
                if w in cur_h_inc:
                    for i in cur_h_inc[w]:
                        h_arr.append(index)
                        index += i
                index = (len(h_arr) * h)

            # define the vertical row of image pixel array of repeating block:
            v_arr = [int(x / 2) for x in h_arr]
            v_arr = v_arr[0:h]

            for val in v_arr:
                arr.extend([x + val for x in h_arr])

    # Rectangle (vertical)

    elif h > w:
        ratio = int(h/w)
        if debug:print(f'height is {ratio} times width!')
        # Set the size of pixel increase array

        cur_h_inc = {w: h_inc[0:w - 1] + [2]}

        # define the first horizontal row of image pixel array:
        if w in cur_h_inc:
            for i in cur_h_inc[w]:
                h_arr.append(index)
                index += i

        # define the vertical row of image pixel array:
        v_arr = [int(x / 2) for x in h_arr]

        # Repeat vertical array block from last value of array * h/w ratio
        for i in range(ratio):
            if i == 0:
                last_val = 0
            else:last_val =arr[-1] + 1

            for val in v_arr:
                arr.extend([last_val+ x + val for x in h_arr])

    elif w == h:   # Square
        cur_h_inc = {w: h_inc[0:w - 1] + [2]}
        # define the first horizontal row of image pixel array:
        if w in cur_h_inc:
            for i in cur_h_inc[w]:
                h_arr.append(index)
                index += i

        # define the vertical row of image pixel array:
        v_arr = [int(x / 2) for x in h_arr]

        for val in v_arr:
            arr.extend([x + val for x in h_arr])

    # ------------------------------------
    # Read image pixels as per array order
    # ------------------------------------

    # open the file a.pvr and read every byte according to the list

    f.seek(offset)
    data = bytearray()

    if px_format == 7 or px_format == 8:  # 8bpp
        palette_entries = 256
        pixels = bytes(f.read(w*h)) # read only required amount of bytes

    else:  # 4bpp , convert to 8bpp

        palette_entries = 16
        pixels = bytes(f.read(w * h // 2)) # read only required amount of bytes
        for i in range (len(pixels)):
            data.append(((pixels[i]) & 0x0f)*0x11)   # last 4 bits
            data.append((((pixels[i]) & 0xf0) >> 4)*0x11)  # first 4 bits

        pixels = data # converted 4bpp --> 8bpp "data" back into "pixels" variable

    data = bytearray()
    for num in arr:
        data.append(pixels[num])

    # create a new image with grayscale data
    img = Image.new('L', (w, h))
    img.putdata(bytes(data))


    if apply_palette == 1:
        new_palette = ImagePalette.raw("RGB", bytes(act_buffer))
    else:
        new_palette = ''

    if palette_entries == 16:

        img = img.convert('RGB')
        img = img.convert('L', colors=16)

        # 16-col greyscale palette
        pal_16_grey = []
        for i in range(0, 16):
            pal_16_grey += [i * 17, i * 17, i * 17]

        #print(palette)
        img = img.convert('P', colors=16)
        img.putpalette(pal_16_grey)

        if new_palette != '':
            # Set the image's palette to the loaded palette

            # Get the palette from the image
            img.getpalette()
            img.putpalette(new_palette)

        # save the image
        img.save((app_dir + '\Extracted/' + file_name[:-4] + ".png"),bits=4)

    else:
        # Convert the image to a palettized grayscale 256 col
        img = img.convert('L', colors=256)
        img = img.convert('P', colors=256)

        # Get the palette from the image
        palette = img.getpalette()

        # Set the palette in the same order as before
        img.putpalette(palette)
        if new_palette != '':
            # Set the image's palette to the loaded palette
            img.putpalette(new_palette)

        # save the image
        img.save((app_dir + '\Extracted/' + file_name[:-4] + ".png"))


def load_pvr(PVR_file):

    try:
        with open(PVR_file, 'rb') as f:
            header_data = f.read()
            offset = header_data.find(b"PVRT")
            if offset != -1 or len(header_data) < 0x10:
                if debug: print("Position of 'PVRT' text:", offset)
                offset += 0x10
                f.seek(offset - 0x4)
                w = int.from_bytes(f.read(2), byteorder='little')
                h = int.from_bytes(f.read(2), byteorder='little')

                f.seek(offset - 0x7)
                pal_modes = {
                    5: 'Pal4 (16-col)',
                    6: 'Pal4 + Mips (16-col)',
                    7: 'Pal8 (256-col)',
                    8: 'Pal8 + Mips (256-col)',
                    11: 'Stride',
                }
                px_format = int.from_bytes(f.read(1), byteorder='little')

                if px_format not in pal_modes or h > 1024 or w > 1024:
                    if debug: print(PVR_file, "Invalid Palettized PVR!")
                else:
                    if debug: print('size:', w, 'x', h, 'format:', pal_modes[px_format])
                    if px_format == 6 or px_format == 8:
                        if debug: print('mip-maps!')

                        mip_size = [0x20, 0x80, 0x200, 0x800, 0x2000, 0x8000, 0x20000, 0x80000]
                        pvr_dim = [4, 8, 16, 32, 64, 128, 256, 512, 1024]
                        extra_mip = {6: 0xc, 8: 0x17}  # smallest mips fixed size
                        size_adjust = {6: 1, 8: 2}  # 8bpp size is 4bpp *2

                        for i in range(len(pvr_dim)):
                            if pvr_dim[i] == w:
                                mip_index = i - 1
                                break

                        # Skip mips for image data offset
                        mip_sum = (sum(mip_size[:mip_index]) * size_adjust[px_format]) + (extra_mip[px_format])
                        offset += mip_sum

                    decode_pvr(f, w, h, offset, px_format)  # file, width, height, image data offset
            else:
                if debug: print("'PVRT' header not found!")

    except: print(f'PVR data error! {PVR_file}')


def load_pvp(PVP_file):

    try:
        with open(PVP_file, 'rb') as f:
            file_size = len(f.read())
            f.seek(0x0)
            PVP_check = f.read(4)

            if PVP_check == b'PVPL' and file_size > 0x10:  # PVPL header and size is OK!
                act_buffer, mode, ttl_entries = read_pvp(f)
                write_act(act_buffer)
            else:
                print('Invalid .PVP file!')  # Skip this file
    except:
         print(f'PVP data error! {PVP_file}')


def main():
    global app_dir,file_name,apply_palette

    # Use Tkinter file selector to load .PVP files

    root = tk.Tk()
    root.withdraw()

    my_file = filedialog.askopenfilenames(
        initialdir=".",
        title="Select palette .PVP and/or palettized .PVR to convert",
        filetypes=[(".pvp .pvr files", ".PV*")]
    )

    # remove companion .PVP/.PVR, filter the list

    new_list = []
    for item in my_file:
        key = item[:-4]
        if not any(key == x[:-4] for x in new_list):
            new_list.append(item)
    my_file = new_list

    selected_files = len(my_file)
    current_file = 0

    # create Extracted\ACT folders
    app_dir = os.path.abspath(os.path.join(os.getcwd()))
    if debug:print(app_dir+'\Extracted\ACT')

    if not os.path.exists(app_dir+'\Extracted\ACT'):
        os.makedirs(app_dir+'\Extracted\ACT')

    # -----------
    # Loop start
    # -----------

    while current_file < selected_files:  # Process all selected files in the list
        if my_file:  # if at least one file selected
            cur_file = my_file[current_file]
            dir_path, file_name = os.path.split(cur_file)
            filetype = cur_file[-4:]
            PVR_file = cur_file[:-4] + '.pvr'  # If .PVR file exists in the same folder
            PVP_file = cur_file[:-4] + '.pvp'  # If .PVP file exists in the same folder

            if debug:print('filetype:',filetype)

            # If cur_file is a .PVP
            if filetype == ".pvp" or filetype == ".PVP":
                load_pvp(PVP_file)

                if os.path.exists(PVR_file):
                    apply_palette = 1
                    load_pvr(PVR_file)

                    if debug:print('companion PVR exist!')

                else:
                    apply_palette = 0
                    if debug:print('Only convert PVP to ACT!')


            # If cur_file is a .PVR
            elif filetype == ".pvr" or filetype == ".PVR":

                if os.path.exists(PVP_file):
                    if debug:print('companion PVP exist!')
                    apply_palette = 1
                    load_pvp(PVP_file)

                else:
                    apply_palette = 0
                    if debug:print('Only convert PVR to grayscale .png!')

                load_pvr(PVR_file)

            current_file += 1

            if debug:print(cur_file)

main()
