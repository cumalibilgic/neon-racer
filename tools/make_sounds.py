"""Neon Racer'ın müziğini ve ses efektlerini üretir, assets/ içine .ogg olarak yazar.

Kullanım:
    pip install numpy soundfile
    python tools/make_sounds.py

Oyunun kendisi numpy kullanmaz; bu script yalnızca sesler değiştiğinde çalıştırılır.
"""

import os

import numpy as np
import soundfile as sf

RATE = 44100
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
rng = np.random.default_rng(7)


def note(name):
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return 440.0 * 2 ** ((names.index(name[:-1]) + 12 * (int(name[-1]) + 1) - 69) / 12)


def tone(freq, duration, harmonics=8, brightness=1.0, detune=0.0, pulse=False):
    """Bant sınırlı testere (veya kare) dalga; brightness yüksek harmonikleri kısar."""
    t = np.arange(int(duration * RATE)) / RATE
    out = np.zeros_like(t)
    for k in range(1, harmonics + 1):
        if pulse and k % 2 == 0:
            continue
        if freq * k > RATE / 2:
            break
        amp = (1 / k) * (1 / (1 + (k / (1 + 6 * brightness)) ** 2))
        out += amp * np.sin(2 * np.pi * freq * k * t + k * 1.3)
        if detune:
            out += amp * np.sin(2 * np.pi * freq * (1 + detune) * k * t)
    return out


def envelope(n, attack, decay, sustain=0.0, release=0.0):
    t = np.arange(n) / RATE
    env = np.where(t < attack, t / max(attack, 1e-6), sustain + (1 - sustain) * np.exp(-(t - attack) / max(decay, 1e-6)))
    if release:
        tail = int(release * RATE)
        env[-tail:] *= np.linspace(1, 0, tail)
    return env


def release(sound, seconds=0.008):
    """Sesin sonunu sıfıra yumuşakça indirir; aniden kesilen ses tık yapar."""
    tail = min(len(sound), int(seconds * RATE))
    sound[-tail:] *= np.linspace(1, 0, tail)
    return sound


def filtered_noise(n, low, high):
    spectrum = np.fft.rfft(rng.uniform(-1, 1, n))
    freqs = np.fft.rfftfreq(n, 1 / RATE)
    spectrum[(freqs < low) | (freqs > high)] = 0
    out = np.fft.irfft(spectrum, n)
    return out / (np.abs(out).max() + 1e-9)


def highpass(sound, cutoff):
    """FFT ile 2. dereceden high-pass (faz kaydırmaz; müzik döngüsel olduğu için başla son da uyumlu kalır)."""
    spectrum = np.fft.rfft(sound)
    freqs = np.fft.rfftfreq(len(sound), 1 / RATE)
    spectrum *= 1 / np.sqrt(1 + (cutoff / np.maximum(freqs, 1e-6)) ** 4)
    return np.fft.irfft(spectrum, len(sound))


def sweep(f0, f1, duration, harmonics=6):
    n = int(duration * RATE)
    freq = np.geomspace(f0, f1, n)
    phase = 2 * np.pi * np.cumsum(freq) / RATE
    return sum(np.sin(k * phase) / k for k in range(1, harmonics + 1))


def add(buffer, sound, start, wrap=True):
    """Sesi buffer'a ekler; wrap açıksa taşan kısım başa sarar (müzik kusursuz döner)."""
    start = int(start) % len(buffer)
    end = start + len(sound)
    if end <= len(buffer):
        buffer[start:end] += sound
    else:
        cut = len(buffer) - start
        buffer[start:] += sound[:cut]
        if wrap:
            buffer[:len(sound) - cut] += sound[cut:]


def normalize(sound, peak=0.9):
    return sound / (np.abs(sound).max() + 1e-9) * peak


def make_music():
    bpm = 104
    beat = 60 / bpm
    step = beat / 4
    progression = [("A", "m"), ("F", ""), ("C", ""), ("G", "")]
    bars_per_chord = 2
    total = int(len(progression) * bars_per_chord * 4 * beat * RATE)
    bass = np.zeros(total)
    arp = np.zeros(total)
    pad = np.zeros(total)
    drums = np.zeros(total)

    kick_n = int(0.35 * RATE)
    kt = np.arange(kick_n) / RATE
    kick = release(np.sin(2 * np.pi * np.cumsum(60 + 110 * np.exp(-kt * 30)) / RATE) * np.exp(-kt * 9))
    snare_n = int(0.45 * RATE)
    snare = release(filtered_noise(snare_n, 900, 9000) * envelope(snare_n, 0.001, 0.12)
                    + 0.5 * np.sin(2 * np.pi * 190 * np.arange(snare_n) / RATE) * envelope(snare_n, 0.001, 0.05))
    hat_n = int(0.06 * RATE)
    hat = filtered_noise(hat_n, 7000, 16000) * envelope(hat_n, 0.001, 0.015, release=0.005)

    for c, (root, quality) in enumerate(progression):
        third = 3 if quality == "m" else 4
        root_f = note(root + "2")
        chord = [root_f * 2 ** (i / 12) for i in (0, third, 7)]
        chord_start = c * bars_per_chord * 4 * beat

        pad_tone = sum(tone(f * 4, bars_per_chord * 4 * beat, 10, 0.3, detune=0.004) for f in chord)
        add(pad, pad_tone * envelope(len(pad_tone), 0.4, 10, 1.0, 0.4), chord_start * RATE)

        for s in range(bars_per_chord * 16):
            pos = (chord_start + s * step) * RATE
            if s % 2 == 0:
                f = root_f * (2 if s % 4 == 2 else 1)
                b = tone(f, step * 1.8, 10, 0.5)
                add(bass, b * envelope(len(b), 0.004, 0.12, 0.3, 0.02), pos)
            arp_notes = [chord[0] * 4, chord[1] * 4, chord[2] * 4, chord[0] * 8]
            a = tone(arp_notes[s % 4], step * 0.9, 9, 0.8, pulse=True)
            add(arp, a * envelope(len(a), 0.003, 0.07, release=0.008), pos)
            if s % 4 == 0:
                add(drums, kick, pos)
            if s % 8 == 4:
                add(drums, snare * 0.7, pos)
            if s % 2 == 1:
                add(drums, hat * 0.35, pos)

    # Arpeje yankı (müzik döngüsel olduğu için kaydırma da döngüsel)
    delay = int(step * 3 * RATE)
    echo = arp.copy()
    for i in range(1, 4):
        echo += np.roll(arp, delay * i) * 0.45 ** i

    # Kick vurduğunda pad ve basın hafifçe kısılması (synthwave "pompalama" hissi)
    duck = np.ones(total)
    duck_n = int(beat * RATE)
    # Ani düşüş tık yapar: 5 ms'lik rampayla 1'den 0.45'e iner, sonra eski eğriyle geri yükselir
    dt = np.arange(duck_n) / RATE
    shape = 1 - 0.55 * np.minimum(1, dt / 0.005) * np.exp(-dt * 9)
    for b in range(int(total / duck_n)):
        duck[b * duck_n:(b + 1) * duck_n] = shape[:len(duck[b * duck_n:(b + 1) * duck_n])]

    # Hoparlörde cızırtı yapmasın diye 70 Hz altı kesilir
    bass = highpass(bass, 70)
    drums = highpass(drums, 70)

    mix = (normalize(bass) * 0.5 * duck + normalize(echo) * 0.3 + normalize(pad) * 0.4 * duck
           + normalize(drums) * 0.4)
    return normalize(np.tanh(mix * 0.6), 0.7)


def make_lane():
    n = int(0.14 * RATE)
    whoosh = filtered_noise(n, 1500, 7000) * envelope(n, 0.02, 0.04, release=0.01)
    chirp = sweep(500, 1100, 0.14, 3) * envelope(n, 0.003, 0.05, release=0.01)
    return normalize(whoosh * 0.5 + chirp * 0.5, 0.6)


def make_boost():
    duration = 0.7
    n = int(duration * RATE)
    rise = sweep(160, 1300, duration, 8) * envelope(n, 0.01, 10, 1.0, 0.25)
    rise2 = sweep(160 * 1.5, 1300 * 1.5, duration, 4) * envelope(n, 0.01, 10, 1.0, 0.25)
    air = filtered_noise(n, 2000, 12000) * np.linspace(0, 1, n) * envelope(n, 0.01, 10, 1.0, 0.25)
    return normalize(rise + rise2 * 0.5 + air * 0.4, 0.75)


def make_crash():
    n = int(1.1 * RATE)
    t = np.arange(n) / RATE
    boom = np.sin(2 * np.pi * np.cumsum(40 + 90 * np.exp(-t * 12)) / RATE) * np.exp(-t * 4)
    smash = filtered_noise(n, 200, 9000) * np.exp(-t * 6)
    metal = sum(np.sin(2 * np.pi * f * t) for f in (1330, 2210, 3170)) * np.exp(-t * 9) / 3
    fade = np.minimum(1, np.linspace(10, 0, n)) * np.minimum(1, t / 0.002)
    return normalize(np.tanh((boom + smash * 0.8 + metal * 0.4) * 1.2) * fade, 0.8)


def make_start():
    out = np.zeros(int(0.75 * RATE))
    for i, name in enumerate(["A4", "C#5", "E5", "A5"]):
        length = 0.4 if i == 3 else 0.12
        s = tone(note(name), length, 8, 1.0, pulse=True)
        add(out, s * envelope(len(s), 0.003, 0.1 if i < 3 else 0.25, release=0.01), i * 0.09 * RATE, wrap=False)
    return normalize(out, 0.7)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sounds = {
        "music": make_music(),
        "lane": make_lane(),
        "boost": make_boost(),
        "crash": make_crash(),
        "start": make_start(),
    }
    for name, data in sounds.items():
        path = os.path.normpath(os.path.join(OUT_DIR, name + ".ogg"))
        # libsndfile büyük Vorbis bloklarını tek seferde yazarken Windows'ta çöküyor; parça parça yaz
        with sf.SoundFile(path, "w", RATE, 1, format="OGG", subtype="VORBIS") as f:
            for i in range(0, len(data), 4096):
                f.write(data[i:i + 4096].astype(np.float32))
        print(f"{path}  {len(data) / RATE:.1f} sn  {os.path.getsize(path) // 1024} KB")


if __name__ == "__main__":
    main()
