# ISSUE-017: Video Validation UI

**Created**: 2026-01-20  
**Priority**: 🔴 P0 (Critical)  
**Phase**: Phase 2 - Creator Studio  
**Estimated**: 6-8 hours  
**Status**: ✅ Complete  
**Depends On**: #016 (Script Review UI)

---

## 🎯 Objective

Build a video validation UI that allows users to review final videos, edit metadata, and approve for YouTube upload. This is the final quality control step before publishing.

---

## 📋 User Story

**As a** video creator  
**I want to** review the final video with all elements before uploading  
**So that** I can ensure quality and make last-minute metadata adjustments

---

## ✅ Acceptance Criteria

### Must Have
- [ ] Display list of videos pending validation
- [ ] Video player with standard controls (play, pause, seek, volume)
- [ ] Display and edit YouTube title
- [ ] Display and edit video description
- [ ] Display and edit hashtags
- [ ] Show thumbnail preview
- [ ] Approve video for upload
- [ ] Reject video (regenerate)
- [ ] Download video file

### Should Have
- [ ] Advanced playback controls (speed, frame-by-frame)
- [ ] Scene markers on timeline
- [ ] Upload checklist (title, description, thumbnail, quality)
- [ ] Video stats (duration, size, resolution)
- [ ] Copy metadata to clipboard
- [ ] Export metadata as JSON

### Nice to Have
- [ ] Side-by-side comparison (multiple versions)
- [ ] Quality analysis (subtitle timing, image quality)
- [ ] Performance predictions (estimated CTR, views)
- [ ] Direct YouTube upload from UI

---

## 🏗️ Technical Implementation

### Database Changes

```sql
-- Add validation fields to videos table
ALTER TABLE videos ADD COLUMN validation_status VARCHAR DEFAULT 'pending'; -- pending, approved, rejected
ALTER TABLE videos ADD COLUMN approved_at TIMESTAMP;
ALTER TABLE videos ADD COLUMN rejection_reason TEXT;
ALTER TABLE videos ADD COLUMN uploaded_to_youtube BOOLEAN DEFAULT FALSE;
ALTER TABLE videos ADD COLUMN youtube_url VARCHAR;
ALTER TABLE videos ADD COLUMN youtube_video_id VARCHAR;

CREATE INDEX idx_videos_validation_status ON videos(validation_status);
```

### Backend API Endpoints

**File**: `backend/app/routers/validation_router.py`

```python
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from app.models import Video, Script
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/validation", tags=["validation"])

@router.get("/videos")
async def list_videos_for_validation(
    status: Optional[str] = "pending",
    db: Session = Depends(get_db)
):
    """List videos for validation."""
    query = db.query(Video)
    
    if status:
        query = query.filter(Video.validation_status == status)
    
    videos = query.order_by(Video.created_at.desc()).all()
    return videos

@router.get("/videos/{id}")
async def get_video_detail(id: int, db: Session = Depends(get_db)):
    """Get complete video details."""
    video = db.query(Video).filter(Video.id == id).first()
    script = db.query(Script).filter(Script.id == video.script_id).first()
    
    return {
        "video": video,
        "script": script,
        "metadata": {
            "title": video.youtube_title or script.catchy_title,
            "description": video.youtube_description or script.video_description,
            "hashtags": script.hashtags,
            "thumbnail_path": video.thumbnail_path
        }
    }

@router.put("/videos/{id}/metadata")
async def update_video_metadata(
    id: int,
    youtube_title: Optional[str] = None,
    youtube_description: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """Update video metadata."""
    video = db.query(Video).filter(Video.id == id).first()
    
    if youtube_title:
        video.youtube_title = youtube_title
    if youtube_description:
        video.youtube_description = youtube_description
    if hashtags:
        script = db.query(Script).filter(Script.id == video.script_id).first()
        script.hashtags = hashtags
    
    db.commit()
    return video

@router.post("/videos/{id}/approve")
async def approve_video(id: int, db: Session = Depends(get_db)):
    """Approve video for upload."""
    video = db.query(Video).filter(Video.id == id).first()
    video.validation_status = "approved"
    video.approved_at = datetime.datetime.now()
    db.commit()
    
    return {"status": "approved", "ready_for_upload": True}

@router.post("/videos/{id}/reject")
async def reject_video(
    id: int,
    reason: str,
    db: Session = Depends(get_db)
):
    """Reject video and mark for regeneration."""
    video = db.query(Video).filter(Video.id == id).first()
    video.validation_status = "rejected"
    video.rejection_reason = reason
    db.commit()
    
    return {"status": "rejected"}

@router.get("/videos/{id}/download")
async def download_video(id: int, db: Session = Depends(get_db)):
    """Stream video file for download."""
    video = db.query(Video).filter(Video.id == id).first()
    
    return FileResponse(
        path=video.file_path,
        media_type="video/mp4",
        filename=f"video_{id}.mp4"
    )
```

### Frontend Components

**File**: `frontend/src/pages/VideoValidation.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import VideoPlayer from '../components/VideoPlayer';
import MetadataEditor from '../components/MetadataEditor';
import UploadChecklist from '../components/UploadChecklist';
import { fetchVideoDetail, updateMetadata, approveVideo } from '../api/validation';

export default function VideoValidation() {
  const { id } = useParams();
  const [video, setVideo] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [checklist, setChecklist] = useState({
    title: false,
    description: false,
    thumbnail: false,
    quality: false
  });
  
  useEffect(() => {
    loadVideo();
  }, [id]);
  
  const loadVideo = async () => {
    const data = await fetchVideoDetail(id);
    setVideo(data.video);
    setMetadata(data.metadata);
  };
  
  const handleMetadataUpdate = async (updates) => {
    await updateMetadata(id, updates);
    loadVideo();
  };
  
  const handleApprove = async () => {
    await approveVideo(id);
    // Show success message or navigate
  };
  
  return (
    <div className="video-validation">
      <div className="validation-layout">
        <div className="left-panel">
          <VideoPlayer videoPath={video?.file_path} />
          <div className="video-info">
            <p>Duration: {video?.duration}s</p>
            <p>Size: {(video?.file_size / 1024 / 1024).toFixed(1)} MB</p>
            <p>Resolution: 1080x1920</p>
          </div>
          <button onClick={() => downloadVideo(id)}>
            Download Video
          </button>
        </div>
        
        <div className="center-panel">
          <MetadataEditor
            metadata={metadata}
            onUpdate={handleMetadataUpdate}
          />
        </div>
        
        <div className="right-panel">
          <UploadChecklist
            checklist={checklist}
            onChange={setChecklist}
          />
          
          <div className="action-buttons">
            <button onClick={handleApprove} className="btn-success">
              Approve for Upload
            </button>
            <button onClick={() => rejectVideo(id)} className="btn-danger">
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 🧪 Testing

- [ ] Test video playback
- [ ] Test metadata editing
- [ ] Test approval workflow
- [ ] Test download functionality
- [ ] Test checklist tracking

---

## 📊 Success Metrics

- ✅ 95%+ video approval rate
- ✅ <3 min average validation time
- ✅ Video player works smoothly
- ✅ Metadata editing is intuitive

---

**Related Issues**: #015, #016  
**Blocked By**: #016  
**Blocks**: None
