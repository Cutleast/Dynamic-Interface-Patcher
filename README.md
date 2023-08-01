<p align="center">
<img src="https://i.imgur.com/Tl3rkTE.png" width="500px" />
<br>
<a href="https://www.nexusmods.com/skyrimspecialedition/mods/96891"><img src="https://i.imgur.com/STsBXT6.png" height="60px"/> </a>
<a href="https://ko-fi.com/cutleast"><img src="https://i.imgur.com/KcPrhK5.png" height="60px"/> </a>
<br>

# Please Note!!!

**I take no responsibility for any problems that may occur or any assets that get redistributed without permission!**

# Description

This is a dynamic patching tool for ui mods with strict permissions like RaceMenu or MiniMap.
**No assets or files by the original mod authors get redistributed! Patching takes place exclusively locally and redistribution of the patched files is strictly prohibited according to the respective permissions.**
The tool requires a compatible patch to work. Those can be found on the Skyrim nexus on Nexus Mods by searching for something like "DIP Patch".
More info on creating patches can be found in the [documentation](./DOCUMENTATION.md).

# Features

- Fully automated patching
- Automatic extraction of BSA
- Can be installed as a mod in MO2 or Vortex
- Commandline arguments for auto patching

# Official Patches

See [here](./OfficialPatches.md) for a list of released and planned patches.

# Contributing

### 1. Feedback (Suggestions/Issues)

If you encountered an issue/error or you have a suggestion, create an issue under the "Issues" tab above.

### 2. Code contributions

1. Install Python 3.11 (Make sure that you add it to PATH!)
2. Clone repository
3. Open terminal in repository folder
4. Type in following command to install all requirements (Using a virtual environment is strongly recommended!):
   `pip install -r requirements.txt`

### 3. Execute from source

1. Open terminal in src folder
2. Execute main file
   `python main.py`

### 4. Compile and build executable

1. Follow the steps on this page [Nuitka.net](https://nuitka.net/doc/user-manual.html#usage) to install a C Compiler
2. Run `build.bat` with activated virtual environment from the root folder of this repo.
3. The executable and all dependencies are built in the main.dist-Folder.

# How it works

1. Copy original mod to a temp folder. (Extract BSAs if required)
2. Patch shapes.
3. Convert SWFs to XMLs.
4. Patch XMLs.
5. Convert XMLs back to SWFs.
6. Copy patched mod back to current directory.

# Credits

- Qt by The [Qt Company Ltd](https://qt.io)
- [bethesda-structs](https://github.com/stephen-bunn/bethesda-structs) by [Stephen Bunn](https://github.com/stephen-bunn)
- [FFDec](https://github.com/jindrapetrik/jpexs-decompiler) by [Jindra Petřík](https://github.com/jindrapetrik)
