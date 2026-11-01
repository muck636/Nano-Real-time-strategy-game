"""Select and loop music based on the current combat state."""

import math
from pathlib import Path
import sys
import time

import pygame

import config as C


# Choose opening or battle music based on match state and unit scores.
def track_for_game(game):
    """Choose an opening or score-based track; ties do not select a track."""
    if game is None or game.winner is not None:
        return None
    if game.combat_event_serial == 0:
        return "bgm1"
    player_score = game.unit_battle_score(game.player)
    enemy_score = game.unit_battle_score(game.enemy)
    if math.isclose(player_score, enemy_score, rel_tol=1e-9, abs_tol=1e-9):
        return None
    return "bgm2" if player_score > enemy_score else "bgm3"


class MusicController:
    # Initialize music paths, playback state, and the balance-track timer.
    def __init__(self, music_dir=None, clock=None):
        self.music_dir = Path(music_dir) if music_dir is not None else Path(__file__).resolve().parent / C.MUSIC_DIRECTORY
        self.requested_track = None
        self.playing_track = None
        self._game = None
        self._last_combat_event = 0
        self._clock = time.monotonic if clock is None else clock
        self._balance_at = None

    # Stop and unload the current music when the mixer is available.
    def _stop_playback(self):
        if pygame.mixer.get_init() is not None:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except pygame.error:
                pass
        self.playing_track = None

    # Stop playback and clear the match and pending music state.
    def stop(self):
        self._stop_playback()
        self.requested_track = None
        self._game = None
        self._last_combat_event = 0
        self._balance_at = None

    # Schedule balance music after the configured silent delay.
    def _wait_for_balance(self):
        self._balance_at = self._clock() + C.MUSIC_BALANCE_DELAY

    # Load and play a named track with filename and format fallbacks.
    def _play_track(self, track, loops):
        self.requested_track = track
        if pygame.mixer.get_init() is None:
            self.playing_track = None
            return
        # Prefer the named music, while still accepting the original bgm1/2/3 filenames.
        names = dict.fromkeys((C.MUSIC_TRACK_NAMES.get(track, track), track))
        for name in names:
            for extension in C.MUSIC_EXTENSIONS:
                path = self.music_dir / (name + extension)
                if not path.is_file():
                    continue
                try:
                    pygame.mixer.music.load(str(path))
                    pygame.mixer.music.set_volume(C.MUSIC_VOLUME)
                    pygame.mixer.music.play(loops=loops, fade_ms=C.MUSIC_FADE_IN_MS)
                except (pygame.error, OSError) as exc:
                    self.playing_track = None
                    print(f"Could not play music {path}: {exc}", file=sys.stderr)
                    continue
                self.playing_track = track
                return
        self._stop_playback()

    # Advance menu, battle, follow-up, and balance music transitions.
    def update(self, game):
        if game is None:
            if self._game is not None:
                self.stop()
            if self.requested_track != "menu":
                self._play_track("menu", loops=-1)
            return
        if game is not self._game:
            self.stop()
            self._game = game
            self._play_track("bgm1", loops=-1)

        new_combat = game.combat_event_serial != self._last_combat_event
        self._last_combat_event = game.combat_event_serial
        if self.playing_track in ("bgm2", "bgm3", "combat3"):
            if pygame.mixer.get_init() is not None and pygame.mixer.music.get_busy():
                return
            completed = self.playing_track
            self._stop_playback()
            self.requested_track = None
            if completed == "bgm2":
                player_score = game.unit_battle_score(game.player)
                enemy_score = game.unit_battle_score(game.enemy)
                if player_score > enemy_score:
                    self._play_track("combat3", loops=0)
                    if self.playing_track == "combat3":
                        return
                self._wait_for_balance()
            elif completed == "combat3":
                self._wait_for_balance()

        if new_combat and game.winner is None:
            self._balance_at = None
            if self.playing_track is not None:
                self._stop_playback()
            self.requested_track = None
            requested = track_for_game(game)
            if requested in ("bgm2", "bgm3"):
                self._play_track(requested, loops=0)
            return
        if self._balance_at is not None and self._clock() >= self._balance_at:
            self._balance_at = None
            self._play_track("balance", loops=-1)
