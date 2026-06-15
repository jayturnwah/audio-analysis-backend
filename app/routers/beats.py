import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.services.audio_analysis import analyze_single_file
from app.database import get_db
from app.models import Beat, AccessRequest, Release
from app.schemas import BeatCreate, BeatResponse

import os
#import stripe
from fastapi import HTTPException
from pydantic import BaseModel
#from dotenv import load_dotenv
from fastapi.responses import JSONResponse, RedirectResponse



#load_dotenv()

#stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

templates = Jinja2Templates(directory="templates")

class AccessRequestCreate(BaseModel):
    name: str
    email: str
    artist_name: str | None = None
    spotify_link: str | None = None
    instagram_link: str | None = None
    message: str | None = None

class ReleaseCreate(BaseModel):
    artist_name: str
    email: str
    beat_title: str
    song_title: str
    spotify_link: str
    apple_music_link: str | None = None
    youtube_link: str | None = None
    release_date: str | None = None
    notes: str | None = None


def attach_preview_url(beat: Beat):
    if beat.file_path.startswith("/Users/justinternois/Desktop/instrumentals"):
        relative_path = beat.file_path.replace("/Users/justinternois/Desktop/instrumentals/", "", 1)
        beat.preview_url = f"/instrumentals/{relative_path}"
    else:
        beat.preview_url = f"/uploads/{beat.file_name}"
    
    return beat

router = APIRouter()

@router.get("/beats", response_model=list[BeatResponse])
def get_beats(
    genre: str | None = None,
    mood: str | None = None,
    musical_key: str | None = None,
    source_folder: str | None = None,
    mood_tag: str | None = None,
    artist_ref: str | None = None,
    sync_target: str | None = None,
    min_bpm: int | None = None,
    max_bpm: int | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Beat)

    if genre:
        query = query.filter(Beat.genre == genre)
    
    if mood:
        query = query.filter(Beat.mood == mood)

    if musical_key:
        query = query.filter(Beat.musical_key == musical_key)
    
    if source_folder:
        query = query.filter(Beat.source_folder == source_folder)
    
    if mood_tag:
        query = query.filter(Beat.mood_tags.ilike(f"%{mood_tag}%"))
    
    if artist_ref:
        query = query.filter(Beat.artist_reference_tags.ilike(f"%{artist_ref}%"))

    if sync_target:
        query = query.filter(Beat.sync_target_tags.ilike(f"%{sync_target}%"))    
    
    if min_bpm is not None:
        query = query.filter(Beat.bpm >= min_bpm)
    
    if max_bpm is not None:
        query = query.filter(Beat.bpm <= max_bpm)

    beats = query.all()
    return [attach_preview_url(beat) for beat in beats]

@router.post("/beats", response_model=BeatResponse)
def create_beat(beat: BeatCreate, db: Session = Depends(get_db)):
    new_beat = Beat(
        title=beat.title,
        bpm=beat.bpm,
        musical_key=beat.musical_key,
        genre=beat.genre,
        mood=beat.mood,
        energy=beat.energy,
        duration_seconds=beat.duration_seconds,
        file_name=beat.file_name,
        file_path=beat.file_path,
        source_folder=beat.source_folder,
        is_public=beat.is_public,
        notes=beat.notes
    )

    db.add(new_beat)
    db.commit()
    db.refresh(new_beat)

    return new_beat

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/analyze", response_model=BeatResponse)
def analyze_beat(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    if not file.filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only .wav files are supported right now")

    saved_path = UPLOAD_DIR / file.filename

    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    existing_beat = db.query(Beat).filter(
        Beat.file_name == file.filename,
        Beat.source_folder == "uploads"
    ).first()

    if existing_beat:
        raise HTTPException(status_code=400, detail="This uploaded beat already exists in the database")

    analysis = analyze_single_file(str(saved_path), source_folder="uploads")

    new_beat = Beat(**analysis)

    db.add(new_beat)
    db.commit()
    db.refresh(new_beat)

    return new_beat

@router.get("/marketplace/beats", response_model=list[BeatResponse])
def get_marketplace_beats(
    mood_tag: str | None = None,
    artist_ref: str | None = None,
    sync_target: str | None = None,
    min_bpm: int | None = None,
    max_bpm: int | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Beat).filter(Beat.is_public == 1)

    if mood_tag:
        query = query.filter(Beat.mood_tags.ilike(f"%{mood_tag}%"))

    if artist_ref:
        query = query.filter(Beat.artist_reference_tags.ilike(f"%{artist_ref}%"))

    if sync_target:
        query = query.filter(Beat.sync_target_tags.ilike(f"%{sync_target}%"))

    if min_bpm is not None:
        query = query.filter(Beat.bpm >= min_bpm)

    if max_bpm is not None:
        query = query.filter(Beat.bpm <= max_bpm)

    beats = query.all()
    return [attach_preview_url(beat) for beat in beats]

@router.patch("/beats/{beat_id}/publish", response_model=BeatResponse)
def publish_beat(beat_id: int, db: Session = Depends(get_db)):
    beat = db.query(Beat).filter(Beat.id == beat_id).first()

    if not beat:
        raise HTTPException(status_code=404, detail="Beat not found")
    
    beat.is_public = 1

    db.commit()
    db.refresh(beat)

    return beat

@router.patch("/beats/{beat_id}/unpublish", response_model=BeatResponse)
def unpublish_beat(beat_id: int, db: Session = Depends(get_db)):
    beat = db.query(Beat).filter(Beat.id == beat_id).first()

    if not beat:
        raise HTTPException(status_code=404, deatail="Beat not found")
    
    beat.is_pulic = 0

    db.commit()
    db.refresh(beat)

    return beat 

@router.get("/marketplace")
def marketplace_page(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    search: str | None = None,
    energy: str | None = None,
    bpm_range: str | None = None,
    vibe: str | None = None,
    sort: str | None = None,
    mood_tag: str | None = None,
    artist_ref: str | None = None,
    sync_target: str | None = None
):
    featured_beats = db.query(Beat)\
        .filter(Beat.is_public == 1, Beat.is_featured == 1)\
        .order_by(Beat.id.desc())\
        .limit(6)\
        .all()
    
    featured_beats = [attach_preview_url(b) for b in featured_beats]
    featured_ids = [beat.id for beat in featured_beats]
    
    query = db.query(Beat).filter(Beat.is_public == 1)
    
    if featured_ids:
        query = query.filter(~Beat.id.in_(featured_ids))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Beat.title.ilike(search_term)) |
            (Beat.mood_tags.ilike(search_term)) |
            (Beat.artist_reference_tags.ilike(search_term)) |
            (Beat.sync_target_tags.ilike(search_term))
        )

    if energy and energy != "All Energy":
        query = query.filter(Beat.energy_label.ilike(energy))

    if vibe and vibe != "All Vibes":
        query = query.filter(Beat.mood_tags.ilike(f"%{vibe}%"))

    if bpm_range and bpm_range != "All BPM":
        if bpm_range == "90-110":
            query = query.filter(Beat.bpm >= 90, Beat.bpm <= 110)
        elif bpm_range == "111-130":
            query = query.filter(Beat.bpm >= 111, Beat.bpm <= 130)
        elif bpm_range == "131-150":
            query = query.filter(Beat.bpm >= 131, Beat.bpm <= 150)
        elif bpm_range == "151+":
            query = query.filter(Beat.bpm >= 151)
    
    if sync_target:
        query = query.filter(Beat.sync_target_tags.ilike(f"%{sync_target}%"))

    # SORTING
    if sort == "newest":
        query = query.order_by(Beat.id.desc())
    elif sort == "oldest":
        query = query.order_by(Beat.id.asc())
    elif sort == "bpm_high":
        query = query.order_by(Beat.bpm.desc())
    elif sort == "bpm_low":
        query = query.order_by(Beat.bpm.asc())
    elif sort == "energy_high":
        query = query.order_by(Beat.energy.desc())
    else:
        query = query.order_by(Beat.id.desc())

    if mood_tag:
        query = query.filter(Beat.mood_tags.ilike(f"%{mood_tag}%"))

    if artist_ref:
        query = query.filter(Beat.artist_reference_tags.ilike(f"%{artist_ref}%"))

    page_size = 10
    offset = (page - 1) * page_size

    total_beats = query.count()
    total_pages = max(1, (total_beats + page_size - 1) // page_size)

    beats = query.offset(offset).limit(page_size).all()
    beats = [attach_preview_url(beat) for beat in beats]

    return templates.TemplateResponse(
        "marketplace.html",
        {
            "request": request,
            "beats": beats,
            "featured_beats": featured_beats,
            "page": page,
            "search": search or "",
            "energy": energy or "All Energy",
            "bpm_range": bpm_range or "All BPM",
            "vibe": vibe or "All Vibes",
            "sort": sort or "newest",
            "mood_tag": mood_tag or "",
            "artist_ref": artist_ref or "",
            "sync_target": sync_target or "",
            "total_pages": total_pages,
        }
    )

@router.post("/access-request")
def create_access_request(
    payload: AccessRequestCreate,
    db: Session = Depends(get_db)
):
    new_request = AccessRequest(
        name=payload.name,
        email=payload.email,
        artist_name=payload.artist_name,
        spotify_link=payload.spotify_link,
        instagram_link=payload.instagram_link,
        message=payload.message,
        status="pending"
    )

    db.add(new_request)
    db.commit()

    return JSONResponse(
        content={
            "status": "success",
            "message": "Access request received",
            "id": int(new_request.id)
        }
    )

class CheckoutRequest(BaseModel):
    tier: str

#@router.post("/create-checkout-session")
"""def create_checkout_session(payload: CheckoutRequest):
    print("PAYLOAD TIER:", payload.tier)
    price_map = {
    "creator": os.getenv("STRIPE_CREATOR_PRICE_ID"),
    "pro": os.getenv("STRIPE_PRO_PRICE_ID"),
    "black_archive": os.getenv("STRIPE_BLACK_ARCHIVE_PRICE_ID"),
    }

    price_id = price_map.get(payload.tier)

    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")
    
    try:
        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            success_url="http://127.0.0.1:8000/marketplace?checkout=success",
            cancel_url="http://127.0.0.1:8000/marketplace?checkout=cancelled",
        )

        return {"url": checkout_session.url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))"""

@router.patch("/beats/publish-all")
def publish_all_beats(db: Session = Depends(get_db)):
    updated = db.query(Beat).update({Beat.is_public: 1})
    db.commit()
    return {"message": "All beats published", "count": updated}

@router.patch("/beats/{beat_id}/feature", response_model=BeatResponse)
def feature_beat(beat_id: int, db: Session = Depends(get_db)):
    beat = db.query(Beat).filter(Beat.id == beat_id).first()

    if not beat:
        raise HTTPException(status_code=404, detail="Beat not found")
    
    beat.is_featured = 1

    db.commit()
    db.refresh(beat)

    return beat

@router.patch("/beats/{beat_id}/unfeature", response_model=BeatResponse)
def unfeature_beat(beat_id: int, db: Session = Depends(get_db)):
    beat = db.query(Beat).filter(Beat.id == beat_id).first()

    if not beat:
        raise HTTPException(status_code=404, detail="Beat not found")
    
    beat.is_featured = 0

    db.commit()
    db.refresh(beat)

    return beat

@router.get("/admin/access-requests")
def access_requests_page(
    request: Request,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(AccessRequest)

    if status and status != "all":
        query = query.filter(AccessRequest.status == status)

    requests = query.order_by(AccessRequest.created_at.desc()).all()

    return templates.TemplateResponse(
        "access_requests.html",
        {
            "request": request,
            "requests": requests,
            "status": status or "all"
        }
    )

@router.post("/admin/access-requests/{request_id}/approve")
def approve_access_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    access_request = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()

    if not access_request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    access_request.status = "approved"
    db.commit()

    return RedirectResponse(
        url="/admin/access-requests",
        status_code=303
    )

@router.post("/admin/access-requests/{request_id}/reject")
def reject_access_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    access_request = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()

    if not access_request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    access_request.status = "rejected"
    db.commit()

    return RedirectResponse(
        url="/admin/access-requests",
        status_code=303
    )

@router.post("/admin/access-requests/{request_id}/delete")
def delete_access_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    access_request = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()

    if not access_request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    db.delete(access_request)
    db.commit()

    return RedirectResponse(
        url="/admin/access-requests",
        status_code=303
    )

@router.post("/release-report")
def create_release_report(
    payload: ReleaseCreate,
    db: Session = Depends(get_db)
):
    new_release = Release(
        artist_name=payload.artist_name,
        email=payload.email,
        beat_title=payload.beat_title,
        song_title=payload.song_title,
        spotify_link=payload.spotify_link,
        apple_music_link=payload.apple_music_link,
        youtube_link=payload.youtube_link,
        release_date=payload.release_date,
        notes=payload.notes
    )

    db.add(new_release)
    db.commit()

    return {
        "status": "success",
        "message": "Release report received"
    }
    
@router.get("/admin/releases")
def releases_page(
    request: Request,
    db: Session = Depends(get_db)
):
    releases = db.query(Release)\
    .order_by(Release.created_at.desc())\
    .all()

    return templates.TemplateResponse(
        "releases.html",
        {
            "request": request,
            "releases": releases
        }
    )

@router.get("/release-report-form")
def release_report_form(
    request: Request
):
    return templates.TemplateResponse(
        "release_report_form.html",
        {
            "request": request
        }
    )

@router.post("/admin/access-requests/{request_id}/notes")
def save_access_request_notes(
    request_id: int,
    notes: str = Form(...),
    db: Session = Depends(get_db)
):
    access_request = (
        db.query(AccessRequest)
        .filter(AccessRequest.id == request_id)
        .first()
    )

    if not access_request:
        raise HTTPException(
            status_code=404,
            detail="Access request not found"
        )

    access_request.notes = notes

    db.commit()

    return RedirectResponse(
        url="/admin/access-requests",
        status_code=303
    )