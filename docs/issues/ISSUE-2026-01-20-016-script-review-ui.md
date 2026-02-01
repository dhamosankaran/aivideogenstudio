# ISSUE-016: Script Review UI

**Created**: 2026-01-20  
**Priority**: 🔴 P0 (Critical)  
**Phase**: Phase 2 - Creator Studio  
**Estimated**: 3-4 hours  
**Status**: ✅ Complete  
**Depends On**: #015 (Content Curation UI)

---

## 🎯 Objective

Build a script review UI that allows users to review AI-generated scripts, edit content, and approve for video generation. This gives creators control over the script before committing to video production.

---

## 📋 User Story

**As a** video creator  
**I want to** review and edit AI-generated scripts before video generation  
**So that** I can ensure the content matches my vision and quality standards

---

## ✅ Acceptance Criteria

### Must Have
- [ ] Display list of scripts pending review
- [ ] Side-by-side view of source article and generated script
- [ ] Edit script title (with 60-character limit)
- [ ] Edit scene narration
- [ ] Edit image keywords
- [ ] Approve script → trigger video generation
- [ ] Reject script → return to content library
- [ ] Regenerate script with AI

### Should Have
- [ ] Scene reordering (drag & drop)
- [ ] Add/remove scenes
- [ ] Change content type
- [ ] Preview image search results
- [ ] Estimated duration display
- [ ] Save draft (partial edits)

### Nice to Have
- [ ] TTS preview (hear narration before video)
- [ ] Collaborative editing (comments)
- [ ] Version history
- [ ] Script templates

---

## 🏗️ Technical Implementation

### Database Changes

```sql
-- Add review fields to scripts table
ALTER TABLE scripts ADD COLUMN content_item_id INTEGER REFERENCES content_items(id);
ALTER TABLE scripts ADD COLUMN script_status VARCHAR DEFAULT 'pending'; -- pending, approved, rejected
ALTER TABLE scripts ADD COLUMN reviewed_at TIMESTAMP;
ALTER TABLE scripts ADD COLUMN rejection_reason TEXT;
ALTER TABLE scripts ADD COLUMN draft_data JSON; -- For saving partial edits

CREATE INDEX idx_scripts_status ON scripts(script_status);
CREATE INDEX idx_scripts_content_item ON scripts(content_item_id);
```

### Backend API Endpoints

**File**: `backend/app/routers/script_router.py`

```python
@router.get("/scripts/pending")
async def list_pending_scripts(db: Session = Depends(get_db)):
    """List scripts pending review."""
    scripts = db.query(Script).filter(
        Script.script_status == "pending"
    ).order_by(Script.created_at.desc()).all()
    return scripts

@router.get("/scripts/{id}/detail")
async def get_script_detail(id: int, db: Session = Depends(get_db)):
    """Get script with source article."""
    script = db.query(Script).filter(Script.id == id).first()
    content_item = db.query(ContentItem).filter(
        ContentItem.id == script.content_item_id
    ).first()
    
    return {
        "script": script,
        "source_article": content_item
    }

@router.put("/scripts/{id}")
async def update_script(
    id: int,
    title: Optional[str] = None,
    scenes: Optional[List[dict]] = None,
    content_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update script content."""
    script = db.query(Script).filter(Script.id == id).first()
    
    if title:
        script.catchy_title = title
    if scenes:
        script.scenes = scenes
    if content_type:
        script.content_type = content_type
    
    script.updated_at = datetime.datetime.now()
    db.commit()
    
    return script

@router.post("/scripts/{id}/approve")
async def approve_script(id: int, db: Session = Depends(get_db)):
    """Approve script and trigger video generation."""
    script = db.query(Script).filter(Script.id == id).first()
    script.script_status = "approved"
    script.reviewed_at = datetime.datetime.now()
    db.commit()
    
    # Trigger video generation
    video_service = EnhancedVideoCompositionService(db)
    audio_service = AudioService(db)
    
    # Generate audio
    audio = audio_service.generate_audio(script.id)
    
    # Create video task
    video = video_service.create_video_task(
        script_id=script.id,
        audio_id=audio.id,
        background_style="scenes"
    )
    
    # Queue video generation
    video_service.process_video(video.id)
    
    return {"video_id": video.id, "status": "queued"}

@router.post("/scripts/{id}/reject")
async def reject_script(
    id: int,
    reason: str,
    db: Session = Depends(get_db)
):
    """Reject script."""
    script = db.query(Script).filter(Script.id == id).first()
    script.script_status = "rejected"
    script.rejection_reason = reason
    script.reviewed_at = datetime.datetime.now()
    db.commit()
    
    return {"status": "rejected"}

@router.post("/scripts/{id}/regenerate")
async def regenerate_script(id: int, db: Session = Depends(get_db)):
    """Regenerate script from same article."""
    old_script = db.query(Script).filter(Script.id == id).first()
    content_item = db.query(ContentItem).filter(
        ContentItem.id == old_script.content_item_id
    ).first()
    
    # Generate new script
    script_service = ScriptService(db)
    new_script = script_service.generate_from_article(
        article_id=content_item.id,
        content_type=old_script.content_type
    )
    
    # Mark old script as rejected
    old_script.script_status = "rejected"
    old_script.rejection_reason = "Regenerated"
    
    db.commit()
    
    return {"new_script_id": new_script.id}
```

### Frontend Components

**File**: `frontend/src/pages/ScriptReview.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ArticlePanel from '../components/ArticlePanel';
import ScriptEditor from '../components/ScriptEditor';
import { fetchScriptDetail, updateScript, approveScript, rejectScript } from '../api/scripts';

export default function ScriptReview() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [script, setScript] = useState(null);
  const [article, setArticle] = useState(null);
  const [editing, setEditing] = useState(false);
  
  useEffect(() => {
    loadScript();
  }, [id]);
  
  const loadScript = async () => {
    const data = await fetchScriptDetail(id);
    setScript(data.script);
    setArticle(data.source_article);
  };
  
  const handleSave = async (updates) => {
    await updateScript(id, updates);
    loadScript();
    setEditing(false);
  };
  
  const handleApprove = async () => {
    await approveScript(id);
    navigate('/videos'); // Go to video validation
  };
  
  const handleReject = async (reason) => {
    await rejectScript(id, reason);
    navigate('/content'); // Go back to content library
  };
  
  return (
    <div className="script-review">
      <div className="review-layout">
        <div className="left-panel">
          <ArticlePanel article={article} />
        </div>
        
        <div className="right-panel">
          <ScriptEditor
            script={script}
            editing={editing}
            onEdit={() => setEditing(true)}
            onSave={handleSave}
            onCancel={() => setEditing(false)}
          />
        </div>
      </div>
      
      <div className="action-bar">
        <button onClick={() => handleReject('Not suitable')} className="btn-danger">
          Reject
        </button>
        <button onClick={() => regenerateScript(id)} className="btn-secondary">
          Regenerate Script
        </button>
        <button onClick={handleApprove} className="btn-success">
          Approve & Generate Video
        </button>
      </div>
    </div>
  );
}
```

---

## 🧪 Testing

- [ ] Test script list view
- [ ] Test side-by-side article/script view
- [ ] Test editing (title, scenes, keywords)
- [ ] Test approve workflow (triggers video generation)
- [ ] Test reject workflow (returns to content library)
- [ ] Test regenerate (creates new script)

---

## 📊 Success Metrics

- ✅ 80%+ script approval rate
- ✅ <5 min average review time
- ✅ 90%+ user satisfaction with editing interface
- ✅ <10% regeneration rate

---

**Related Issues**: #015 (Content Curation), #017 (Video Validation)  
**Blocked By**: #015  
**Blocks**: None
