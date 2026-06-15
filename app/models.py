from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base
from datetime import datetime

class Beat(Base):
    __tablename__ = "beats"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    source_folder = Column(String, nullable=False)

    bpm = Column(Integer, nullable=False)
    musical_key = Column(String, nullable=False)
    duration_seconds = Column(Integer, nullable=False)

    genre = Column(String, nullable=False)
    mood = Column(String, nullable=False)

    energy = Column(Integer, nullable=False)

    # --- analyzer outputs ---
    energy_label = Column(String, nullable=True)
    mood_tags = Column(String, nullable=True)
    ai_tags = Column(String, nullable=True)
    genre_tags = Column(String, nullable=True)
    artist_reference_tags = Column(String, nullable=True)
    sync_target_tags = Column(String, nullable=True)

    is_public = Column(Integer, default=0, nullable=False)
    is_featured = Column(Integer, default=0, nullable=False)

    notes = Column(String, nullable=True)
    hook_start_seconds = Column(Integer, default=30)

class AccessRequest(Base):
    __tablename__ = 'access_requests'

    id = Column(Integer, primary_key =True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    artist_name = Column(String, nullable=True)
    spotify_link = Column(String, nullable=True)
    instagram_link = Column(String, nullable=True)

    message = Column(Text, nullable=True)
    
    status = Column(String, default='pending')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Release(Base):
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, index=True)

    artist_name = Column(String, nullable=False)
    email = Column(String, nullable=False)

    beat_title = Column(String, nullable=False)

    song_title = Column(String, nullable=False)

    spotify_link = Column(String, nullable=True)
    apple_music_link = Column(String, nullable=True)
    youtube_link = Column(String, nullable=True)

    release_date = Column(String, nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    
    
    