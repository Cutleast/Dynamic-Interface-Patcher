# [NEW] Auto Patch Creator
### Dynamic Interface Construction Kit (DICK)

<p align="center">
<img src="https://i.imgur.com/76J8IOv.png" width="500px" />
<br>
<a href="https://www.nexusmods.com/skyrimspecialedition/mods/97864"><img src="https://i.imgur.com/STsBXT6.png" height="60px"/> </a>
<a href="https://github.com/Cutleast/Dynamic-Interface-Construction-Kit"><img src="https://imgur.com/x6joDMm.png" height="60px"/> </a>
</p>

This tool automatically creates a DIP-suitable patch from finished SWF files. Instructions on usage can be found in its [README.md](https://github.com/Cutleast/Dynamic-Interface-Construction-Kit).

# Manually creating Patches

**This documentation always refers to the latest version of the patcher!**

*Latest version as time of writing: v1.0*

Patches are done in two major steps. At first they are created in FFDec itself and then they get documented in a json files for the automated patcher.
A patch consists of two parts; a "Patch" folder that has the same folder structure as the mod to patch (including BSA files as folders). It contains the specifications and instructions for the patcher and there is a "Shapes" folder containing the shapes that will replace the shapes.

**NOTE:** You can view the status of official patches [here](https://www.nexusmods.com/skyrimspecialedition/mods/92345/?tab=forum&topic_id=12944454). It would be very great if you'd read through that **before** starting to create a patch yourself. We love to see the community take action but it doesn't help anyone if two people are working on a patch at the same time and we end up with two.

### Requirements for creating patches

- [JPEXS Free Flash Decompiler](https://github.com/jindrapetrik/jpexs-decompiler)
  - you have to know how to use it, of course
- (Skyrim) UI modding in general
- basic knowledge about JSON syntax

### Things that can be patched automatically using the patcher

- Shapes (svg files recommended; use png files at your own risk!)
- Everything else via the JSON files

# Patch folder structure

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

# Patch file structure

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

```bash
Usage: DIP.exe [-h] [-d] [-b] [patchpath] [originalpath]

Dynamic Interface Patcher (c) Cutleast

Positional Arguments:
  patchpath         Path to patch that gets automatically run. An original mod path must also be given!
  originalpath      Path to original mod that gets automatically patched. A patch path must also be given!

Options:
  -h, --help        Show this help message and exit
  -d, --debug       Enables debug mode so that debug files get outputted.
  -b, --repack-bsa  Enables experimental repacking of original BSA file(s).
```
