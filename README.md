# Nvidia-vBIOS-Clock-Power-Tweaker

## Disclaimer :
The goal of this tool is to allow users to read and edit clock, power and other settings of their nvidia GPU vBIOS. The guideline being to allow users to tune the performance of their GPU. Specifically targeted at mobile GPUs

**I am not a programmer, this code was written in python and then compiled thanks to pyinstaller. The code is not clean nor sexy, it works, it's not optimal but it shows that it can be done.**

It is now possible to save your custom vbios. **Be extremely careful, use a CH341a programmer w/ 1.8v adapter to recover from a vbios that bricks your card**. Very little testing has been done so far so expect the programe to brick your vbios ! You have been warned.

***Once editing is implemented it should only work for Pascal ! Newer cards won't accept a modified vBIOS, they will result in error 43 in windows, card doesn't initialize***

The app might crash if you feed it an incompatible vBIOS aka a vBIOS that I haven't tried yet, I implemented some redundancy but expect crashes non the less.

## Using the tool

Find the latest version in the [releases](https://github.com/JadeRover/Nvidia-vBIOS-Clock-Power-Tweaker/releases) and follow the instructions on how to run the program.

⚠️ **_ONLY VERSIONS STARTING FROM V1.3.4 WORK !! PRIOR VERSIONS FAIL TO CREATE VALID VBIOS_** ⚠️

Since it is written in python, you can either execute the python code directly or run a precompiled exe.

# Compatibility :

Latest version, v1.4 can now fully edit the vbios of most pascal mobile & desktop cards (turing and above still fail to load custom vbios due to extra security checks).
List of cards fully compatible :

- P3000, P4000, P5000, P3200, P4200 & P5200
- GTX 1050, 1050ti, 1060, 1070 & 1080
- P1000, P2000, mx150, mx250, P600m
- Tesla P6 & p106m can be edited but they are picky about the VP profile... Testing needed !

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

## Screenshots of V1.4:
The vbios shown is my personal P4000m OC vbios that enabled me to take the first place in 3D mark time spy =D

[3D mark Time Spy result](https://www.3dmark.com/search#advanced?test=spy%20P&cpuId=&gpuId=1273&gpuCount=1&gpuType=ALL&deviceType=ALL&storageModel=ALL&modelId=&showRamDisks=false&memoryChannels=0&country=&scoreType=graphicsScore&hofMode=false&showInvalidResults=false&freeParams=&minGpuCoreClock=&maxGpuCoreClock=&minGpuMemClock=&maxGpuMemClock=&minCpuClock=&maxCpuClock=)

<img width="818" height="755" alt="image" src="https://github.com/user-attachments/assets/7a225cf5-95f2-46c0-91c3-d50f1ee8f38f" />

<img width="819" height="755" alt="image" src="https://github.com/user-attachments/assets/7e33bac2-8906-47c5-a97c-91e9225593b0" />

<img width="813" height="752" alt="image" src="https://github.com/user-attachments/assets/694ee607-2956-43e5-9316-17c8abfcd94b" />

<img width="818" height="754" alt="image" src="https://github.com/user-attachments/assets/27d191b9-23bd-4ecd-9e72-e8dcbe5ecb87" />

<img width="818" height="756" alt="image" src="https://github.com/user-attachments/assets/ad2a7635-e193-46eb-a607-8aab93d4291b" />


## How it works
The tool uses recursive algorithms to find the data offsets for the different vBIOS tables that contain the info we want to read + edit.
This means that there is wide compatibility among the different generations of GPUs. However this also means that this tool **can make mistakes parsing the data** = I highly recommend to use good judgement as well as double checking the vbios info on sites such as techpowerup to make sure the vbios info you are getting is correct.

On the technical level, I explaine some of the code in comments in the files, the file that contains all the algorithms is the "_calcuator.py". Some of it is guess work (for some offset calculations).

## Current state/compatibility
The tool saves your edits and also fixes the checksum. Also fixes the checksum for "dual image" vbios such as RTX3000. However my personal testing of flashing a custom vbios to my RTX3000 kept bricking the card ! No compatibiity for flashing Turing and newer cards.

To calculate the clock values the tool applies some rounding. Saving a custom vbios then opening it again might have clock values with +-1 Mhz.

Compatibility :
- **Only PASCAL GPUs** are supported right now, mobile & desktop. You can make a custom vbios for turing and newer cards but the card will reject the vbios...

## TO-DO
- Add a thermal tab to edit thermal limits
- Add a display table tab to read and edit the display outputs of the GPU : DP_A, DP_B, DP_C, DP_D, etc -> Done thanks to ssj92's work !!
- Add more compatibility for the P6 gpus as well as maybe Blackwell GPUs (should be possible) -> Will come very soon as a much better understanding of the virtual p state cable can enable some editing -> Done !
- Compatibility for desktop cards (more variants than mobile, this will take time) -> Done !
- Add tab for eediting voltages of the card, however I doubt this will be achievable...

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
