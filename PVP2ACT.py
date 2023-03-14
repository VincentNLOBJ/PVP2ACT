from PIL import Image,ImagePalette
import os
import sys
import easystruct as bin
import tkinter as tk
from tkinter import filedialog

debug = False
apply_palette = 1  # If .PVR and .PVP in same folder apply color to .png ( 0 = grayscale )

def read_col(mode, color, act_buffer):

    if mode == 444:
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

        if mode == 444:
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
    global act_buffer,ttl_entries

    f.seek(0x08)
    pixel_type = bin.read_uint8_buff(f)
    if pixel_type == 1:
        mode = 565
    elif pixel_type == 2:
        mode = 444
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


def write_act(act_buffer, ttl_entries):

    with open((app_dir + '\Extracted\ACT/' + file_name[:-4] + ".ACT"), 'w+b') as n:
        print(app_dir + '\Extracted\ACT/' + file_name[:-4] + ".ACT")

        # Pad file with 0x00 if 16-color palette

        if ttl_entries == 16:
            act_file = act_buffer+bytes(b'\x00' * 0x2d0)
        else: act_file=act_buffer

        n.write(act_file)


def decode_pvr(f,w, h, pos=None,px_format=None):
    global cur_file

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
        #print(v_arr)

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

    f.seek(pos)
    data = bytearray()

    if px_format == 7 or px_format == 8:  # 8bpp
        pixels = bytes(f.read(w*h)) # read only required amount of bytes

    else:  # 4bpp , convert to 8bpp

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

    if ttl_entries == 16:

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

        #img.show()
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

    with open(PVR_file, 'rb') as f:
        header_data = f.read()
        offset = header_data.find(b"PVRT")
        if offset != -1 or len(header_data) < 0x10:
            print("Position of 'PVRT' text:", offset)
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
                print("Invalid Palettized PVR!")
            else:
                print('size:', w, 'x', h, 'format:', pal_modes[px_format])
                decode_pvr(f, w, h, offset,px_format)    # file, width, height, image data offset
        else:
            print("'PVRT' header not found!")


def main():
    global cur_file,app_dir,file_name

    # Use Tkinter file selector to load .PVP files

    root = tk.Tk()
    root.withdraw()

    my_file = filedialog.askopenfilenames(initialdir=".", title="Select one or more .PVP to convert",
                                          filetypes=[(".PVP", ".pvp")])

    # Loop start

    selected_files = len(my_file)
    current_file = 0
    app_dir = os.path.abspath(os.path.join(os.getcwd()))
    print(app_dir+'\Extracted\ACT')

    if not os.path.exists(app_dir+'\Extracted\ACT'):
        os.makedirs(app_dir+'\Extracted\ACT')

    while current_file < selected_files:  # Process all selected files in the list
        if my_file:  # if at least one file selected
            cur_file = my_file[current_file]
            dir_path, file_name = os.path.split(cur_file)

            PVR_file = cur_file[:-4] + '.pvr' # If .PVR file exists in the same folder

            if debug:print(cur_file)

            #print(PVR_file)

            with open(cur_file, 'rb') as f:
                file_size =len(f.read())
                f.seek(0x0)
                PVP_check = f.read(4)

                if PVP_check == b'PVPL' and file_size >0x10: # PVPL header and size is OK!
                    act_buffer, mode, ttl_entries = read_pvp(f)
                    write_act(act_buffer, ttl_entries)

                    if os.path.exists(PVR_file):
                        if debug: print(".pvr file in the same directory!")
                        load_pvr(PVR_file)
                else:
                    print('Invalid .PVP file!')  # Skip this file
                current_file += 1

main()
