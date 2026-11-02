# NMS Bases Sorted Alphabetically in Terminus List

Sort your **No Man's Sky → Terminus → My Bases** list by base name using an exported save file.

This Python utility reorders the base records in the **first `PersistentPlayerBases` array** in a save export. In the workflow tested during this project's development, that array determined the order shown in My Bases. The script creates modified exports for you to import with your save editor; running it alone does not update the game.

A naming scheme such as `G209-FOOTHOLD-PORTAL` makes the result especially useful: bases can be grouped by galaxy number, then by name.

The resulting file then becomes THE FULL JSON FILE THAT ONE IMPORTS BACK INTO THE GAMESAVE EDITOR, REPLACING THE ORIGINAL EXPORT AND THUS REPLACING THE ENTIRE GAMESAVE FILE. This is fine because the only change to the file is the sort-order of the bases.

## Usefulness of this tool has diminished
With Vectorcmdr's subsequent incorporation of base-list sorting in his excellent NMSE tool, my file becomes somewhat moot. His front-end is very cool, and he keeps up with NMS code-changes. I suggest using this tool more for the fun of analyzing the Python code than for sorting your bases. Use his tool instead.

See: https://github.com/vectorcmdr/NMSE and https://nmse.vectorcmdr.xyz/ 

## What it changes

- Sorts names without regard to capitalization, with numbers compared numerically: `G2` comes before `G10`.
- Places records with blank or missing names after named bases.
- Keeps the original order when sort keys are equal.
- Moves complete base objects while preserving their raw JSON text and the array's existing separator/indentation layout.
- Leaves text outside the first array unchanged, including any later `PersistentPlayerBases` sections.
- Checks that the reordered array contains exactly the same raw base objects and that the second section, if present, remains unchanged.

It does not rename bases or change their building parts, coordinates, ownership, or timestamps.

### Why only the first section?

The development conversation, **NMS JSON Reordering Help**, established that sorting the first section changed the visible Terminus order, and the author confirmed that it worked in-game. The second section appeared to serve a separate persistence/sync role; its exact purpose was not established. This tool deliberately leaves it alone.

The script selects the first occurrence in file order, rather than selecting a context by name. This behavior was tested with the author's export layout; it is not a guarantee for every save layout or future game version.

## Requirements

- **Python 3.10 or newer.** Only the Python standard library is used; there are no packages to install.
- A save editor that can export readable NMS save JSON and import the edited result.
- A **UTF-8 text export**, either on its own or inside a ZIP archive, containing the readable key `PersistentPlayerBases`.

A file ending in `.hg` must already be a readable text export. The script does not decode native compressed or encrypted game saves, access cloud saves, or write directly to a live save slot.

## Quick start

1. Back up your game save and close No Man's Sky before editing it.
2. Export the intended save slot as readable JSON using your save editor. Keep an untouched copy.
3. Put the export and `sort_nms_first_persistent_player_bases.py` in the same folder, then open a terminal in that folder.
4. Run the script with the export's filename:

   ```powershell
   python sort_nms_first_persistent_player_bases.py save.hg.zip
   ```

   If your Windows installation uses the Python launcher, use:

   ```powershell
   py sort_nms_first_persistent_player_bases.py save.hg.zip
   ```

   For a raw JSON export or a path containing spaces:

   ```powershell
   py sort_nms_first_persistent_player_bases.py "C:\NMS Exports\my-save.json"
   ```

5. Review the completion report. Check the number of records sorted, the first and last names, and the integrity-check messages.
6. Import the **full modified JSON or ZIP**, whichever your editor accepts, into the same intended save slot. Save the changes in the editor.
7. Load that save in NMS and check **Terminus → My Bases**. Retain your backup until you have verified the result.

Export/import controls vary by editor. This repository supplies the sorter, not a save editor.

### Windows batch shortcut

`Parse by Base Names.bat` runs:

```bat
python sort_nms_first_persistent_player_bases.py save.hg.zip
pause
```

Run it from the repository folder with an export named `save.hg.zip` beside the script. Edit the batch file if your export has a different name or your installation requires `py` instead of `python`. The pause keeps the result or error visible.

## Generated files

The script writes three files beside the input. For `save.hg.zip`, they are:

| File | Contents / use |
| --- | --- |
| `save.hg_first_bases_sorted_by_name_raw_preserved.json` | Full modified save export, for import into an editor that accepts JSON. |
| `save.hg_first_bases_sorted_by_name_raw_preserved.zip` | Full modified export in a ZIP, for an editor that accepts that format. |
| `save.hg_sorted_first_PersistentPlayerBases.txt` | Only the sorted first section, for inspection or a deliberate section-level edit. This is not a complete save export. |

The ZIP contains one modified text file, using the selected input member's filename without its folder path. It does not reproduce every member of the original archive.

**The original input is not modified. Existing generated files with the same names are overwritten on another run.** Copy outputs elsewhere if you want to keep multiple results.

## Input details and limits

- For ZIP input, use an archive containing just the intended save export. If there are multiple files, the script selects the first `.json`, `.hg`, or `.txt` member; if none match, it selects the first file. It does not ask you to choose.
- Each base object must be valid JSON with an optional top-level `Name` field. The script parses individual base objects rather than reserializing the entire save.
- Raw object text is preserved, but the output files are written as UTF-8 without a byte-order mark. This is not a byte-for-byte copy of the original archive or file encoding.
- An empty first base array or a missing `PersistentPlayerBases` key causes an error.
- This is a one-time reorder of an export. It does not keep the in-game list automatically sorted after later changes.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `python` is not recognized, or Windows offers the Microsoft Store | Install Python 3.10+ or try `py` if it is already installed. |
| `Input file does not exist` | Check the filename and current folder, or pass the full path in quotes. |
| `No PersistentPlayerBases sections found` | Confirm that you supplied a readable save export with unobfuscated field names, and that the ZIP contains the intended file. |
| `First PersistentPlayerBases section contains no base records` | Check that you exported the intended slot and that its first base section contains records. |
| JSON parsing or UTF-8 decoding error | Re-export readable UTF-8 JSON. A native save file is not interchangeable with a JSON export. |
| Game order has not changed | Confirm that you imported and saved the full modified export into the correct slot, then reloaded it. Check that your export layout matches the first-section behavior described above. |

If an integrity check fails, do not import the result. Keep the original export and inspect the error.

## Repository files

| File | Purpose |
| --- | --- |
| `sort_nms_first_persistent_player_bases.py` | Main command-line utility. |
| `sort_nms_first_persistent_player_bases_v1.0.py` | Versioned copy; currently identical to the main script. |
| `Parse by Base Names.bat` | Windows shortcut for the example ZIP input. |
| [Original PDF guide](README%20-%20%20NMS%20Bases%20Sorted%20Alphabetically%20in%20Terminus%20List_2026-05-21.pdf) | Earlier documentation dated May 21, 2026. |
| [READEME_old.md](READEME_old.md) | Original short README, preserved unchanged. |
