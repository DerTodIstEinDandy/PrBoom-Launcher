### PrBoom-Launcher

This is a simple GUI launcher for Prboom+, an enhanced Doom source port. It can
offer the following features:

* Easy way to launch every official Doom release, including Master Levels

* Automatic handling of -complevel options for official Doom releases,
  automatic load of tnt31 patch for TNT.wad

* A simple GUI that shows the load order of custom files

* Auto-creation of separate save folders for official releases, as well as for
  different combinations of custom pwads

* Preset saving and loading to switch between different custom wads easily

##### Quick Start

[Microsoft Visual C++ 2015 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=53587) is required for the Windows binary.

Put the launcher in the folder where your PrBoom+ executables are located. By
default the launcher assumes your OpenGL executable is called "glboom-plus", and
your software one is "prboom-plus". If the names of your binaries are
different, or if you only have one binary, be sure to enter the correct name(s)
in "Files" > "Executables" dialog box.

You can save/load launcher configurations, completely with all the custom game
options, in the "Presets" menu.

##### File locations

By default, the launcher assumes your WAD files are located in the same folder,
and your Master Levels files are in the "master" subfolder. You can set paths
to your IWAD, PWAD, Master Levels and NERVE.WAD folders in the "Files" menu. You
can also specify there a custom config file to use and a folder for your saved
games (by default, the launcher creates a new "saves" folder if  it doesn't
exist).

##### Easy launch of the official games

The "Official releases" tab allows you to start every official campaign in  a
couple of clicks. The correct settings, including the compatibility mode, are
applied automatically. The patch for TNT map 31 ("tnt31.wad") will be
auto-loaded, too, as long as you have it in your IWAD folder next to TNT.WAD.
(NOTE: If you start a custom game with TNT.WAD, the patch will still be
auto-added as the first file in the load order, for custom PWADs to override it)

##### Automatic save folder creation

The launcher auto-generates subfolders in your save folder based on the
game/PWAD combination you choose. Your Master Levels saves will go into
"saves/master", and saves  for AV.WAD will be in "saves/DOOM2_AV". If you don't
want this behavior, uncheck  "Files" > "Auto create save subfolders".

##### Video menu

"Video" menu allows you to choose whether to launch the OpenGL executable. You
can also set different resolution/screen mode for each of the binaries. "Disable
fullscreen desktop mode" is relevant if you're using [the unofficial build with
fullscreen desktop mode support](https://www.doomworld.com/forum/topic/31039-prboom-plus-ver-2514/?page=102&tab=comments#comment-1850772)

##### Compatibility modes

The launcher offers a dropdown menu to choose the most common compatibility
options. You can check in-depth overview of compatibility modes in the PrBoom+
documentation.

* If a custom wad you're going to play is designed for the original MS-DOS
  Doom.exe (classic releases like Memento Mori, or modern releases that have
  "vanilla  compatible" in their description), select one of the compatibility
  modes depending  on the base IWAD file: Ultimate Doom mode (also works for
  freedoom1.wad), DOOM2 mode (also works for freedoom2.wad) or Final Doom mode.

* If a custom wad has "BOOM compatible" in its description, select "BOOM
  compatible mode"

* If a custom wad has "MBF compatible" in its description, select "MBF
  compatible mode"

* "Don't set -complevel" option is useful when you're going to watch a demo and
  you want PrBoom+ to auto detect the correct compatibility option for it.


##### Python version

The program is written for Python 3.6. It was not tested with earlier versions.
