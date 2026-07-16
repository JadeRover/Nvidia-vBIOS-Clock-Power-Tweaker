# Nvidia-vBIOS-Clock-Power-Tweaker

## Disclaimer :
The goal of this tool is to allow users to read and edit clock, power and other settings of their nvidia GPU vBIOS. The guideline being to allow users to tune the performance of their GPU. Specifically targeted at mobile GPUs

**I am not a programmer, this code was written in python and then compiled thanks to pyinstaller. The code is not clean nor sexy, it works, it's not optimal but it shows that it can be done.**

It is now possible to save your custom vbios. **Be extremely careful, use a CH341a programmer w/ 1.8v adapter to recover from a vbios that bricks your card**. Very little testing has been done so far so expect the programe to brick your vbios ! You have been warned.

***Once editing is implemented it should only work for Pascal ! Newer cards won't accept a modified vBIOS, they will result in error 43 in windows, card doesn't initialize***

The app might crash if you feed it an incompatible vBIOS aka a vBIOS that I haven't tried yet, I implemented some redundancy but expect crashes non the less.

## Using the tool

Find the latest version in the releases : https://github.com/JadeRover/Nvidia-vBIOS-Clock-Power-Tweaker/releases and follow the instructions on how to run the program.

**_ONLY VERSIONS STARTING FROM V1.3.4 WORK !! PRIOR VERSIONS FAIL TO CREATE VALID VBIOS_**

Since it is written in python, you can either execute the python code directly or run a precompiled exe.

# Compatibility :

Latest version, v1.3.4 can now fully edit the vbios of most pascal mobile cards (turing and above still fail to load custom vbios due to extra security checks).
List of cards fully compatible :

P3000, P4000, P5000, P3200, P4200 & P5200
GTX 1050, 1050ti, 1060, 1070 & 1080
Cards not fully compatible:

P1000, P2000, mx150, mx250, P600m -> power table is still not understood yet, clock editing works

# Recommended settings :

Since you need a BIOS flasher to flash the custom vbios, I recommend that you read the vbios already on your card and then edit it with the program.

The program defaults to removing the vbios header, I strongly recommend to do this, keeping the vbios header might result in a bricked card. You can try keeping the header, if you get error 43 flash the custom vbios without a header.

Core clocks editing works great, keep in mind that the card won't go exactly to your "max core clock", it will default to the closest and lowest "allowed" core clock value.
Example :
-> set max core to 1905Mhz -> under load card will boost to a maximum of 1898Mhz since that's the nearest value

Anything above 1911Mhz isn't applied and the card will boost to a maxium of 1911Mhz.

Memory clocks editing is still hit or miss right now. Same as for core clocks, memory clocks will go to the nearest "allowed" memory clock. For instance, testing on a P4000m went like this :

stock memory of 3000Mhz -> set 4000Mhz and the card will boost to max 3500Mhz -> set to 4500Mhz and the card does go to 4500Mhz...

You can try different memory clock values and see what works...

## Screenshots of V1.3.4:
The vbios shown is my personal P4000m OC vbios that enabled me to take the first place in 3D mark time spy =D

https://www.3dmark.com/search#advanced?test=spy%20P&cpuId=&gpuId=1273&gpuCount=1&gpuType=ALL&deviceType=ALL&storageModel=ALL&modelId=&showRamDisks=false&memoryChannels=0&country=&scoreType=graphicsScore&hofMode=false&showInvalidResults=false&freeParams=&minGpuCoreClock=&maxGpuCoreClock=&minGpuMemClock=&maxGpuMemClock=&minCpuClock=&maxCpuClock=

<img width="1019" height="932" alt="image" src="https://github.com/user-attachments/assets/6b4da0d9-e550-4a2c-951b-4583168fcd26" />

<img width="1019" height="934" alt="image" src="https://github.com/user-attachments/assets/302fb96b-9de4-4561-9d4e-8fac7af945ff" />

<img width="1022" height="936" alt="image" src="https://github.com/user-attachments/assets/2a4d9646-c348-407c-8c62-b396edb2dfce" />


## How it works
The tool uses recursive algorithms to find the data offsets for the different vBIOS tables that contain the info we want to read + edit.
This means that there is wide compatibility among the different generations of GPUs. However this also means that this tool **can make mistakes parsing the data** = I highly recommend to use good judgement as well as double checking the vbios info on sites such as techpowerup to make sure the vbios info you are getting is correct.

On the technical level, I explaine some of the code in comments in the files, the file that contains all the algorithms is the "_calcuator.py". Some of it is guess work (for some offset calculations).

## Current state/compatibility
The tool saves your edits and also fixes the checksum. Also fixes the checksum for "dual image" vbios such as RTX3000. However my personal testing of flashing a custom vbios to my RTX3000 kept bricking the card ! No compatibiity for flashing Turing and newer cards.

To calculate the clock values the tool applies some rounding. Saving a custom vbios then opening it again might have clock values with +-1 Mhz.

Compatibility :
- **ONLY Mobile GPUs** are supported right now. I had a look at desktop cards and they have similar architecture to the quadro P6 cards. Implementation should be possible in the future.
- Most mobile cards that are tested from the Pascal to Ada Lovelace area are supported, I haven't checked the "MXOOO" cards yet.

## TO-DO
- Add a thermal tab to edit thermal limits
- Add a display table tab to read and edit the display outputs of the GPU : DP_A, DP_B, DP_C, DP_D, etc -> Done thanks to ssj92's work !!
- Add more compatibility for the P6 gpus as well as maybe Blackwell GPUs (should be possible) -> Will come very soon as a much better understanding of the virtual p state cable can enable some editing
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
