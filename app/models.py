from sqlalchemy import Column, Integer, String
from app.database import Base


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