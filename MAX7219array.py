#!/usr/bin/env python
# ---------------------------------------------------------
# Filename: MAX7219array.py
# ---------------------------------------------------------
# MAX7219array library - functions for driving an array of
# daisy-chained MAX7219 8x8 LED matrix boards
#
# v1.0
# JLC Archibald 2014
# ---------------------------------------------------------
# Controls a linear array of MAX7219 LED Display Drivers,
#   each of which is driving an 8x8 LED matrix.
#
# Terminology used in this script:
# - matrix: one of the MAX7219 boards incl 8x8 LED display
# - array: a 'daisy-chained' line of such matrices
#
# Wiring up the array of MAX7219 controller boards:
# - Each board's Vcc & GND pins connected to power (not from
#   the Raspberry Pi as the current requirement would be too
#   high). Note that the common GND also needs to be connected
#   to the Pi's GND pin
# - Each board's CS & CLK pins to be connected to the corresponding
#   SPI GPIO pins (CE0=Pin24 & SCLK=Pin23) on the RPi
# - The right-most board's DIN pins to be connected to the
#   MOSI (=Pin19) SPI GPIO pin on the RPi
# - Each subsequent board's DIN pin to be connected to the DOUT
#   pin on the board to its right as shown below:
#
#   ...-+    +----+    +----+    +----+
#       |    |    |    |    |    |    |
#     DOUT-  |  DOUT-  |  DOUT-  |  DOUT-
#     |   |  |  |   |  |  |   |  |  |   |
#     -DIN-  |  -DIN-  |  -DIN-  |  -DIN-
#       |    |    |    |    |    |    |
#       +----+    +----+    +----+    +---> RPi SPI.MOSI
#
# Numbering used by this library:
# - The total number of matrices daisy-chained to be specified
#   in the NUM_MATRICES variable below
# - Matrices are numbered from 0 (left) to NUM_MATRICES-1 (right)
# - gfx_ (graphics-based) functions use an x,y coordinate system
#   to address individual LEDs:
#     x=0 (left-hand column) to x=8*NUM_MATRICES-1 (right-hand column)
#     y=0 (top row) to y=7 (bottom row)
# ---------------------------------------------------------
# The main use for this script is as an imported library:
#   1. In the main script, import the library using eg:
#        import MAX7219array.py as m7219
#   2. Also import the fonts with:
#        from MAX7219fonts import CP437_FONT, SINCLAIRS_FONT, LCD_FONT, TINY_FONT
#   3. To facilitate calling the library functions,
#      import the following pre-defined parameters:
#        from MAX7219array import DIR_L, DIR_R, DIR_U, DIR_D
#        from MAX7219array import DIR_LU, DIR_RU, DIR_LD, DIR_RD
#        from MAX7219array import DISSOLVE, GFX_ON, GFX_OFF, GFX_INVERT
#   4. The main script can then use the library functions using eg:
#        m7219.scroll_message_horiz("Marquee text goes here")
#
# This script can also be executed directly as a shorthand way of running
#   a 'marquee' display.  Enter the following at the command line to use
#   this functionality:
#       python MAX7219array.py message [repeats [speed [direction [font]]]]"
# Or for more information on this usage, see the help text at the end of this
#   script, or alternatively, enter the following at the command line:
#       python MAX7219array.py
# ---------------------------------------------------------
# Based on and extended from the max7219 module by RM Hull
#   (see https://github.com/rm-hull/max7219)
#   but uses the spidev module to provide the SPI interface
#   instead of the SPI-Py C extension used by max7219
# ---------------------------------------------------------
# Requires:
# - python-dev & py-spidev modules, see install instructions
#   at www.100randomtasks.com/simple-spi-on-raspberry-pi
# - MAX7219fonts.py file containing font bitmaps
# - User should also set NUM_MATRICES variable below to the
#   appropriate value for the setup in use.  Failure to do
#   this will prevent the library functions working properly
# ---------------------------------------------------------
# The functions from spidev used in this library are:
#   xfer()  : send bytes deasserting CS/CE after every byte
#   xfer2() : send bytes only de-asserting CS/CE at end
# ---------------------------------------------------------
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
# See further documentation of each library function below
# Also see MAX7219array_demo.py script for examples of use
# MAX7219 datasheet gives full details of operation of the
# LED driver chip
# ---------------------------------------------------------

import spidev
import time
from random import randrange

# Note: If any additional fonts are added in MAX7219fonts.py, add them to the import list here:
#       Also add them to the section at the end of this script that parses command line arguments
from MAX7219fonts import CP437_FONT, SINCLAIRS_FONT, LCD_FONT, TINY_FONT

# IMPORTANT: User must specify the number of MAX7219 matrices here:
NUM_MATRICES = 8                   # Number of separate MAX7219 matrices

# Optional: It is also possible to change the default font for all the library functions:
DEFAULT_FONT = CP437_FONT          # Note: some fonts only contain characters in chr(32)-chr(126) range

# ---------------------------------------------------------
# Should not need to change anything below here
# ---------------------------------------------------------

PAD_STRING   = " " * NUM_MATRICES  # String for trimming text to fit
NO_OP        = [0,0]               # 'No operation' tuple: 0x00 sent to register MAX_7219_NOOP
MATRICES     = range(NUM_MATRICES) # List of available matrices for validation

# Graphics setup
gfx_buffer  = []
gfx_rows    = range(8)
gfx_columns = range(NUM_MATRICES * 8)
for gfx_col in gfx_columns:
    gfx_buffer += [0]

# Registers in the MAX7219 matrix controller (see datasheet)
MAX7219_REG_NOOP        = 0x0
MAX7219_REG_DIGIT0      = 0x1
MAX7219_REG_DIGIT1      = 0x2
MAX7219_REG_DIGIT2      = 0x3
MAX7219_REG_DIGIT3      = 0x4
MAX7219_REG_DIGIT4      = 0x5
MAX7219_REG_DIGIT5      = 0x6
MAX7219_REG_DIGIT6      = 0x7
MAX7219_REG_DIGIT7      = 0x8
MAX7219_REG_DECODEMODE  = 0x9
MAX7219_REG_INTENSITY   = 0xA
MAX7219_REG_SCANLIMIT   = 0xB
MAX7219_REG_SHUTDOWN    = 0xC
MAX7219_REG_DISPLAYTEST = 0xF

# Scroll & wipe directions, for use as arguments to various library functions
# For ease of use, import the following constants into the main script
DIR_U      = 1   # Up
DIR_R      = 2   # Right
DIR_D      = 4   # Down
DIR_L      = 8   # Left
DIR_RU     = 3   # Right & up diagonal scrolling for gfx_scroll() function only
DIR_RD     = 6   # Right & down diagonal scrolling for gfx_scroll() function only
DIR_LU     = 9   # Left & up diagonal scrolling for gfx_scroll() function only
DIR_LD     = 12  # Left & down diagonal scrolling for gfx_scroll() function only
DISSOLVE   = 16  # Pseudo-random fade transition for wipe_message() function only
GFX_OFF    = 0   # Turn the relevant LEDs off, or omit (don't draw) the endpoint of a line
GFX_ON     = 1   # Turn the relevant LEDs on, or include (draw) the endpoint of a line
GFX_INVERT = 2   # Invert the state of the relevant LEDs

# Open SPI bus#0 using CS0 (CE0)
spi = spidev.SpiDev()
spi.open(0,0)

# ---------------------------------------
# Library function definitions begin here
# ---------------------------------------

def send_reg_byte(register, data):
    # Send one byte of data to one register via SPI port, then raise CS to latch
    # Note that subsequent sends will cycle this tuple through to successive MAX7219 chips
    spi.xfer([register, data])

def send_bytes(datalist):
    # Send sequence of bytes (should be [register,data] tuples) via SPI port, then raise CS
    # Included for ease of remembering the syntax rather than the native spidev command, but also to avoid reassigning to 'datalist' argument
    spi.xfer2(datalist[:])

def send_matrix_reg_byte(matrix, register, data):
    # Send one byte of data to one register in just one MAX7219 without affecting others
    if matrix in MATRICES:
        padded_data = NO_OP * (NUM_MATRICES - 1 - matrix) + [register, data] + NO_OP * matrix
        send_bytes(padded_data)

def send_all_reg_byte(register, data):
    # Send the same byte of data to the same register in all of the MAX7219 chips
    send_bytes([register, data] * NUM_MATRICES)

def clear(matrix_list):
    # Clear one or more specified MAX7219 matrices (argument(s) to be specified as a list even if just one)
    for matrix in matrix_list:
        if matrix in MATRICES:
            for col in range(8):
                send_matrix_reg_byte(matrix, col+1, 0)

def clear_all():
    # Clear all of the connected MAX7219 matrices
    for col in range(8):
        send_all_reg_byte(col+1, 0)

def brightness(intensity):
    # Set a specified brightness level on all of the connected MAX7219 matrices
    # Intensity: 0-15 with 0=dimmest, 15=brightest; in practice the full range does not represent a large difference
    intensity = int(max(0, min(15, intensity)))
    send_bytes([MAX7219_REG_INTENSITY, intensity] * NUM_MATRICES)

def send_matrix_letter(matrix, char_code, font=DEFAULT_FONT):
    # Send one character from the specified font to a specified MAX7219 matrix
    if matrix in MATRICES:
        for col in range(8):
            send_matrix_reg_byte(matrix, col+1, font[char_code % 0x100][col])

def send_matrix_shifted_letter(matrix, curr_code, next_code, progress, direction=DIR_L, font=DEFAULT_FONT):
    # Send to one MAX7219 matrix a combination of two specified characters, representing a partially-scrolled position
    # progress: 0-7: how many pixels the characters are shifted: 0=curr_code fully displayed; 7=one pixel less than fully shifted to next_code
    # With multiple matrices, this function sends many NO_OP tuples, limiting the scrolling speed achievable for a whole line
    # scroll_message_horiz() and scroll_message_vert() are more efficient and can scroll a whole line of text faster
    curr_char = font[curr_code % 0x100]
    next_char = font[next_code % 0x100]
    show_char = [0,0,0,0,0,0,0,0]
    progress  = progress % 8
    if matrix in MATRICES:
        if direction == DIR_L:
            for col in range(8):
                if col+progress < 8:
                    show_char[col] = curr_char[col+progress]
                else:
                    show_char[col] = next_char[col+progress-8]
                send_matrix_reg_byte(matrix, col+1, show_char[col])
        elif direction == DIR_R:
            for col in range(8):
                if col >= progress:
                    show_char[col] = curr_char[col-progress]
                else:
                    show_char[col] = next_char[col-progress+8]
                send_matrix_reg_byte(matrix, col+1, show_char[col])
        elif direction == DIR_U:
            for col in range(8):
                show_char[col] = (curr_char[col] >> progress) + (next_char[col] << (8-progress))
                send_matrix_reg_byte(matrix, col+1, show_char[col])
        elif direction == DIR_D:
            for col in range(8):
                show_char[col] = (curr_char[col] << progress) + (next_char[col] >> (8-progress))
                send_matrix_reg_byte(matrix, col+1, show_char[col])

def static_message(message, font=DEFAULT_FONT):
    # Send a stationary text message to the array of MAX7219 matrices
    # Message will be truncated from the right to fit the array
    message = trim(message)
    for matrix in range(NUM_MATRICES-1, -1, -1):
        send_matrix_letter(matrix, ord(message[NUM_MATRICES - matrix - 1]), font)

def scroll_message_horiz(message, repeats=0, speed=3, direction=DIR_L, font=DEFAULT_FONT, finish=True):
    # Scroll a text message across the array, for a specified (repeats) number of times
    # repeats=0 gives indefinite scrolling until script is interrupted
    # speed: 0-9 for practical purposes; speed does not have to integral
    # direction: DIR_L or DIR_R only; DIR_U & DIR_D will do nothing
    # finish: True/False - True ensures array is clear at end, False ends with the last column of the last character of message
    #   still displayed on the array - this is included for completeness but rarely likely to be required in practice
    # Scrolling starts with message off the RHS(DIR_L)/LHS(DIR_R) of array, and ends with message off the LHS/RHS
    # If repeats>1, add space(s) at end of 'message' to separate the end of message & start of its repeat
    delay = 0.5 ** speed
    if repeats <= 0:
        indef = True
    else:
        indef = False
        repeats = int(repeats)
    if len(message) < NUM_MATRICES:
        message = trim(message)
    # Repeatedly scroll the whole message (initially 'front-padded' with blanks) until the last char appears
    scroll_text = ""
    if direction == DIR_L:
        scroll_text = PAD_STRING + message
    elif direction == DIR_R:
        scroll_text = message + PAD_STRING
    counter = repeats
    while (counter > 0) or indef:
        scroll_text_once(scroll_text, delay, direction, font)
        # After the first scroll, replace the blank 'front-padding' with the start of the same message
        if counter == repeats:
            if direction == DIR_L:
                scroll_text = message[-NUM_MATRICES:] + message
            elif direction == DIR_R:
                scroll_text = message + message[:NUM_MATRICES]
        counter -= 1
    # To finish, 'end-pad' the message with blanks and scroll the end of the message off the array
    if direction == DIR_L:
        scroll_text = message[-NUM_MATRICES:] + PAD_STRING
    elif direction == DIR_R:
        scroll_text = PAD_STRING + message[:NUM_MATRICES]
    scroll_text_once(scroll_text, delay, direction, font)
    # Above algorithm leaves the last column of the last character displayed on the array, so optionally erase it
    if finish:
        clear_all()

def scroll_text_once(text, delay, direction, font):
    # Subroutine used by scroll_message_horiz(), scrolls text once across the array, starting & ending with test on the array
    # Not intended to be used as a user routine; if used, note different syntax: compulsory arguments & requires delay rather than speed
    length = len(text) - NUM_MATRICES
    start_range = []
    if direction == DIR_L:
        start_range = range(length)
    elif direction == DIR_R:
        start_range = range(length-1, -1, -1)
    for start_char in start_range:
        for stage in range(8):
            for col in range(8):
                column_data = []
                for matrix in range(NUM_MATRICES-1, -1, -1):
                    if direction == DIR_L:
                        this_char = font[ord(text[start_char + NUM_MATRICES - matrix - 1])]
                        next_char = font[ord(text[start_char + NUM_MATRICES - matrix])]
                        if col+stage < 8:
                            column_data += [col+1, this_char[col+stage]]
                        else:
                            column_data += [col+1, next_char[col+stage-8]]
                    elif direction == DIR_R:
                        this_char = font[ord(text[start_char + NUM_MATRICES - matrix])]
                        next_char = font[ord(text[start_char + NUM_MATRICES - matrix - 1])]
                        if col >= stage:
                            column_data += [col+1, this_char[col-stage]]
                        else:
                            column_data += [col+1, next_char[col-stage+8]]
                send_bytes(column_data)
            time.sleep(delay)

def scroll_message_vert(old_message, new_message, speed=3, direction=DIR_U, font=DEFAULT_FONT, finish=True):
    # Transitions vertically between two different (truncated if necessary) text messages
    # speed: 0-9 for practical purposes; speed does not have to integral
    # direction: DIR_U or DIR_D only; DIR_L & DIR_R will do nothing
    # finish: True/False : True completely displays new_message at end, False leaves the transition one pixel short
    # False should be used to ensure smooth scrolling if another vertical scroll is to follow immediately
    delay = 0.5 ** speed
    old_message = trim(old_message)
    new_message = trim(new_message)
    for stage in range(8):
        for col in range(8):
            column_data=[]
            for matrix in range(NUM_MATRICES-1, -1, -1):
                this_char = font[ord(old_message[NUM_MATRICES - matrix - 1])]
                next_char = font[ord(new_message[NUM_MATRICES - matrix - 1])]
                scrolled_char = [0,0,0,0,0,0,0,0]
                if direction == DIR_U:
                    scrolled_char[col] = (this_char[col] >> stage) + (next_char[col] << (8-stage))
                elif direction == DIR_D:
                    scrolled_char[col] = (this_char[col] << stage) + (next_char[col] >> (8-stage))
                column_data += [col+1, scrolled_char[col]]
            send_bytes(column_data)
        time.sleep(delay)
    # above algorithm finishes one shift before fully displaying new_message, so optionally complete the display
    if finish:
        static_message(new_message)

def wipe_message(old_message, new_message, speed=3, transition=DISSOLVE, font=DEFAULT_FONT):
    # Transition from one message (truncated if necessary) to another by a 'wipe' or 'dissolve'
    # speed: 0-9 for practical purposes; speed does not have to integral
    # transition: WIPE_U, WIPE_D, WIPE_L, WIPE_R, WIPE RU, WIPE_RD, WIPE_LU, WIPE_LD to wipe each letter simultaneously
    #   in the respective direction (the diagonal directions do not give a true corner-to-corner 'wipe' effect)
    # or transition: DISSOLVE for a pseudo-random dissolve from old_message to new_message
    delay = 0.5 ** speed
    old_message = trim(old_message)
    new_message = trim(new_message)
    old_data =  [ [], [], [], [], [], [], [], [] ]
    new_data =  [ [], [], [], [], [], [], [], [] ]
    pixel =     [ [], [], [], [], [], [], [], [] ]
    stage_range = range(8)
    col_range = range(8)
    for col in range(8):
        for letter in range(NUM_MATRICES):
            old_data[col] += [col+1] + [font[ord(old_message[letter])][col]]
            new_data[col] += [col+1] + [font[ord(new_message[letter])][col]]
            if transition == DISSOLVE:
                pixel[col] += [randrange(8)]
            elif transition == DIR_D:
                pixel[col] += [0]
            elif transition == DIR_U:
                pixel[col] += [7]
            elif transition == DIR_RU or transition == DIR_LD:
                pixel[col] += [col]
            elif transition == DIR_RD or transition == DIR_LU:
                pixel[col] += [7-col]
            elif transition == DIR_L:
                col_range = range(7, -1, -1)
                stage_range = [0]
            elif transition == DIR_R:
                stage_range = [0]
    for stage in stage_range:
        for col in col_range:
            if transition == DIR_L or transition == DIR_R:
                old_data[col]=new_data[col][:]
            else:
                for letter in range(NUM_MATRICES):
                    mask = (0x01 << pixel[col][letter])
                    old_data[col][2*letter+1] = old_data[col][2*letter+1] & ~mask | new_data[col][2*letter+1] & mask
                    if transition == DISSOLVE:
                        pixel_jump = 3
                    elif transition & DIR_D:
                        pixel_jump = 1
                    elif transition & DIR_U:
                        pixel_jump = 7
                    pixel[col][letter] = (pixel[col][letter] + pixel_jump)%8
            send_bytes(old_data[col])
            if transition == DIR_L or transition == DIR_R:
                time.sleep(delay)
        time.sleep(delay)

def trim(text):
    # Trim or pad specified text to the length of the MAX7219 array
    text += PAD_STRING
    text = text[:NUM_MATRICES]
    return text

def gfx_set_px(g_x, g_y, state=GFX_INVERT):
    # Set an individual pixel in the graphics buffer to on, off, or the inverse of its previous state
    if (g_x in gfx_columns) and (g_y in gfx_rows):
        if state == GFX_ON:
            gfx_buffer[g_x] = gfx_buffer[g_x] | (0x01 << g_y)
        elif state == GFX_OFF:
            gfx_buffer[g_x] = (gfx_buffer[g_x] & ~(0x01 << g_y)) & 0xFF
        elif state == GFX_INVERT:
            gfx_buffer[g_x] = (gfx_buffer[g_x] ^ (0x01 << g_y)) & 0xFF

def gfx_set_col(g_col, state=GFX_INVERT):
    # Set an entire column in the graphics buffer to on, off, or the inverse of its previous state
    if (g_col in gfx_columns):
        if state == GFX_ON:
            gfx_buffer[g_col] = 0xFF
        elif state == GFX_OFF:
            gfx_buffer[g_col] = 0x00
        elif state == GFX_INVERT:
            gfx_buffer[g_col] = (~gfx_buffer[g_col]) & 0xFF

def gfx_set_all(state=GFX_INVERT):
    # Set the entire graphics buffer to on, off, or the inverse of its previous state
    for g_col in gfx_columns:
        if state == GFX_ON:
            gfx_buffer[g_col] = 0xFF
        elif state == GFX_OFF:
            gfx_buffer[g_col] = 0x00
        elif state == GFX_INVERT:
            gfx_buffer[g_col] = (~gfx_buffer[g_col]) & 0xFF

def gfx_line(start_x, start_y, end_x, end_y, state=GFX_INVERT, incl_endpoint=GFX_ON):
    # Draw a staright line in the graphics buffer between the specified start- & end-points
    # The line can be drawn by setting each affected pixel to either on, off, or the inverse of its previous state
    # The final point of the line (end_x, end_y) can either be included (default) or omitted
    # It can be usefully omitted if drawing another line starting from this previous endpoint using GFX_INVERT
    start_x, end_x = int(start_x), int(end_x)
    start_y, end_y = int(start_y), int(end_y)
    len_x = end_x - start_x
    len_y = end_y - start_y
    if abs(len_x) + abs(len_y) == 0:
        if incl_endpoint == GFX_ON:
            gfx_set_px(start_x, start_y, state)
    elif abs(len_x) > abs(len_y):
        step_x = abs(len_x) / len_x
        for g_x in range(start_x, end_x + incl_endpoint*step_x, step_x):
            g_y = int(start_y + float(len_y) * (float(g_x - start_x)) / float(len_x) + 0.5)
            if (g_x in gfx_columns) and (g_y in gfx_rows):
            #if (0 <= g_x < 8*NUM_MATRICES) and (0<= g_y <8):
                gfx_set_px(g_x, g_y, state)
    else:
        step_y = abs(len_y) / len_y
        for g_y in range(start_y, end_y + incl_endpoint*step_y, step_y):
            g_x = int(start_x + float(len_x) * (float(g_y - start_y)) / float(len_y) + 0.5)
            if (g_x in gfx_columns) and (g_y in gfx_rows):
            #if (0 <= g_x < 8*NUM_MATRICES) and (0<= g_y <8):
                gfx_set_px(g_x, g_y, state)

def gfx_letter(char_code, start_x=0, state=GFX_INVERT, font=DEFAULT_FONT):
    # Overlay one character from the specified font into the graphics buffer, at a specified horizontal position
    # The character is drawn by setting each affected pixel to either on, off, or the inverse of its previous state
    start_x = int(start_x)
    for l_col in range(0,8):
        if (l_col + start_x) in gfx_columns:
        #if ((l_col + start_x) >= 0) and (l_col + start_x < NUM_MATRICES*8):
            if state == GFX_ON:
                gfx_buffer[l_col + start_x] = font[char_code][l_col]
            elif state == GFX_OFF:
                gfx_buffer[l_col + start_x] = (~font[char_code][l_col]) & 0xFF
            elif state == GFX_INVERT:
                gfx_buffer[l_col + start_x] = (gfx_buffer[l_col + start_x] ^ font[char_code][l_col]) & 0xFF

def gfx_sprite(sprite, start_x=0, state=GFX_INVERT):
    # Overlay a specified sprite into the graphics buffer, at a specified horizontal position
    # The sprite is drawn by setting each affected pixel to either on, off, or the inverse of its previous state
    # Sprite is an 8-pixel (high) x n-pixel wide pattern, expressed as a list of n bytes eg [0x99, 0x66, 0x5A, 0x66, 0x99]
    for l_col in range(0,len(sprite)):
        if ((l_col + start_x) >= 0) and (l_col + start_x < NUM_MATRICES*8):
            if state == GFX_ON:
                gfx_buffer[l_col + start_x] = sprite[l_col]
            elif state == GFX_OFF:
                gfx_buffer[l_col + start_x] = (~sprite[l_col]) & 0xFF
            elif state == GFX_INVERT:
                gfx_buffer[l_col + start_x] = (gfx_buffer[l_col + start_x] ^ sprite[l_col]) & 0xFF

def gfx_scroll(direction=DIR_L, start_x=0, extent_x=8*NUM_MATRICES, start_y=0, extent_y=8, new_pixels=GFX_OFF):
    # Scroll the specified area of the graphics buffer by one pixel in the given direction
    # direction: any of DIR_U, DIR_D, DIR_L, DIR_R, DIR_LU, DIR_RU, DIR_RD, DIR_LD
    # Pixels outside the rectangle are unaffected; pixels scrolled outside the rectangle are discarded
    # The 'new' pixels in the gap created are either set to on or off depending upon the new_pixels argument
    start_x  = max(0, min(8*NUM_MATRICES - 1 , int(start_x)))
    extent_x = max(0, min(8*NUM_MATRICES - start_x, int(extent_x)))
    start_y  = max(0, min(7, int(start_y)))
    extent_y = max(0, min(8 - start_y, int(extent_y)))
    mask = 0x00
    for g_y in range(start_y, start_y + extent_y):
        mask = mask | (0x01 << g_y)
    if direction & DIR_L:
        for g_x in range(start_x, start_x + extent_x - 1):
            gfx_buffer[g_x] = (gfx_buffer[g_x] & ~mask) | (gfx_buffer[g_x + 1] & mask)
        gfx_buffer[start_x + extent_x - 1] = gfx_buffer[start_x + extent_x - 1] & ~mask
        if new_pixels == GFX_ON:
            gfx_buffer[start_x + extent_x - 1] = gfx_buffer[start_x + extent_x - 1] | mask
    elif direction & DIR_R:
        for g_x in range(start_x + extent_x - 1, start_x, -1):
            gfx_buffer[g_x] = (gfx_buffer[g_x] & ~mask) | (gfx_buffer[g_x - 1] & mask)
        gfx_buffer[start_x] = gfx_buffer[start_x] & ~mask
        if new_pixels == GFX_ON:
            gfx_buffer[start_x] = gfx_buffer[start_x] | mask
    if direction & DIR_U:
        for g_x in range(start_x, start_x + extent_x):
            gfx_buffer[g_x] = (gfx_buffer[g_x] & ~mask) | (((gfx_buffer[g_x] & mask) >> 1) & mask)
            if new_pixels == GFX_ON:
                gfx_buffer[g_x] = gfx_buffer[g_x] | (0x01 << (start_y + extent_y - 1))
    elif direction & DIR_D:
        for g_x in range(start_x, start_x + extent_x):
            gfx_buffer[g_x] = (gfx_buffer[g_x] & ~mask) | (((gfx_buffer[g_x] & mask) << 1) & mask)
            if new_pixels == GFX_ON:
                gfx_buffer[g_x] = gfx_buffer[g_x] | (0x01 << start_y)

def gfx_read_buffer(g_x, g_y):
    # Return the current state (on=True, off=False) of an individual pixel in the graphics buffer
    # Note that this buffer only reflects the operations of these gfx_ functions, since the buffer was last cleared
    # The buffer does not reflect the effects of other library functions such as send_matrix_letter() or (static_message()
    if (g_x in gfx_columns) and (g_y in gfx_rows):
        return (gfx_buffer[g_x] & (0x01 << g_y) != 0)

def gfx_render():
    # All of the above gfx_ functions only write to (or read from) a graphics buffer maintained in memory
    # This command sends the entire buffer to the matrix array - use it to display the effect of one or more previous gfx_ functions
    for g_col in range(8):
        column_data = []
        for matrix in range(NUM_MATRICES):
            column_data += [g_col+1, gfx_buffer[8*matrix + g_col]]
        send_bytes(column_data)

def init():
    # Initialise all of the MAX7219 chips (see datasheet for details of registers)
    send_all_reg_byte(MAX7219_REG_SCANLIMIT, 7)   # show all 8 digits
    send_all_reg_byte(MAX7219_REG_DECODEMODE, 0)  # using a LED matrix (not digits)
    send_all_reg_byte(MAX7219_REG_DISPLAYTEST, 0) # no display test
    clear_all()                                   # ensure the whole array is blank
    brightness(3)                                 # set character intensity: range: 0..15
    send_all_reg_byte(MAX7219_REG_SHUTDOWN, 1)    # not in shutdown mode (i.e start it up)
    gfx_set_all(GFX_OFF)                          # clear the graphics buffer

# -----------------------------------------------------
# Library function definitions end here
# The following script executes if run from command line
# ------------------------------------------------------

if __name__ == "__main__":
    import sys
    # Parse arguments and attempt to correct obvious errors
    try:
        # message text
        message = sys.argv[1]
        # number of marequu repeats
        try:
            repeats = abs(int(sys.argv[2]))
        except (IndexError, ValueError):
            repeats = 0
        # speed of marquee scrolling
        try:
            speed = float(sys.argv[3])
        except (IndexError, ValueError):
            speed = 3
        if speed < 1:
            speed = 3
        elif speed > 9:
            speed = 9
        # direction of marquee scrolling
        try:
            direction = sys.argv[4].lower()
            if direction in ["dir_r", "dirr", "r", "right", ">", 2]:
                direction = 2 # Right
            else:
                direction = 8 # Left
        except (IndexError, ValueError):
            direction = 8 # Left
        # font
        try:
            font = sys.argv[5].lower()
            if font in ["cp437", "cp437_font", "cp437font", "cp_437", "cp_437font", "cp_437_font"]:
               font = CP437_FONT
            elif font in ["sinclairs_font", "sinclairs", "sinclair_s", "sinclair_s_font", "sinclairsfont"]:
               font = SINCLAIRS_FONT
            elif font in ["lcd_font", "lcd", "lcdfont"]:
               font = LCD_FONT
            elif font in ["tiny_font", "tiny", "tinyfont"]:
               font = TINY_FONT
            # Note: if further fonts are added to MAX7219fonts.py, add suitable references to parse command line arguments here
            else:
               font = CP437_FONT
        except (IndexError, ValueError):
            font = CP437_FONT
        # Call the marquee function with the parsed arguments
        try:
            scroll_message_horiz(message, repeats, speed, direction, font)
        except KeyboardInterrupt:
            clear_all()
    except IndexError:
        # If no arguments given, show help text
        print "MAX7219array.py"
        print "Scrolls a message across an array of MAX7219 8x8 LED boards"
        print "Run syntax:"
        print "  python MAX7219array.py message [repeats [speed [direction [font]]]]"
        print "    or, if the file has been made executable with chmod +x MAX7219array.py :"
        print "      ./MAX7219array.py message [repeats [speed [direction [font]]]]"
        print "Parameters:"
        print "  (none)               : displays this help information"
        print "  message              : any text to be displayed on the array"
        print "                         if message is more than one word, it must be enclosed in 'quotation marks'"
        print "                         Note: include blank space(s) at the end of 'message' if it is to be displayed multiple times"
        print "  repeats (optional)   : number of times the message is scrolled"
        print "                         repeats = 0 scrolls indefinitely until <Ctrl<C> is pressed"
        print "                         if omitted, 'repeats' defaults to 0 (indefinitely)"
        print "  speed (optional)     : how fast the text is scrolled across the array"
        print "                         1 (v.slow) to 9 (v.fast) inclusive (not necessarily integral)"
        print "                         if omitted, 'speed' defaults to 3"
        print "  direction (optional) : direction the text is scrolled"
        print "                         L or R - if omitted, 'direction' defaults to L"
        print "  font (optional)      : font to use for the displayed text"
        print "                         CP437, SINCLAIRS, LCD or TINY only - default 'font' if not recognized is CP437"
        print "MAX7219array.py can also be imported as a module to provide a wider range of functions for driving the array"
        print "  See documentation within the script for details of these functions, and how to setup the library and the array"
                                                               

