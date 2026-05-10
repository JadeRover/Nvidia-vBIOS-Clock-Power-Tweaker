# Nvidia-vBIOS-Clock-Power-Tweaker

## Disclaimer :
The goal of this tool is to allow users to read and edit clock, power and other settings of their nvidia GPU vBIOS. The guideline being to allow users to tune the performance of their GPU. Specifically targeted at mobile GPUs

**I am not a programmer, this code was written in python and then compiled thanks to pyinstaller. The code is not clean nor sexy, it works, it's not optimal but it shows that it can be done.**

It is now possible to save your custom vbios. **Be extremely careful, use a CH341a programmer w/ 1.8v adapter to recover from a vbios that bricks your card**. Very little testing has been done so far so expect the programe to brick your vbios ! You have been warned.

***Once editing is implemented it should only work for Pascal ! Newer cards won't accept a modified vBIOS, they will result in error 43 in windows, card doesn't initialize***

The app might crash if you feed it an incompatible vBIOS aka a vBIOS that I haven't tried yet, I implemented some redundancy but expect crashes non the less.

## Using the tool

Find the latest version in the releases and follow the instructions on how to run the program.

Since it is written in python, you can either execute the python code directly or run a precompiled exe.

## Screenshots :
The vbios in the picture is my personnal 1060M MXM vbios that I edited by hand to change power limits + enable power slider.

<img width="445" height="507" alt="image" src="https://github.com/user-attachments/assets/28d65235-4dff-493f-9925-d296ab4e94ff" />

<img width="448" height="508" alt="image" src="https://github.com/user-attachments/assets/d2f233a8-ac10-430c-aba0-06d872b87d7e" />

## How it works
The tool uses recursive algorithms to find the data offsets for the different vBIOS tables that contain the info we want to read + edit.
This means that there is wide compatibility among the different generations of GPUs. However this also means that this tool **can make mistakes parsing the data** = I highly recommend to use good judgement as well as double checking the vbios info on sites such as techpowerup to make sure the vbios info you are getting is correct.

On the technical level, I explaine some of the code in comments in the files, the file that contains all the algorithms is the "_calcuator.py". Some of it is guess work (for some offset calculations).

## Current state/compatibility
The tool saves your edits and also fixes the checksum. Also fixes the checksum for "dual image" vbios such as RTX3000. However my personal testing of flashing a custom vbios to an RTX3000 kept bricking the card ! No compatibiity for flashing Turing and newer cards.

To calculate the clock values the tool applies some rounding. Saving a custom vbios then opening it again might have clock values with +-1 Mhz.

Compatibility :
- **ONLY Mobile GPUs** are supported right now. I had a look at desktop cards and they have similar architecture to the quadro P6 cards. Implementation should be possible in the future.
- Most mobile cards that are tested from the Pascal to Ada Lovelace area are supported, I haven't checked the "MXOOO" cards yet.

## TO-DO
- Add a thermal tab to edit thermal limits
- Add a display table tab to read and edit the display outputs of the GPU : DP_A, DP_B, DP_C, DP_D, etc
- Add more compatibility for the P6 gpus as well as maybe Blackwell GPUs (should be possible)
- Compatibility for desktop cards (more variants than mobile, this will take time)

## Sources
There is little info online of all the vbios data tables that containt the info we want to get to. Here are my sources that allowed me to understand some of these structures. 

https://nvidia.github.io/open-gpu-doc/BIOS-Information-Table/BIOS-Information-Table.html
This table has info on all the known vbios tables, however some are out of date.

https://github.com/envytools/envytools/tree/master/nvbios
This repository contains tools that users can build to access info inside the vbios tables, however these tables are also out of date for the most part

https://www.techpowerup.com/forums/threads/rtx40x0-vbios-viewer-kepler-ada-nvidia-vbios-visualizer-opensource-pattern-for-imhex.322299/
This parsing file used with the ImHex tool gave great insight on how to find offsets for the different tables of the vbios.

https://github.com/LaneLyng/MobilePascalTDPTweaker/
This repository is a tool for editing pascal/turing vbios power + thermal limits. Reverse engineering it's operations gave insight on power limits.

https://forums.macrumors.com/threads/imac-2011-maxwell-and-pascal-gpu-upgrade.2300989/
This forum has user made vBIOS for pascal cards that bumped up the clock limits. Reverse engineering their vBIOS gave great insight on Virtual P tables (VP tables) that control clock frequencies of GPUs.
