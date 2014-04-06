#!/usr/bin/env python
# ---------------------------------------------------------
# Filename: MAX7219array_demo.py
# ---------------------------------------------------------
# Demonstration of the features in the MAX7219array library
#
# v1.0
# JLC Archibald 2014
# ---------------------------------------------------------
# Inspired by and based on the max7219 module by RM Hull
# (see https://github.com/rm-hull/max7219)
# ---------------------------------------------------------
# See MAX7219array.py library file for more details
# ---------------------------------------------------------
# This demo script is intended to run on an array of 8
#   MAX7219 boards, connected as described in the library
#   script.  It should run without errors on other-sized
#   arrays, but would not then fully or correctly display
#   the operation of the library functions
# The variable NUM_MATRICES, defined in the MAX7219array.py
#   library script, should always be set to be consistent
#   with the actual hardware setup in use.  If it is not
#   set correctly, then the functions will not work as
#   intended:
#   a)NUM_MATRICES set > actual number or matrices:
#     The functions will assume the presence of the
#     non-existent extra matrices off to the left-hand
#     side of the real array, and so some data sent will
#     not be displayed
#   b)NUM_MATRICES set < actual number of matrices:
#     The functions should work correctly in the right-
#     most matrices declared to the library. Some of
#     the displayed data will however be duplicated on
#     the addition non-declared matrices
# The main script calling the library functions should
#   send arguments appropriate for the value of
#   NUM_MATRICES set in the library.  Error-trapping in
#   the library attempts to capture any inappropriate
#   arguments (and either set them to appropriate values
#   instead or simply ignore the command) but may not
#   correct or eliminate them all. If required, the
#   NUM_MATRICES variable could be imported into the
#   main script to allow the script to adjust to the
#   size of array in use
# ---------------------------------------------------------

import time
from random import randrange

# Import library
import MAX7219array as m7219
# Import fonts
from MAX7219fonts import CP437_FONT, SINCLAIRS_FONT, LCD_FONT, TINY_FONT

# The following imported variables make it easier to feed parameters to the library functions
from MAX7219array import DIR_L, DIR_R, DIR_U, DIR_D
from MAX7219array import DIR_LU, DIR_RU, DIR_LD, DIR_RD
from MAX7219array import DISSOLVE, GFX_ON, GFX_OFF, GFX_INVERT

# Initialise the library and the MAX7219/8x8LED array
m7219.init()

try:

    # Display a stationary message
    m7219.static_message("Welcome!")
    time.sleep(2)
    m7219.clear_all()

    # Cycle through the range of brightness levels - up then down
    m7219.brightness(0)
    m7219.static_message("Bright ?")
    for loop in range(2):
        for brightness in range(15*(loop%2), 16-17*(loop%2), 1-2*(loop%2)):
            m7219.brightness(brightness)
            time.sleep(0.1)
        time.sleep(1)

    # Clear the whole display and reset brightness
    m7219.clear_all()
    m7219.brightness(3)
    time.sleep(1)

    # Random flashing lights (Hollywood's version of a computer)
    for loop in range(16):
        for matrix in range(8):
            for col in range(8):
                m7219.send_matrix_reg_byte(matrix, col+1, randrange(0x100))
                time.sleep(0.001)
    m7219.clear_all()
    time.sleep(1)

    # Display all characters from the font individually
    for char in range(0x100):
        m7219.send_matrix_letter(7-(char%8), char)
        time.sleep(0.02)
    time.sleep(0.5)
    m7219.clear_all()
    time.sleep(0.5)

    # Scroll characters in each of 4 directions
    for matrix in range(8):
        m7219.send_matrix_letter(matrix, 72 - matrix)
    time.sleep(0.5)
    letter_offset=0
    for dir in (DIR_L, DIR_R, DIR_U, DIR_D):
        for stage in range(8):
            for matrix in range(8):
                m7219.send_matrix_shifted_letter(matrix, 72 - matrix + letter_offset, 73 - matrix - letter_offset, stage, dir)
            time.sleep(0.1)
        letter_offset = 1 - letter_offset
    for dir in (DIR_R, DIR_L, DIR_D, DIR_U):
        for stage in range(8):
            for matrix in range(8):
                m7219.send_matrix_shifted_letter(matrix, 72 - matrix - letter_offset, 71 - matrix + letter_offset, stage, dir)
            time.sleep(0.1)
        letter_offset = 1 - letter_offset
    for matrix in range(8):
        m7219.send_matrix_letter(matrix, 72 - matrix)
    time.sleep(1)
    m7219.clear_all()

    # Scroll only part of a display
    Floors = ["B", "G", "1", "2"]
    m7219.static_message("Floor: " + Floors[0])
    time.sleep(1)
    for floor, display in enumerate(Floors[:-1]):
        for stage in range(8):
            m7219.send_matrix_shifted_letter(0, ord(display), ord(Floors[floor+1]), stage, DIR_D)
            time.sleep(0.1)
    m7219.static_message("Floor: " + Floors[-1])
    time.sleep(1)
    m7219.clear_all()

    # Horizontally scroll and repeat a long message
    for dir in [DIR_L, DIR_R]:
        for speed in [3,6,9]:
            m7219.scroll_message_horiz("Speed:"+chr(48+speed)+" ", speed/3 , speed, dir)
        time.sleep(1)

    # Vertically transition (scroll) between different lines of a message
    for speed in [3,6,9]:
        m7219.static_message("Speed: "+chr(48+speed))
        time.sleep(1)
        m7219.scroll_message_vert("Speed: "+chr(48+speed), "Line 2",speed, DIR_U)
        time.sleep(0.25)
        m7219.scroll_message_vert("Line 2", "Line 3", speed, DIR_U)
        time.sleep(0.25)
        m7219.scroll_message_vert("Line 3", "Speed: "+chr(48+speed), speed, DIR_U)
        time.sleep(1)
        m7219.scroll_message_vert("Speed: "+chr(48+speed), "Line 5", speed, DIR_D)
        time.sleep(0.25)
        m7219.scroll_message_vert("Line 5", "Line 6", speed, DIR_D)
        time.sleep(0.25)
        m7219.scroll_message_vert("Line 6", "Speed: "+chr(48+speed), speed, DIR_D)
        time.sleep(1)
    m7219.clear_all()
    time.sleep(1)

    # Wipe/fade effects
    m7219.static_message("ABCDEFGH")
    time.sleep(1)
    for trans in (DIR_U, DIR_RU, DIR_R, DIR_RD, DIR_D, DIR_LD, DIR_L, DIR_LU):
        m7219.wipe_message("ABCDEFGH", "IJKLMNOP" ,4, trans)
        time.sleep(0.5)
        m7219.wipe_message("IJKLMNOP", "ABCDEFGH" ,4, trans)
        time.sleep(0.5)
    time.sleep(1)
    for repeat in range(2):
        m7219.wipe_message("ABCDEFGH", "Dissolve" ,4, DISSOLVE)
        time.sleep(0.5)
        m7219.wipe_message("Dissolve", "ABCDEFGH" ,4, DISSOLVE)
        time.sleep(0.5)
    time.sleep(1)
    m7219.clear_all()

    # Different fonts available in fonts.py
    m7219.scroll_message_horiz("CP437_FONT : ABCDEFGH abcdefgh 1234567890 +++ ", 2, 7.5, DIR_L, CP437_FONT)
    m7219.scroll_message_horiz("LCD_FONT : ABCDEFGH abcdefgh 1234567890 +++ ", 2, 7.5, DIR_L, LCD_FONT)
    m7219.scroll_message_horiz("SINCLAIRS_FONT : ABCDEFGH abcdefgh 1234567890 +++ ", 2, 7.5, DIR_L, SINCLAIRS_FONT)
    m7219.scroll_message_horiz("TINY_FONT : ABCDEFGH abcdefgh 1234567890 +++ ", 2, 7.5, DIR_L, TINY_FONT)

    # Displaying 'graphics' (a simulated ECG) by a low-level method
    heartbeat = [0x10, 0x10, 0x0F, 0xFC, 0x30, 0x08, 0x10, 0x10]
    for loop in range(2):
        for matrix in range(7, -1, -1):
            for col in range(8):
                m7219.send_matrix_reg_byte((matrix-1)%8, col+1, 0x00)
                m7219.send_matrix_reg_byte(matrix, col+1, heartbeat[col])
                time.sleep(0.15)

    # Clear each matrix in turn
    for matrix in range(7, -1, -1):
        m7219.clear([matrix])
        time.sleep(0.2)
    time.sleep(1)

    # Print text characters using gfx_ method
    text="MAX 7219"
    for letter in range(len(text)):
        m7219.gfx_letter(ord(text[letter]), 8*letter)
    m7219.gfx_render()
    time.sleep(1)

    # Using gfx_ methods allows easy subsequent manipulation eg inverting text
    for matrix in range(3,8):
        for col in range(8):
            m7219.gfx_set_col(8*matrix+col, GFX_INVERT)
        m7219.gfx_render()
    time.sleep(1)

    # Draw some line patterns and demonstrate graphics scrolling
    for fill in (GFX_OFF, GFX_ON):
        m7219.gfx_set_all(GFX_OFF)
        m7219.gfx_line(0, 3, 63, 3, GFX_ON)
        m7219.gfx_line(0, 4, 63, 4, GFX_ON)
        for matrix in range(8):
             m7219.gfx_line(8*matrix+3 ,0 ,8*matrix+3 ,7 , GFX_ON)
             m7219.gfx_line(8*matrix+4 ,0 ,8*matrix+4 ,7 , GFX_ON)
        m7219.gfx_render()
        time.sleep(1)
        for index, scroll in enumerate([DIR_LD, DIR_L, DIR_LU, DIR_U, DIR_RU, DIR_R, DIR_RD, DIR_D]):
            for repeat in range(8):
                m7219.gfx_scroll(scroll, 8*index, 8, 0, 8, fill)
                m7219.gfx_render()
                time.sleep(0.05)
    m7219.gfx_set_all(GFX_OFF)
    m7219.gfx_render()

    # Draw random lines in both 'on' & 'off' modes
    x_new = 32
    y_new = 0
    for ink in [GFX_ON, GFX_OFF]:
        for line in range(128):
            x_old, y_old = x_new, y_new
            x_new, y_new = randrange(64), 7 - y_old
            m7219.gfx_line(x_old, y_old, x_new, y_new, ink)
            m7219.gfx_render()
            time.sleep(0.1)
    time.sleep(1)
    m7219.gfx_set_all(GFX_OFF)
    m7219.gfx_render()

    # Printing text in 'invert' mode allows easy subsequent erasure (eg to scroll it over a background)
    for x_s in range(16, 41):
        m7219.gfx_line(x_s, 7, x_s + 7, 0)
    text = " Raspberry Pi "
    rasp = [0x03, 0x05, 0x39, 0x46, 0xAA, 0x94, 0xAA, 0x46, 0x39, 0x05, 0x03]
    length = len(text)
    ext = len(rasp)
    for position in range(64, -8*length-2*ext-1, -1):
        m7219.gfx_sprite(rasp, position, GFX_INVERT)
        for letter in range(length):
            m7219.gfx_letter(ord(text[letter]), ext+position+8*letter, GFX_INVERT)
        m7219.gfx_sprite(rasp, ext+position+8*length, GFX_INVERT)
        m7219.gfx_render()
        time.sleep(0.1)
        m7219.gfx_sprite(rasp, position, GFX_INVERT)
        for letter in range(length):
            m7219.gfx_letter(ord(text[letter]), ext+position+8*letter, GFX_INVERT)
        m7219.gfx_sprite(rasp, ext+position+8*length, GFX_INVERT)

    # Similarly graphics drawn eg with gfx_sprite can be erased and scrolled by using 'invert' mode
    m7219.gfx_set_all(GFX_OFF)
    m7219.gfx_render()
    sinewave = [0x0C, 0x02, 0x01, 0x01, 0x02, 0x0C, 0x30, 0x40, 0x80, 0x80, 0x40, 0x30]
    sine_len=len(sinewave)
    text = "Max 7219"
    for letter in range(len(text)):
        m7219.gfx_letter(ord(text[letter]), 8*letter, GFX_ON)
    m7219.gfx_render()
    for loop in range(16):
        for position in range(sine_len):
            for repeat in range(64//sine_len+2):
                m7219.gfx_sprite(sinewave, repeat*sine_len - position, GFX_INVERT)
            m7219.gfx_render()
            time.sleep(0.02)
            for repeat in range(64//sine_len+2):
                m7219.gfx_sprite(sinewave, repeat*sine_len - position, GFX_INVERT)
    m7219.gfx_render()

    # Define & draw a large sprite, and then move it around on the array
    Pi = [0x7E, 0x12, 0x12, 0x6C, 0x00, 0x54, 0x54, 0x78, # Ra
          0x00, 0x48, 0x54, 0x24, 0x00, 0xFC, 0x24, 0x18, # sp
          0x00, 0x7E, 0x48, 0x30, 0x00, 0x38, 0x54, 0x58, # be
          0x00, 0x78, 0x04, 0x04, 0x00, 0x78, 0x04, 0x04, # rr
          0x9C, 0xA0, 0x7C, 0x00, 0x00, 0x00, 0x00, 0x00, # y_
          0x00, 0x7E, 0x12, 0x12, 0x0C, 0x00, 0x74, 0x00, # Pi
          0x00, 0x00, 0x00, 0x03, 0x05, 0x39, 0x46, 0xAA, # } logo
          0x94, 0xAA, 0x46, 0x39, 0x05, 0x03]             # }
    m7219.gfx_set_all(GFX_OFF)
    m7219.gfx_sprite(Pi,1)
    m7219.gfx_render()
    time.sleep(1)
    for repeat in range(2):
        for scroll in (DIR_L, DIR_LU, DIR_U, DIR_RU, DIR_R, DIR_RD, DIR_D, DIR_LD):
            moves = 2*repeat+1
            if scroll in [DIR_R, DIR_RD, DIR_D, DIR_LD]:
                moves += 1
            for loop in range(moves):
                m7219.gfx_scroll(scroll)
                m7219.gfx_render()
                time.sleep(0.1)

    # Continuous marquee display
    diamonds = chr(4) * 5
    m7219.scroll_message_horiz(" This is the end of the demo " + diamonds + " Press <Ctrl><C> to end " + diamonds, 0, 5)

except KeyboardInterrupt:
    # reset array
    m7219.scroll_message_horiz("Goodbye!", 1, 8)
    m7219.clear_all()
