# Game music

The included MP3 files are selected as follows:

- `Soviet March.mp3`: title-screen music, looped.
- `1_(beginning).mp3`: match opening, looped until combat starts.
- `Combat_2_(triumphal).mp3`: combat music when the player's unit score is higher, played once.
- `Combat_1_(Losing).mp3`: combat music when the player's unit score is lower, played once.
- `Combat_3_(triumphal).mp3`: played once after Combat 2 if the player's score is still higher.
- `ExploringinHavana(balance).mp3`: looped after five seconds of silence if Combat 2 finishes without an advantage, or after Combat 3 finishes.

A shot during the five-second wait or Balance cancels that state and triggers a new score comparison. Battle tracks are not interrupted by new shots. After Combat 1, or if scores are tied when a shot occurs, the game stays silent until another shot. Adjust the base filenames, volume, fade-in or wait in `config.py`. OGG and WAV files with the configured base names are also accepted. The previous `bgm1`, `bgm2`, and `bgm3` names remain supported as fallbacks.
