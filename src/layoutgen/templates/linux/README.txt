@@NAME@@ keyboard layout for Linux
==================================

Files:

  @@ID@@          XKB symbols file: what each key types
  @@ID@@.compose  Compose file: what the dead keys do
  evdev.xml       registry entry, so that keyboard settings list the layout
  install.py      installs the files for the current user

Install, in a terminal in this folder:

  python3 install.py

Then log out and back in. On GNOME, the script adds the layout as an input
source; elsewhere, add "English (@@NAME@@)" in the keyboard settings, or
use the XKB layout name @@ID@@ (in Sway: input * xkb_layout @@ID@@).
The alternative layer is on the right Alt key (AltGr).

To remove it again:

  python3 install.py --uninstall

The layout files go into ~/.config/xkb, which libxkbcommon reads in Wayland
sessions (GNOME, KDE Plasma, Sway, and others). The X server of an X11
session doesn't read them; install.py prints a command for that case.

The dead keys work through the Compose file, which install.py includes from
~/.XCompose. GTK, IBus, Qt, and most other programs read it; some (Snap and
Flatpak packages, some Electron programs) may not, and there the dead keys
type nothing.
