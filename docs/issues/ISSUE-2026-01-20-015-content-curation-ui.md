# ISSUE-015: Content Curation UI

**Created**: 2026-01-20  
**Priority**: 🔴 P0 (Critical)  
**Phase**: Phase 2 - Creator Studio  
**Estimated**: 4-5 hours  
**Status**: ✅ Complete

---

## 🎯 Objective

Build a content curation UI that allows users to browse, filter, and select articles from RSS feeds for script generation. This gives creators control over what content becomes videos.

---

## 📋 User Story

**As a** video creator  
**I want to** browse and select articles from my RSS feeds  
**So that** I can control which content becomes videos

---

## ✅ Acceptance Criteria

### Must Have
- [ ] Display list of articles from RSS feeds in card format
- [ ] Show article metadata (source, title, summary, date)
- [ ] Filter by source, date range, content type, and status
- [ ] Search articles by keywords
- [ ] Select multiple articles with checkboxes
- [ ] Generate scripts from selected articles (bulk action)
- [ ] Track processing status (Unprocessed → Script → Video)

### Should Have
- [ ] AI-powered relevance scoring (0-10 scale)
- [ ] Auto-suggested content type (Daily Update, Big Tech, etc.)
- [ ] Pagination (20 articles per page)
- [ ] Sort by date, relevance, or source

### Nice to Have
- [ ] Article detail view (expand to see full content)
- [ ] Mark articles as irrelevant (hide from feed)
- [ ] Save filter presets
- [ ] Keyboard shortcuts for selection

---

## 🏗️ Technical Implementation

### Database Changes

**New Table**: `content_items`
```sql
CREATE TABLE content_items (
    id SERIAL PRIMARY KEY,
    source VARCHAR NOT NULL,           -- RSS feed source
    title VARCHAR NOT NULL,
    url VARCHAR UNIQUE NOT NULL,
    description TEXT,
    content TEXT,                      -- Full article content
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW(),
    
    -- Curation fields
    relevance_score FLOAT,             -- AI-generated score (0-10)
    suggested_content_type VARCHAR,    -- AI suggestion
    selected_for_script BOOLEAN DEFAULT FALSE,
    selected_at TIMESTAMP,
    
    -- Processing status
    status VARCHAR DEFAULT 'unprocessed', -- unprocessed, script_generated, video_created
    script_id INTEGER REFERENCES scripts(id),
    
    -- Metadata
    key_points JSON,                   -- Extracted key points
    tags JSON,                         -- Auto-generated tags
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_content_status ON content_items(status);
CREATE INDEX idx_content_selected ON content_items(selected_for_script);
CREATE INDEX idx_content_published ON content_items(published_at DESC);
CREATE INDEX idx_content_source ON content_items(source);
```

**Migration**: Migrate existing `articles` table data to `content_items`

---

### Backend API Endpoints

**File**: `backend/app/routers/content_router.py`

```python
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.models import ContentItem
from app.services.content_service import ContentService

router = APIRouter(prefix="/api/content", tags=["content"])

@router.get("/items")
async def list_content_items(
    source: Optional[str] = None,
    date_range: Optional[str] = "last_7_days",
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List content items with filters and pagination."""
    service = ContentService(db)
    return service.list_items(
        source=source,
        date_range=date_range,
        content_type=content_type,
        status=status,
        search=search,
        page=page,
        page_size=page_size
    )

@router.get("/items/{id}")
async def get_content_item(id: int, db: Session = Depends(get_db)):
    """Get full content item details."""
    service = ContentService(db)
    return service.get_item(id)

@router.post("/items/select")
async def select_items(item_ids: List[int], db: Session = Depends(get_db)):
    """Mark items as selected for script generation."""
    service = ContentService(db)
    return service.select_items(item_ids)

@router.post("/generate-scripts")
async def generate_scripts(
    item_ids: List[int],
    content_type: Optional[str] = "daily_update",
    db: Session = Depends(get_db)
):
    """Generate scripts from selected content items."""
    service = ContentService(db)
    return service.generate_scripts(item_ids, content_type)

@router.post("/items/{id}/analyze")
async def analyze_content(id: int, db: Session = Depends(get_db)):
    """Analyze article and generate relevance score + suggestions."""
    service = ContentService(db)
    return service.analyze_item(id)
```

---

### Backend Service

**File**: `backend/app/services/content_service.py`

```python
from app.models import ContentItem, Script
from app.services.script_service import ScriptService
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

class ContentService:
    def __init__(self, db: Session):
        self.db = db
        self.script_service = ScriptService(db)
    
    def list_items(self, source, date_range, content_type, status, search, page, page_size):
        """List content items with filters."""
        query = self.db.query(ContentItem)
        
        # Apply filters
        if source:
            query = query.filter(ContentItem.source == source)
        
        if date_range:
            days = self._parse_date_range(date_range)
            cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
            query = query.filter(ContentItem.published_at >= cutoff)
        
        if content_type:
            query = query.filter(ContentItem.suggested_content_type == content_type)
        
        if status:
            query = query.filter(ContentItem.status == status)
        
        if search:
            query = query.filter(
                ContentItem.title.ilike(f"%{search}%") |
                ContentItem.description.ilike(f"%{search}%")
            )
        
        # Pagination
        total = query.count()
        items = query.order_by(ContentItem.published_at.desc()) \
                    .offset((page - 1) * page_size) \
                    .limit(page_size) \
                    .all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    def select_items(self, item_ids: List[int]):
        """Mark items as selected."""
        items = self.db.query(ContentItem).filter(ContentItem.id.in_(item_ids)).all()
        for item in items:
            item.selected_for_script = True
            item.selected_at = datetime.datetime.now()
        self.db.commit()
        return {"selected": len(items)}
    
    def generate_scripts(self, item_ids: List[int], content_type: str):
        """Generate scripts from selected items."""
        items = self.db.query(ContentItem).filter(ContentItem.id.in_(item_ids)).all()
        script_ids = []
        
        for item in items:
            # Generate script using script service
            script = self.script_service.generate_from_article(
                article_id=item.id,
                content_type=content_type
            )
            
            # Update content item
            item.status = "script_generated"
            item.script_id = script.id
            
            script_ids.append(script.id)
        
        self.db.commit()
        return {"scripts_created": len(script_ids), "script_ids": script_ids}
    
    def analyze_item(self, item_id: int):
        """Analyze content and generate AI insights."""
        item = self.db.query(ContentItem).filter(ContentItem.id == item_id).first()
        
        # Use LLM to analyze
        analysis = self.script_service.llm.analyze_article(
            title=item.title,
            content=item.description or item.content
        )
        
        # Update item with analysis
        item.relevance_score = analysis.get("score", 5.0)
        item.suggested_content_type = analysis.get("content_type", "daily_update")
        item.key_points = analysis.get("key_points", [])
        item.tags = analysis.get("tags", [])
        
        self.db.commit()
        return analysis
```

---

### Frontend Components

**File**: `frontend/src/pages/ContentLibrary.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import ArticleCard from '../components/ArticleCard';
import FilterBar from '../components/FilterBar';
import BulkActions from '../components/BulkActions';
import { fetchContentItems, generateScripts } from '../api/content';

export default function ContentLibrary() {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState([]);
  const [filters, setFilters] = useState({
    source: null,
    dateRange: 'last_7_days',
    contentType: null,
    status: null,
    search: ''
  });
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    loadItems();
  }, [filters]);
  
  const loadItems = async () => {
    setLoading(true);
    const data = await fetchContentItems(filters);
    setItems(data.items);
    setLoading(false);
  };
  
  const handleSelect = (id) => {
    setSelected(prev => 
      prev.includes(id) 
        ? prev.filter(i => i !== id)
        : [...prev, id]
    );
  };
  
  const handleGenerateScripts = async () => {
    await generateScripts(selected);
    setSelected([]);
    loadItems();
  };
  
  return (
    <div className="content-library">
      <h1>Content Library</h1>
      
      <FilterBar filters={filters} onChange={setFilters} />
      
      <div className="article-grid">
        {items.map(item => (
          <ArticleCard
            key={item.id}
            item={item}
            selected={selected.includes(item.id)}
            onSelect={handleSelect}
          />
        ))}
      </div>
      
      {selected.length > 0 && (
        <BulkActions
          count={selected.length}
          onGenerate={handleGenerateScripts}
        />
      )}
    </div>
  );
}
```

**File**: `frontend/src/components/ArticleCard.jsx`

```jsx
import React from 'react';

export default function ArticleCard({ item, selected, onSelect }) {
  const getStatusColor = (status) => {
    switch(status) {
      case 'unprocessed': return 'orange';
      case 'script_generated': return 'blue';
      case 'video_created': return 'green';
      default: return 'gray';
    }
  };
  
  return (
    <div className={`article-card ${selected ? 'selected' : ''}`}>
      <div className="card-header">
        <span className="source-badge">{item.source}</span>
        <span className="timestamp">{item.published_at}</span>
      </div>
      
      <h3>{item.title}</h3>
      <p className="description">{item.description}</p>
      
      <div className="card-footer">
        <span className="score">Score: {item.relevance_score}/10</span>
        <span className="content-type">{item.suggested_content_type}</span>
        <span className={`status ${getStatusColor(item.status)}`}>
          {item.status}
        </span>
      </div>
      
      <input
        type="checkbox"
        checked={selected}
        onChange={() => onSelect(item.id)}
        className="select-checkbox"
      />
    </div>
  );
}
```

---

## 🧪 Testing

### Unit Tests
- [ ] Test content service methods
- [ ] Test API endpoints
- [ ] Test React components

### Integration Tests
- [ ] Test full workflow (browse → select → generate)
- [ ] Test filters and search
- [ ] Test pagination

### Manual Testing
- [ ] Browse articles from real RSS feeds
- [ ] Test all filters
- [ ] Select and generate scripts
- [ ] Verify status updates

---

## 📊 Success Metrics

- ✅ User can browse all articles from RSS feeds
- ✅ Filters work correctly (source, date, type, status)
- ✅ Search returns relevant results
- ✅ Bulk selection and script generation works
- ✅ Status tracking is accurate
- ✅ <2s page load time
- ✅ 90%+ user satisfaction

---

## 🔗 Dependencies

- Existing RSS feed ingestion system
- Script generation service
- Database (SQLite → PostgreSQL migration recommended)

---

## 📝 Notes

- This is the **highest priority** feature for Phase 2
- Gives user immediate control over content selection
- Foundation for script review and video validation UIs
- Should be completed before moving to script review

---

## 🚀 Next Steps After Completion

1. Test with real RSS feed data
2. Gather user feedback
3. Iterate on UI/UX
4. Move to Issue #016 (Script Review UI)

---

**Related Issues**: #016 (Script Review), #017 (Video Validation)  
**Blocked By**: None  
**Blocks**: #016
