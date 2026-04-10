from pathlib import Path
import re

import numpy as np
import librosa
from mutagen import File as MutagenFile

from app.database import SessionLocal
from app.models import Beat
from transformers import pipeline

import random

BEATS_FOLDER = "/Users/justinternois/Desktop/instrumentals"

semantic_audio_tagger = pipeline(
    task="zero-shot-audio-classification",
    model="laion/clap-htsat-unfused"
)

def generate_ai_semantic_tags(file_path: str, bpm: int, energy_label: str):

    import random

    # ---------- MOOD LABELS ----------
    if bpm >= 145 and energy_label == "high":
        mood_labels = [
        "aggressive", "explosive", "turnt", "menacing", "street",
        "high energy", "bossed up", "urgent", "dark", "gritty"
    ]
    elif bpm >= 120 and energy_label in ["medium", "high"]:
        mood_labels = [
        "late night", "luxury", "cinematic", "moody", "wavy",
        "dark", "player", "dramatic", "smooth", "street"
    ]
    elif energy_label == "low":
        mood_labels = [
        "melancholic", "nostalgic", "introspective", "soulful", "dreamy",
        "ambient", "heartfelt", "smooth", "laid back", "emotional"
    ]
    else:
        mood_labels = [
        "cinematic", "dramatic", "gritty", "dark", "late night",
        "emotional", "smooth", "wavy", "luxury", "intense"
    ]
    # ---------- ARTIST LABELS ----------
    if bpm >= 145 and energy_label == "high":
        artist_labels = [
        "rage lane",
        "street anthem lane",
        "dark street rap lane",
        "aggressive trap lane",
        "hype anthem lane",
        "club trap lane",
        "cinematic trap lane"
    ]
    elif bpm >= 120 and energy_label in ["medium", "high"]:
        artist_labels = [
        "luxury rap lane",
        "melodic trap lane",
        "late night introspective lane",
        "southern trap lane",
        "dark street rap lane",
        "club trap lane",
        "pop rap lane"
    ]
    elif energy_label == "low":
        artist_labels = [
        "pain rap lane",
        "emotional rap lane",
        "late night introspective lane",
        "melodic trap lane",
        "pop rap lane",
        "experimental rap lane"
    ]
    else:
        artist_labels = [
        "southern trap lane",
        "melodic trap lane",
        "dark street rap lane",
        "luxury rap lane",
        "cinematic trap lane",
        "emotional rap lane"
    ]

    # ---------- RUN AI (MOOD) ----------
    mood_results = semantic_audio_tagger(
        file_path,
        candidate_labels=mood_labels
    )

    primary_mood = mood_results[0]["label"]
    secondary_moods = [item["label"] for item in mood_results[1:3]]
    mood_tags = [primary_mood] + secondary_moods


    # ---------- RUN AI (ARTIST) ----------
    artist_results = semantic_audio_tagger(
        file_path,
        candidate_labels=artist_labels
    )

    filtered_artists = []

    for item in artist_results:
        if item["score"] > 0.25:
            filtered_artists.append(item["label"])

    # prevent same artists every time
    random.shuffle(filtered_artists)

    artist_tags = filtered_artists[:2]

    return {
        "mood_tags": ", ".join(mood_tags),
        "artist_reference_tags": ", ".join(artist_tags)
    }

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


def import_beats():
    db = SessionLocal()

    try:
        wav_files = [p for p in Path(BEATS_FOLDER).rglob("*") if p.is_file() and p.suffix.lower() == ".wav"]
        print(f"Found {len(wav_files)} wav files\n")

        added_count = 0
        skipped_count = 0

        for file_path in wav_files:
            file_name = file_path.name
            source_folder = file_path.parent.name

            existing_beat = db.query(Beat).filter(
                Beat.file_name == file_name,
                Beat.source_folder == source_folder
            ).first()

            if existing_beat:
                skipped_count += 1
                print(f"Skipping duplicate: {source_folder}/{file_name}")
                continue

            title = clean_title(file_name)
            filename_bpm = extract_bpm_from_filename(file_name)
            detected_bpm = estimate_bpm(str(file_path))
            final_bpm = filename_bpm if filename_bpm is not None else (detected_bpm or 0)

            musical_key = extract_key_from_filename(file_name)
            genre = infer_genre_from_folder(source_folder)
            duration_seconds = get_duration_seconds(str(file_path))
            energy_score, energy_label = analyze_energy(str(file_path))
            ai_tags = generate_ai_semantic_tags(str(file_path), final_bpm, energy_label)
            ai_mood_tags = ai_tags["mood_tags"]
            ai_artist_tags = ai_tags["artist_reference_tags"]

            mood_tags = generate_mood_tags(
            musical_key=musical_key,
            energy=energy_score,
            energy_label=energy_label,
            bpm=final_bpm,
            genre=genre
            )

            rule_tag_list = [tag.strip() for tag in mood_tags.split(",") if tag.strip()]
            ai_tag_list = [tag.strip() for tag in ai_mood_tags.split(",") if tag.strip()]

            combined_mood_tags = []
            for tag in rule_tag_list + ai_tag_list:
                if tag not in combined_mood_tags:
                    combined_mood_tags.append(tag)

            mood_tags = ", ".join(combined_mood_tags)

            artist_reference_tags = ai_artist_tags

            

            sync_target_tags = generate_sync_target_tags(
            musical_key=musical_key,
            energy=energy_score,
            energy_label=energy_label,
            bpm=final_bpm,
            genre=genre,
            mood_tags=mood_tags,
            artist_reference_tags=artist_reference_tags
            )

            new_beat = Beat(
                title=title,
                bpm=final_bpm,
                musical_key=musical_key,
                genre=genre,
                mood="Unknown",
                energy=energy_score,
                duration_seconds=duration_seconds,
                file_name=file_name,
                file_path=str(file_path),
                source_folder=source_folder,
                energy_label=energy_label,
                mood_tags=mood_tags,
                genre_tags=None,
                artist_reference_tags=artist_reference_tags,
                sync_target_tags=sync_target_tags,
                is_public=0,
                ai_tags=ai_mood_tags,
                notes=None
            )

            db.add(new_beat)
            added_count += 1

            print(
            f"Added: {file_name} | bpm={final_bpm} | key={musical_key} | "
            f"genre={genre} | energy={energy_score} ({energy_label}) | "
            f"mood_tags={mood_tags} | artist_refs={artist_reference_tags} | "
            f"sync_targets={sync_target_tags} | is_public=0 | duration={duration_seconds}"
            )

        db.commit()
        print(f"\nImport complete. Added {added_count}, skipped {skipped_count}.")

    except Exception as e:
        db.rollback()
        print(f"IMPORT ERROR: {e}")

    finally:
        db.close()

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
        ai_lower = mood_tags.lower()

        key_lower = musical_key.lower()
        genre_lower = genre.lower()
        mood_lower = mood_tags.lower()

        is_minor = "minor" in key_lower
        is_major = "major" in key_lower

        if "dark trap" in ai_lower or "aggressive" in ai_lower:
            tags.extend(["Future", "Travis Scott", "Young Thug"])
        if "melancholic" in ai_lower or "emotional" in ai_lower:
            tags.extend(["Drake", "Rod Wave", "The Weeknd"])
        if "uplifting" in ai_lower or "triumphant" in ai_lower:
            tags.extend(["Kanye West", "Travis Scott"])
        if "gritty" in ai_lower:
            tags.extend(["21 Savage", "Key Glock"])
        if "cinematic" in ai_lower:
            tags.extend(["Metro Boomin", "Hans Zimmer"])

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

    if bpm >= 145 and energy_label == "high":
        tags.extend([
        "sports promo",
        "fight content",
        "streetwear ad",
        "trailer",
        "gaming montage"
    ])

    elif bpm >= 120 and energy_label in ["medium", "high"]:
        tags.extend([
        "luxury nightlife",
        "fashion ad",
        "automotive ad",
        "urban drama",
        "late night campaign"
    ])

    elif energy_label == "low":
        tags.extend([
        "emotional scene",
        "brand story",
        "coming-of-age scene",
        "romantic scene",
        "reflective montage"
    ])

    else:
        tags.extend([
        "cinematic scene",
        "fashion ad",
        "urban drama",
        "lifestyle brand"
    ])

    if genre_lower == "pop" and is_major:
        tags.extend(["commercial ad", "lifestyle brand"])

    if is_minor and "cinematic" in mood_lower:
        tags.extend(["trailer", "dramatic scene"])

    if "luxury" in mood_lower or "late night" in mood_lower:
        tags.extend(["luxury nightlife", "fashion ad"])

    if "street" in mood_lower or "aggressive" in mood_lower:
        tags.extend(["streetwear ad", "fight content"])
    
    unique_tags = []
    for tag in tags:
        if tag not in unique_tags:
            unique_tags.append(tag)

    return ", ".join(unique_tags)

if __name__ == "__main__":
    import_beats()