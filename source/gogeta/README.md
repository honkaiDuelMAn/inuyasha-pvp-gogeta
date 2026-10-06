# Gogeta build inputs

This folder contains the reproducible source manifest and replaceable artwork used to add character key `go` (오지터) to the separate Gogeta PvP repository.

The Manga RPG input is never copied into this repository. `input-hashes.json` pins the user-provided `RPG.swf` and the verified InuYasha baseline files by SHA-256. Regenerate the manifest with:

```powershell
python tools/gogeta_inputs.py --manga-rpg "D:\CHAT\manga rpg\RPG.swf"
```

Generated preview sheets stay under `source/gogeta/previews/` and are ignored except for documentation. Final normalized artwork and the extraction manifest are checked in so the shipped build can be reproduced without editor state.
