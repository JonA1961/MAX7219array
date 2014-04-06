#!/usr/bin/env python
# -----------------------------------------------------------
# This filename: MAX78219array_ReadMe.py
# -----------------------------------------------------------
# Documentation read-me file for MAX7219array.py library
#   and the suppporting files
# Largely duplicates comments in the scripts
# -----------------------------------------------------------
# -----------------------------------------------------------
#
#
#
#
# -----------------------------------------------------------
# -----------------------------------------------------------
# Library filename: MAX7219array.py
# -----------------------------------------------------------
# MAX7219array library - functions for driving an array of
# daisy-chained MAX7219 8x8 LED matrix boards
#
# v1.0
# JLC Archibald 2014
# -----------------------------------------------------------
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
# -----------------------------------------------------------
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
# -----------------------------------------------------------
# Based on and extended from the max7219 module by RM Hull
#   (see https://github.com/rm-hull/max7219)
#   but uses the spidev module to provide the SPI interface
#   instead of the SPI-Py C extension used by max7219
# -----------------------------------------------------------
# Requires:
# - python-dev & py-spidev modules, see install instructions
#   at www.100randomtasks.com/simple-spi-on-raspberry-pi
# - MAX7219fonts.py file containing font bitmaps
# - User should also set NUM_MATRICES variable below to the
#   appropriate value for the setup in use.  Failure to do
#   this will prevent the library functions working properly
# -----------------------------------------------------------
# The functions from spidev used in this library are:
#   xfer()  : send bytes deasserting CS/CE after every byte
#   xfer2() : send bytes only de-asserting CS/CE at end
# -----------------------------------------------------------
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
# -----------------------------------------------------------
# See further documentation of each library function below
# Also see MAX7219array_demo.py script for examples of use
# MAX7219 datasheet gives full details of operation of the
# LED driver chip
# -----------------------------------------------------------
#
# List of library functions:
# --------------------------
#
# Note that the functions below have both compulsory and
# optional arguments.  Optional arguments can be seen in the
# syntax for each function as they have default definitions
# which will be used of the argument is not provided when the
# function is called.  Where an argument in the function
# syntax do not have these default definitions, they are
# compulsory and must be provided when the function is called
#   eg in the function:
#     send_matrix_letter(matrix, char_code, font=EFAULT_FONT):
#   the arguments 'matrix' & 'char_code' are compulsory and
#   must be provided whenever the function is called
#   However, 'font=DEFAULT_FONT' means that the argument
#   'font' COULD be provided when the function is called,
#   but if it is omitted, then the value of DEFAULT_FONT
#   will be used instead
#
# Low-level basic functions:
# ..........................
#
# send_reg_byte(register, data):
#     Send one byte of data to one register via SPI port,
#     then raise CS to latch.  Note that subsequent sends
#     will cycle this tuple through to successive MAX7219 chips
#
# send_bytes(datalist):
#     Send sequence of bytes (should be [register,data] tuples)
#     via SPI port, then raise CS. Included for ease of
#     remembering the syntax rather than the native spidev
#     command, but also to avoid reassigning to 'datalist'
#     argument
#
# send_matrix_reg_byte(matrix, register, data):
#     Send one byte of data to one register in just one MAX7219
#     without affecting others
#
# send_all_reg_byte(register, data):
#     Send the same byte of data to the same register in all
#     of the MAX7219 chips
#
# Housekeeping functions:
# .......................
#
# clear(matrix_list):
#     Clear one or more specified MAX7219 matrices (argument(s)
#     to be specified as a [list] even if just one)
#
# clear_all():
#     Clear all of the connected MAX7219 matrices
#
# brightness(intensity):
#     Set a specified brightness level on all of the connected
#     MAX7219 matrices
#     Intensity: 0-15 with 0=dimmest, 15=brightest; in practice
#       the full range does not represent a large difference
#
# init():
#     Initialise all of the MAX7219 chips (see datasheet for
#     details of registers) to the following settings:
#       show all 8 digits / using a LED matrix (not digits) /
#       no display test / not in shutdown mode
#     Also ensure the whole array is blank, set brightness &
#     clear the graphics buffer
#
# Text-based functions:
# .....................
#
# send_matrix_letter(matrix, char_code, font=DEFAULT_FONT):
#     Send one character from the specified font to a
#     specified MAX7219 matrix
#
# send_matrix_shifted_letter(matrix, curr_code, next_code, progress, direction=DIR_L, font=DEFAULT_FONT):
#     Send to one MAX7219 matrix a combination of two
#     specified characters, representing a partially-
#     scrolled position
#     progress: 0-7: how many pixels the characters are shifted:
#       0=curr_code fully displayed;
#       7=one pixel less than fully shifted to next_code
#     With multiple matrices, this function sends many NO_OP
#     tuples, limiting the scrolling speed achievable for a
#     whole line.  scroll_message_horiz() and
#     scroll_message_vert() are more efficient and can scroll
#     a whole line of text faster
#
# static_message(message, font=DEFAULT_FONT):
#     Send a stationary text message to the array of MAX7219
#     matrices.  Message will be truncated from the right to
#     fit the array
#
# scroll_message_horiz(message, repeats=0, speed=3, direction=DIR_L, font=DEFAULT_FONT, finish=True):
#     Scroll a text message across the array, for a specified
#     number of times
#     repeats=0 gives indefinite scrolling until script is
#       interrupted
#     speed: 0-9 for practical purposes; speed does not have
#       to be integral
#     direction: DIR_L or DIR_R only; DIR_U & DIR_D will
#       do nothing
#     finish: True/False - True ensures array is clear at end,
#       False ends with the last column of the last character
#       of message still displayed on the array - this is
#       included for completeness but rarely likely to be
#       required in practice
#     Scrolling starts with message off the RHS(DIR_L)
#     /LHS(DIR_R) of array, and ends with message off the
#     LHS/RHS
#     If repeats>1, add space(s) at end of 'message' to
#     separate the end of message & start of its repeat
#
# scroll_message_vert(old_message, new_message, speed=3, direction=DIR_U, font=DEFAULT_FONT, finish=True):
#     Transitions vertically between two different
#     (truncated if necessary) text messages
#     speed: 0-9 for practical purposes; speed does not
#       have to integral
#     direction: DIR_U or DIR_D only; DIR_L & DIR_R
#       will do nothing
#     finish: True/False : True completely displays
#       new_message at end, False leaves the transition
#       one pixel short.  False should be used to ensure
#       smooth scrolling if another vertical scroll is
#       to follow immediately
#
# wipe_message(old_message, new_message, speed=3, transition=DISSOLVE, font=DEFAULT_FONT):
#     Transition from one message (truncated if necessary)
#     to another by a 'wipe' or 'dissolve'
#     speed: 0-9 for practical purposes; speed does not
#       have to integral
#     transition: WIPE_U, WIPE_D, WIPE_L, WIPE_R, WIPE RU,
#       WIPE_RD, WIPE_LU, WIPE_LD to wipe each letter
#       simultaneously in the respective direction
#     The diagonal directions do not give a true corner
#     -to-corner 'wipe' effect
#     OR transition: DISSOLVE for a pseudo-random dissolve
#       from old_message to new_message
#
# Graphics-based functions:
# .........................
#
# gfx_set_px(g_x, g_y, state=GFX_INVERT):
#     Set an individual pixel in the graphics buffer to on,
#     off, or the inverse of its previous state
#
# gfx_set_col(g_col, state=GFX_INVERT):
#     Set an entire column in the graphics buffer to on,
#     off, or the inverse of its previous state
#
# gfx_set_all(state=GFX_INVERT):
#     Set the entire graphics buffer to on, off, or the
#     inverse of its previous state
#
# gfx_line(start_x, start_y, end_x, end_y, state=GFX_INVERT, incl_endpoint=GFX_ON):
#     Draw a staright line in the graphics buffer between
#     the specified start- & end-points.  The line can be
#     drawn by setting each affected pixel to either on,
#     off, or the inverse of its previous state
#     The final point of the line (end_x, end_y) can
#     either be included (default) or omitted.  It can be
#     usefully omitted if drawing another line starting
#     from this previous endpoint using GFX_INVERT
#
# gfx_letter(char_code, start_x=0, state=GFX_INVERT, font=DEFAULT_FONT):
#     Overlay one character from the specified font into
#     the graphics buffer, at a specified horizontal position
#     The character is drawn by setting each affected pixel
#     to either on, off, or the inverse of its previous state
#
# gfx_sprite(sprite, start_x=0, state=GFX_INVERT):
#     Overlay a specified sprite into the graphics buffer,
#     at a specified horizontal position.  The sprite is
#     drawn by setting each affected pixel to either on,
#     off, or the inverse of its previous state
#     Sprite is an 8-pixel (high) x n-pixel wide pattern,
#     expressed as a list of n bytes
#       eg [0x99, 0x66, 0x5A, 0x66, 0x99]
#
# gfx_scroll(direction=DIR_L, start_x=0, extent_x=8*NUM_MATRICES, start_y=0, extent_y=8, new_pixels=GFX_OFF):
#     Scroll the specified area of the graphics buffer
#     by one pixel in the given direction
#     direction: any of DIR_U, DIR_D, DIR_L, DIR_R, DIR_LU,
#     DIR_RU, DIR_RD, DIR_LD
#     Pixels outside the rectangle are unaffected; pixels
#     scrolled outside the rectangle are discarded
#     The 'new' pixels in the gap created are either set
#     to on or off depending upon the new_pixels argument
#
# gfx_read_buffer(g_x, g_y):
#     Return the current state (on=True, off=False) of an
#     individual pixel in the graphics buffer
#     Note that this buffer only reflects the operations
#     of these gfx_ functions, since the buffer was last
#     cleared.  The buffer does not reflect the effects
#     of other library functions such as
#     send_matrix_letter() or (static_message()
#
# gfx_render():
#     All of the above gfx_ functions only write to (or
#     read from) a graphics buffer maintained in memory
#     This command sends the entire buffer to the matrix
#     array - use it to display the effect of one or more
#     previous gfx_ functions
#
# Internal functions:
# ...................
# (used by other library functions; not intended for use
#   directly by user-scripts)
#
# scroll_text_once(text, delay, direction, font):
#     Subroutine used by scroll_message_horiz(), scrolls
#     text once across the array, starting & ending with
#     'text' on the array
#     NOTE: Not intended to be used as a user routine;
#     if used, note different syntax: compulsory arguments
#     & requires delay rather than speed
#
# trim(text):
#     Trim or pad specified text to the length of the
#     MAX7219 array
#
# -----------------------------------------------------
#
# Execution from the command line
#
# As well as being used as a library of functions, the
# library script can itself be run directly from the
# command line.  In this case, it scrolls a message
# across the array of MAX7219 8x8 LED boards, with
# optional arguments controlling the display
#
# Run syntax:
#     python MAX7219array.py message [repeats [speed [direction [font]]]]
# or, if the file has been made executable with
# chmod +x MAX7219array.py :
#     ./MAX7219array.py message [repeats [speed [direction]]]
#
# Parameters:
#   (none)               : displays this help information
#   message              : any text to be displayed on the array
#                          if message is more than one word,
#                          it must be enclosed in 'quotation marks'
#                          Note: include blank space(s) at the end
#                          of 'message' if it is to be displayed
#                          multiple times
#   repeats (optional)   : number of times the message is scrolled
#                          repeats = 0 scrolls indefinitely until
#                          <Ctrl<C> is pressed
#                          if omitted, 'repeats' defaults to
#                          0 (indefinitely)
#   speed (optional)     : how fast the text is scrolled across
#                          the array
#                          1 (v.slow) to 9 (v.fast) inclusive
#                          (not necessarily integral)
#                          if omitted, 'speed' defaults to 3
#   direction (optional) : direction the text is scrolled
#                          L or R - if omitted, 'direction'
#                          defaults to L
#   font (optional)      : font to use for the displayed text
#                          CP437, SINCLAIRS, LCD or TINY only
#                          default 'font' if not recognized
#                          is CP437
# -----------------------------------------------------------
# -----------------------------------------------------------
#
#
#
#
# -----------------------------------------------------------
# -----------------------------------------------------------
# Fonts filename: MAX7219fonts.py
# -----------------------------------------------------------
# Fonts data for use by the MAX7219array.py library
#
# v1.0
# JLC Archibald
# -----------------------------------------------------------
# Structure:
# - each font is a list of 256 characters
# - each character represented as an 8x8 binary bitmap:
# - each character's data comprises an 8-byte list
# - each byte represents one column of the character
# - the bytes are in column order left-to-right
# - the bits in each byte are in row order: MSB (bottom row)
#     to LSB (top row)
# - some fonts only have non-zero (ie non-blank) data for
#     characters in the range 0x20 to 0x7F
# -----------------------------------------------------------
# Each font's source is listed, although some have had
#   to be transposed to the above structure
# -----------------------------------------------------------
# Additional 8x8 fonts can be added as follows:
# - add additional list data at the bottom of the fonts file
# - ensure that the file structure is maintained, and
#     that the new font data is in the same form
# - include zero data for any non-repesented characters, so
#     that every font variable is a 256x8 nested list
# - import the variable names representing the additional
#     fonts into the MAX7219array.py library, and into the
#     main script where they will be used as arguments to
#     the library functions
# -----------------------------------------------------------
# -----------------------------------------------------------
#
#
#
#
# -----------------------------------------------------------
# -----------------------------------------------------------
# Demo script filename: MAX7219array_demo.py
# -----------------------------------------------------------
# Demonstration of the features in the MAX7219array library
#
# v1.0
# JLC Archibald 2014
# -----------------------------------------------------------
# Inspired by and based on the max7219 module by RM Hull
# (see https://github.com/rm-hull/max7219)
# -----------------------------------------------------------
# See MAX7219array.py library file for more details
# -----------------------------------------------------------
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
# -----------------------------------------------------------
# -----------------------------------------------------------
