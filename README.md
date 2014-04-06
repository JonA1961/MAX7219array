MAX7219array
============

Drive an array of MAX7219 8x8 LED matrices via SPI in Python from the Raspberry Pi

Files:

MAX7219array.py:
Library of functions for driving an array of daisy-chained MAX7219 8x8 LED matrix boards

MAX7219fonts.py:
Fonts data for use by the MAX7219array.py library

MAX7219array_demo.py:
Demonstration of the features in the MAX7219array library

MAX7219array_ReadMe.py:
Documentation file consisting largely of comments also included in the other files
See this file for more details


Installation of spidev module required to use this library:
Before you use these files, unless you already have it installed on your Pi, you need to install spidev.  I suggest you follow the same instructions that I used from http://www.100randomtasks.com/simple-spi-on-raspberry-pi (ignore the references to the TLC549 ADC but follow the instructions as far as the bit that reads "With all the setup now complete, it's time to write some python")

To download all the MAX7219array files, enter the following on your RPi at the command line prompt:

git clone https://github.com/JonA1961/MAX7219array.git

This will create a folder in your current folder called MAX7219array and copy the files from Github into it.

Note that the demo script is written for a set-up of 8 MAX7219 boards.  It should run even if you have a different number but will not (obviously) display exactly what I intended it to.  Looking at the code however you should see how to adapt it for your purposes, or how to use the library functions.

The wiring setup I used for the MAX7219 boards is documented in either the MAX7219array.py or the MAX7219array_ReadMe.py files.  You also need to set the value of NUM_MATRICES in the MAX7219array.py library file to the number of MAX7219 boards you have in your daisy-chain. 

To run the demo, in the MAX7219array folder, enter the following at the command line prompt:

  python MAX7219array_demo.py

To use the library file as a simple command-line utility to scroll a message on the array, first alter the permissions as follows:

  chmod +x MAX7219array.py
  
and you can then enter at the command line prompt:

  ./MAX7219array.py 'Your message goes here'


Note:
Written for Python 2.7.  I believe the main culprits requiring attention to make the library script compatible with Python 3 would be the print statements in the last 20 or so lines
