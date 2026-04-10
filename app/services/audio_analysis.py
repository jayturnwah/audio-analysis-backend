from pathlib import Path
import re

import numpy as np
import librosa
from mutagen import File as MutagenFile


def clean_title(filename: str) -> str:
    return Path(filename).stem.replace("_", " ").replace("-", " ").strip()


def get_duration_seconds(file_path: str):
    try:
        audio = MutagenFile(file_path)
        if audio is not None and audio.info is not None:
            return int(audio.info.length)
    except Exception as e:
        print(f"Duration error for {file_path}: {e}")
    return 0


def estimate_bpm(file_path: str):
    try:
        y, sr = librosa.load(file_path, sr=None, mono=True)

        if y is None or len(y) == 0:
            return None

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        tempo_array = np.atleast_1d(tempo)

        if tempo_array.size == 0:
            return None

        bpm = float(tempo_array[0])

        if bpm <= 0:
            return None

        return int(round(bpm))

    except Exception as e:
        print(f"BPM error for {file_path}: {e}")
        return None


def extract_bpm_from_filename(filename: str):
    matches = re.findall(r"\b(\d{2,3})\b", filename)
    candidates = [int(m) for m in matches if 60 <= int(m) <= 220]
    if candidates:
        return candidates[-1]
    return None


def extract_key_from_filename(filename: str):
    lowered = Path(filename).stem.lower()

    key_patterns = [
        "a flat minor", "a flat major",
        "b flat minor", "b flat major",
        "c flat minor", "c flat major",
        "d flat minor", "d flat major",
        "e flat minor", "e flat major",
        "f flat minor", "f flat major",
        "g flat minor", "g flat major",
        "a minor", "a major",
        "b minor", "b major",
        "c minor", "c major",
        "d minor", "d major",
        "e minor", "e major",
        "f minor", "f major",
        "g minor", "g major",
    ]

    for pattern in sorted(key_patterns, key=len, reverse=True):
        if pattern in lowered:
            return pattern.title()

    return "Unknown"


def infer_genre_from_folder(folder_name: str):
    lowered = folder_name.lower()

    if "pop" in lowered:
        return "Pop"
    if "trap" in lowered:
        return "Trap"
    if "drake" in lowered:
            return "Trap"
    if "future" in lowered:
        return "Trap"
    if "gucci" in lowered:
        return "Trap"

    return "Unknown"


def analyze_energy(file_path: str):
    try:
        y, sr = librosa.load(file_path, sr=None, mono=True)

        if y is None or len(y) == 0:
            return 0, "low"

        rms = librosa.feature.rms(y=y)[0]
        rms_mean = float(np.mean(rms))

        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid_mean = float(np.mean(spectral_centroid))

        rms_score = min(rms_mean * 100, 10)
        centroid_score = min(centroid_mean / 500, 10)

        raw_score = (rms_score * 0.7) + (centroid_score * 0.3)
        energy_score = max(0, min(int(round(raw_score)), 10))

        if energy_score <= 3:
            energy_label = "low"
        elif energy_score <= 6:
            energy_label = "medium"
        else:
            energy_label = "high"

        return energy_score, energy_label

    except Exception as e:
        print(f"Energy error for {file_path}: {e}")
        return 0, "low"


def generate_mood_tags(musical_key: str, energy: int, energy_label: str, bpm: int, genre: str):
    tags = []

    key_lower = musical_key.lower()
    genre_lower = genre.lower()

    is_minor = "minor" in key_lower
    is_major = "major" in key_lower

    if is_minor:
        tags.append("dark")
    elif is_major:
        tags.append("bright")
    else:
        tags.append("neutral")

    if energy_label == "high":
        tags.append("intense")
    elif energy_label == "medium":
        tags.append("steady")
    else:
        tags.append("calm")

    if bpm >= 140:
        tags.append("driving")
    elif bpm >= 110:
        tags.append("grooving")
    else:
        tags.append("slow")

    if genre_lower == "trap":
        if is_minor and energy >= 7:
            tags.extend(["aggressive", "tense", "confident"])
        elif is_minor:
            tags.extend(["moody", "gritty"])
        else:
            tags.extend(["bouncy", "swagger"])
    elif genre_lower == "pop":
        if is_major and energy >= 5:
            tags.extend(["uplifting", "commercial", "catchy"])
        elif energy <= 3:
            tags.extend(["warm", "reflective"])
        else:
            tags.extend(["melodic", "polished"])
    else:
        if is_minor and energy >= 7:
            tags.extend(["cinematic", "urgent"])
        elif is_major:
            tags.extend(["open", "hopeful"])

    unique_tags = []
    for tag in tags:
        if tag not in unique_tags:
            unique_tags.append(tag)

    return ", ".join(unique_tags)


def generate_artist_reference_tags(
    musical_key: str,
    energy: int,
    energy_label: str,
    bpm: int,
    genre: str,
    mood_tags: str
):
    tags = []

    key_lower = musical_key.lower()
    genre_lower = genre.lower()
    mood_lower = mood_tags.lower()

    is_minor = "minor" in key_lower
    is_major = "major" in key_lower

    if genre_lower == "trap":
        if is_minor and energy_label == "high" and bpm >= 140:
            tags.extend(["Future", "Travis Scott", "Southside"])
        elif is_minor and bpm >= 125:
            tags.extend(["Drake", "Future"])
        elif "moody" in mood_lower:
            tags.extend(["Drake", "NAV"])
        elif "swagger" in mood_lower:
            tags.extend(["2 Chainz", "Young Dolph"])

    elif genre_lower == "pop":
        if is_major and energy >= 5:
            tags.extend(["Justin Timberlake", "Dua Lipa", "The Weeknd"])
        elif "warm" in mood_lower or "reflective" in mood_lower:
            tags.extend(["The Weeknd", "Post Malone"])
        else:
            tags.extend(["Justin Timberlake", "The Weeknd"])

    else:
        if is_minor and energy_label == "high":
            tags.extend(["Travis Scott", "The Weeknd"])
        elif is_major:
            tags.extend(["Justin Timberlake"])

    unique_tags = []
    for tag in tags:
        if tag not in unique_tags:
            unique_tags.append(tag)

    return ", ".join(unique_tags)


def generate_sync_target_tags(
    musical_key: str,
    energy: int,
    energy_label: str,
    bpm: int,
    genre: str,
    mood_tags: str,
    artist_reference_tags: str
):
    tags = []

    key_lower = musical_key.lower()
    genre_lower = genre.lower()
    mood_lower = mood_tags.lower()
    artist_lower = artist_reference_tags.lower()

    is_minor = "minor" in key_lower
    is_major = "major" in key_lower

    if genre_lower == "trap":
        if is_minor and energy_label == "high" and bpm >= 140:
            tags.extend(["sports promo", "fight content", "streetwear ad"])
        elif is_minor and "moody" in mood_lower:
            tags.extend(["luxury nightlife", "urban drama", "fashion ad"])
        elif "swagger" in mood_lower:
            tags.extend(["automotive ad", "streetwear ad"])

    if genre_lower == "pop":
        if is_major and energy >= 5:
            tags.extend(["commercial ad", "fashion ad", "lifestyle brand"])
        elif "warm" in mood_lower or "reflective" in mood_lower:
            tags.extend(["coming-of-age", "romantic scene", "brand story"])

    if "travis scott" in artist_lower or "future" in artist_lower:
        tags.extend(["sports promo", "trailer", "streetwear ad"])

    if "drake" in artist_lower or "nav" in artist_lower:
        tags.extend(["luxury nightlife", "urban drama", "fashion ad"])

    if "the weeknd" in artist_lower:
        tags.extend(["luxury brand", "nightlife campaign", "fashion ad"])

    if is_minor and energy >= 7:
        tags.extend(["trailer", "dramatic scene"])

    if is_major and energy_label == "high":
        tags.extend(["uplifting commercial", "fitness brand", "lifestyle brand"])

    unique_tags = []
    for tag in tags:
        if tag not in unique_tags:
            unique_tags.append(tag)

    return ", ".join(unique_tags)

def analyze_single_file(file_path: str, source_folder: str = "uploads"):
    file_name = Path(file_path).name
    title = clean_title(file_name)

    filename_bpm = extract_bpm_from_filename(file_name)
    detected_bpm = estimate_bpm(file_path)
    final_bpm = filename_bpm if filename_bpm is not None else (detected_bpm or 0)

    musical_key = extract_key_from_filename(file_name)
    genre = infer_genre_from_folder(source_folder)
    duration_seconds = get_duration_seconds(file_path)
    energy_score, energy_label = analyze_energy(file_path)

    mood_tags = generate_mood_tags(
        musical_key=musical_key,
        energy=energy_score,
        energy_label=energy_label,
        bpm=final_bpm,
        genre=genre
    )

    artist_reference_tags = generate_artist_reference_tags(
        musical_key=musical_key,
        energy=energy_score,
        energy_label=energy_label,
        bpm=final_bpm,
        genre=genre,
        mood_tags=mood_tags
    )

    sync_target_tags = generate_sync_target_tags(
        musical_key=musical_key,
        energy=energy_score,
        energy_label=energy_label,
        bpm=final_bpm,
        genre=genre,
        mood_tags=mood_tags,
        artist_reference_tags=artist_reference_tags
    )

    return {
        "title": title,
        "file_name": file_name,
        "file_path": file_path,
        "source_folder": source_folder,
        "bpm": final_bpm,
        "musical_key": musical_key,
        "genre": genre,
        "mood": "Unknown",
        "energy": energy_score,
        "duration_seconds": duration_seconds,
        "energy_label": energy_label,
        "mood_tags": mood_tags,
        "genre_tags": genre,
        "artist_reference_tags": artist_reference_tags,
        "sync_target_tags": sync_target_tags,
        "notes": None,
    }