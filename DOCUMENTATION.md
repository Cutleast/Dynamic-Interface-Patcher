# Creating Patches

Patches are done in two major steps. At first they are created in FFDec itself and then they get processed by the patch creator of DIP.

**NOTE:** You can view the status of official patches [here](OfficialPatches.md). It would be very great if you'd read through that **before** starting to create a patch yourself. We love to see the community take action but it doesn't help anyone if two people are working on a patch at the same time and we end up with two.

### Requirements for creating patches

- [JPEXS Free Flash Decompiler](https://github.com/jindrapetrik/jpexs-decompiler)
  - you have to know how to use it, of course
- (Skyrim) UI modding in general

### Things that can be patched automatically using the patcher

- Shapes (svg files recommended; use png files at your own risk!)
- Everything else via the JSON files

## Instructions

1. Create your patched SWF files in FFDec as you would publish them.
2. Start DIP and go to the "Patch creator" tab.
3. Put in the path to the original mod.
4. Put in the path to the folder with your patched SWF files (same folder structure as the original mod without BSA).
5. (Optional) Put in a path for the output to appear in.
6. Click on *Run!*
7. The output gets generated in a `Output` folder where DIP.exe is located or at your specified location.
8. If the original mod had a BSA, create a folder with the full filename of the BSA in the `Patch` folder and move everything that's normally in the BSA in it.

For example:

`Direct output`:

```
Output (root folder)
├── Patch
|   └── interface
|       ├── racemenu
|       |   └── buttonart.json
|       └── racesex_menu.json
└── Shapes
    ├── shape_1.svg
    └── shape_2.svg
```

`Finished output` (with created BSA folder):

```
Output (root folder)
├── Patch
|   └── RaceMenu.bsa
|       └── interface
|           ├── racemenu
|           |   └── buttonart.json
|           └── racesex_menu.json
└── Shapes
    ├── shape_1.svg
    └── shape_2.svg
```

9. Now you can publish the content of the output folder in a subfolder named like your patch (for eg. `Nordic UI - RaceMenu - DIP Patch`) so that the folder structure in Skyrim's data folder would look like this:

```
data (in Skyrim's installation directory)
└── Nordic UI - RaceMenu - DIP Patch (the Output folder)
    ├── Patch
    |   └── RaceMenu.bsa
    |       └── interface
    |           ├── racemenu
    |           |   └── buttonart.json
    |           └── racesex_menu.json
    └── Shapes
        ├── shape_1.svg
        └── shape_2.svg
```

10. The usage of a simple FOMOD is strongly recommended to avoid mod managers warning that the mod does not look correct for the data folder.

## For advanced users

If encounter some edge cases and the auto-generated patch causes some weird issues, check out the `config/patch_creator_config.json` config file and try to tweak it.

# Patch structure

The root folder name should contain "DIP" for the patcher to auto detect it and the "Patch" folder has the same structure as the mod that gets patched. This includes BSA archives as folders. For example, to patch `racesex_menu.swf` from the RaceMenu mod the path of the respective JSON file looks like this:

`<RaceMenu>/RaceMenu.bsa/interface/racesex_menu.json`

And a complete RaceMenu patch could look like this:

`Example patch`:

```
data (in Skyrim's installation directory)
└── Example DIP Patch (root folder)
    ├── Patch
    |   └── RaceMenu.bsa
    |       └── interface
    |           ├── racemenu
    |           |   └── buttonart.json
    |           └── racesex_menu.json
    └── Shapes
        ├── shape_1.svg
        └── shape_2.svg
```

## Patch file structure

A Patch JSON file consists of two major parts:

- the shapes, their file paths and the ids they replace

and

- the swf itself, where everything else can be modified

There's also an optional "optional" tag to indicate that the original SWF doesn't have to exist for the patch to succeed.
DIP will then ignore this patch file if the original SWF is missing instead of throwing an error.

#### SWF (XML) Patch structure

The patcher converts the SWF files to XML files and modifies them according to the changes specified in the `swf` part of the JSON file.
Therefore this part of the JSON has a very similar structure and it is recommended to familiarize yourself with the general structure of the SWF file when it is converted to an XML file (FFDec has an export feature for this).
Since not all changes should be applied to every element in the file, filters are required to use. There are three different "prefixes" to differentiate between filters, changes and parent elements:

| Type of key | Prefix |
| ----------- | ------ |
| Filters     | #      |
| Changes     | ~      |
| Parents     | None   |

<hr>

`patch.json`:

```json
{
    "shapes": [
        {
            "id": "1,2,5,7,9",
            "fileName": "example.svg" // Path relative to "Shapes" folder
        }
    ],
    "optional": true, // this tag itself is optional and indicates that the original file doesn't have to exist for the patch to succeed
    // '#' for filters | '~' for changes | '' for parent elements
    "swf": {
        "displayRect": {
            "~Xmax": "25600",
            "~Xmin": "0",
            "~Ymax": "14400",
            "~Ymin": "0"
        },
        "tags": [
            {
                "#type": "DefineSpriteTag",
                "#spriteId": "3",
                "subTags": [
                    {
                        "#type": "PlaceObject2Tag",
                        "#characterId": "2",
                        "#depth": "1",
                        "~placeFlagHasMatrix": "true"
                    },
                    {
                        "#type": "PlaceObject2Tag",
                        "#characterId": "2",
                        "#depth": "1",
                        "matrix": {
                            "~hasScale": "true",
                            "~scaleX": "0",
                            "~scaleY": "0"
                        }
                    }
                ]
            },
            {
                "#type": "DefineEditTextTag",
                "#characterID": "5",
                "textColor": {
                    "~type": "RGBA",
                    "~alpha": "255",
                    "~blue": "255",
                    "~green": "255",
                    "~red": "255"
                }
            }
        ]
    }
}
```

# Patcher Commandline Usage

```
Usage: DIP.exe [-h] [-d] [-b] [-o OUTPUT_PATH] [-s] [patchpath] [originalpath]

Dynamic Interface Patcher (c) Cutleast

Positional Arguments:
  patchpath             Path to patch that gets automatically run. An original mod path must also be given!
  originalpath          Path to original mod that gets automatically patched. A patch path must also be given!

Options:
  -h, --help            Show this help message and exit
  -d, --debug           Enables debug mode so that debug files get outputted.
  -b, --repack-bsa      Enables experimental repacking of original BSA file(s).
  -o, --output-path OUTPUT_PATH
                        Specifies output path for patched files.
  -s, --silent          Toggles whether the GUI is shown while patching automatically.
```
