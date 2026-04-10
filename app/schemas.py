from pydantic import BaseModel


class BeatCreate(BaseModel):
    title: str
    bpm: int
    musical_key: str
    genre: str
    mood: str
    energy: int
    duration_seconds: int
    file_name: str
    file_path: str
    source_folder: str

    energy_label: str | None = None
    mood_tags: str | None = None
    genre_tags: str | None = None
    artist_reference_tags: str | None = None
    sync_target_tags: str | None = None

    is_public: int = 0
    is_featured: int = 0

    notes: str | None = None


class BeatResponse(BaseModel):
    id: int
    title: str
    bpm: int
    musical_key: str
    genre: str
    mood: str
    energy: int
    duration_seconds: int
    file_name: str
    file_path: str
    source_folder: str

    energy_label: str | None = None
    mood_tags: str | None = None
    genre_tags: str | None = None
    artist_reference_tags: str | None = None
    sync_target_tags: str | None = None

    is_public: int = 0
    is_featured: int = 0
    preview_url: str | None = None

    notes: str | None = None

    class Config:
        from_attributes = True