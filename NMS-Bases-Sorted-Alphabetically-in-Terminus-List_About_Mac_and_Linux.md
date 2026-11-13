# NMS-Bases-Sorted-Alphabetically-in-Terminus-List on macOS and Linux

**Compatibility is untested on macOS and Linux.** These instructions use the checked-in source. Run the Python script directly in place of the Windows batch launcher.

## macOS · Terminal

Use an existing Python 3.10 or later interpreter if available. Check it with `python3 --version`. Otherwise, with Homebrew installed, use:

```bash
brew install python@3.12
```

From Terminal, replace the example path with the path to your checkout. The block uses Homebrew Python. If using an existing installation, replace `"$(brew --prefix python@3.12)/bin/python3.12"` with its `python3` command or executable path.

```bash
cd "/path/to/NMS-Bases-Sorted-Alphabetically-in-Terminus-List"
"$(brew --prefix python@3.12)/bin/python3.12" -m venv .venv
source .venv/bin/activate
python --version
```

The source uses the Python standard library. There are no packages to install with pip.

Work on a copy of an exported save ZIP or readable JSON/HG text file. Replace the example path with your export. The script sorts the first `PersistentPlayerBases` array and writes JSON, ZIP, and text outputs beside the input. Use a writable folder and keep the original export separately.

```bash
python sort_nms_first_persistent_player_bases.py "$HOME/Saves/save.hg.zip"
```

## Linux · Bash

Use the command for your distribution if Python or its virtual environment support is missing. Check that `python3 --version` reports Python 3.10 or later.

```bash
# Ubuntu or Debian
sudo apt update
sudo apt install python3 python3-venv

# Fedora
sudo dnf install python3

# Arch Linux
sudo pacman -Syu python
```


```bash
cd "/path/to/NMS-Bases-Sorted-Alphabetically-in-Terminus-List"
python3 -m venv .venv
source .venv/bin/activate
python --version
```

The source uses the Python standard library. There are no packages to install with pip.

Work on a copy of an exported save ZIP or readable JSON/HG text file. Replace the example path with your export. The script sorts the first `PersistentPlayerBases` array and writes JSON, ZIP, and text outputs beside the input. Use a writable folder and keep the original export separately.

```bash
python sort_nms_first_persistent_player_bases.py "$HOME/Saves/save.hg.zip"
```

In a new terminal, return to the checkout and run `source .venv/bin/activate` before launching again.
