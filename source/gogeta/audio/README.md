# Gogeta original audio mapping

Source: D:/CHAT/manga rpg/RPG.swf (SHA-256 7bb23abfdad7ef49979c8d535926fc0a86ec54b485c2bf9676bc78b9f333c106).
Runtime: D:/CHAT/inuyasha-pvp-gogeta/public/game/characters/go_figure.swf.
Extracted assets: D:/CHAT/inuyasha-pvp-gogeta/source/gogeta/audio/sounds/<ID>.mp3 and <ID>.define-sound.bin.

| Action | Source sprite / label | One-based source frames and sound IDs |
|---|---|---|
| basicPunch | 7034 / 변신5공격1 | 6 -> 2456 |
| kiRelease | 7062 / 변신5스킬z | 3 -> 1927 |
| bigBangKamehameha | 7158 / 변신5스킬e | 2 -> 93, 13 -> 100, 36 -> 3763, 73 -> 93 |
| dragonFist | 7117 / 변신5스킬q | 39 -> 1990 |
| superEnergyBackflow | 7101 / 변신5스킬s | 17 -> 3712 |
| superKamehameha | 7109 / 변신5스킬f | 2 -> 100, 50 -> 1704 |

energyUp, heal and summonShippo use the kiRelease cue at frame 3. Ambient has no repeated attack sound.
The SWF embeds the original MP3 payload, sample count, seek offset and SOUNDINFO rather than re-encoding or substituting effects.
No dedicated character voice linkage was identified. This is not a claim that every source audio clip is speech-free. No unrelated character voice is assigned.
