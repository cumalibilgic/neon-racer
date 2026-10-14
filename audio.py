"""Müzik ve ses efektleri. Platforma özgü ses kodu burada toplanır."""

import os

import pygame

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
EFFECTS = {"lane": 0.35, "boost": 0.6, "crash": 0.8, "start": 0.6}
MUSIC_VOLUME = 0.45


class Audio:
    def __init__(self, muted=False):
        self.muted = muted
        self.music_level = 1.0
        self.sounds = {}
        self.music = None
        self.music_channel = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            for name, volume in EFFECTS.items():
                sound = pygame.mixer.Sound(os.path.join(ASSETS, name + ".ogg"))
                sound.set_volume(volume)
                self.sounds[name] = sound
            self.music = pygame.mixer.Sound(os.path.join(ASSETS, "music.ogg"))
            pygame.mixer.set_reserved(1)
            self.music_channel = pygame.mixer.Channel(0)
        except (pygame.error, FileNotFoundError) as error:
            print("Ses kullanılamıyor:", error)
            self.sounds = {}
            self.music = None

    def start_music(self):
        """Tarayıcılar ilk dokunuştan önce ses çalmaya izin vermez; bu yüzden ilk girişte çağrılır."""
        if self.music and not self.music_channel.get_busy():
            self.music_channel.play(self.music, loops=-1, fade_ms=800)
            self.update_music_volume()

    def set_music_level(self, level):
        self.music_level = level
        self.update_music_volume()

    def update_music_volume(self):
        if self.music_channel:
            self.music_channel.set_volume(0.0 if self.muted else MUSIC_VOLUME * self.music_level)

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            for sound in self.sounds.values():
                sound.stop()
        self.update_music_volume()
        return self.muted

    def play(self, name):
        sound = self.sounds.get(name)
        if sound and not self.muted:
            sound.play()
