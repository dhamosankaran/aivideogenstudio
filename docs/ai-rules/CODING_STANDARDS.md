# Coding Standards: AIVideoGen

> This file defines coding conventions and patterns for AI-assisted development.

---

## 🐍 Python (Backend)

### General Rules
- **Python 3.11+** required
- **Type hints** on all function signatures
- **Docstrings** on public functions and classes
- **Black** for formatting (line length: 88)
- **isort** for import ordering

### Naming Conventions
```python
# Files: snake_case
video_downloader.py
rss_reader.py

# Classes: PascalCase
class VideoDownloader:
class TranscriptionService:

# Functions/variables: snake_case
def download_video(url: str) -> Path:
video_path = Path("./data")

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

### Function Signatures
```python
# ✅ Good: Type hints, clear naming
async def transcribe_audio(
    audio_path: Path,
    model: str = "large-v3",
    language: str | None = None,
) -> TranscriptionResult:
    """Transcribe audio file using Whisper.
    
    Args:
        audio_path: Path to audio file
        model: Whisper model size
        language: Optional language code
        
    Returns:
        TranscriptionResult with text and segments
        
    Raises:
        FileNotFoundError: If audio file doesn't exist
        TranscriptionError: If Whisper fails
    """
    ...

# ❌ Bad: No types, vague names
def process(x, y=None):
    ...
```

### Error Handling
```python
# ✅ Good: Specific exceptions, logging, re-raise
try:
    result = await external_api.call()
except httpx.TimeoutException as e:
    logger.error(f"API timeout after {timeout}s: {e}")
    raise ServiceTimeoutError(f"External API timed out") from e
except httpx.HTTPStatusError as e:
    logger.error(f"API error {e.response.status_code}: {e}")
    raise ServiceError(f"API returned {e.response.status_code}") from e

# ❌ Bad: Bare except, silent failure
try:
    result = api.call()
except:
    pass
```

### Import Order (isort style)
```python
# 1. Standard library
import os
from pathlib import Path

# 2. Third-party packages
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 3. Local imports
from app.config import settings
from app.models.video import Video
from app.services.downloader import download_video
```

---

## ⚛️ React/JavaScript (Frontend)

### General Rules
- **Functional components only** (no class components)
- **React 18** features (hooks, suspense)
- **ES6+** syntax always
- **PropTypes or JSDoc** for component props

### File Naming
```
# Components: PascalCase.jsx
VideoCard.jsx
ScriptEditor.jsx

# Hooks: camelCase starting with 'use'
useApi.js
useWebSocket.js

# Utils: camelCase
formatDate.js
apiClient.js
```

### Component Structure
```jsx
// ✅ Good: Clear, typed props, descriptive
import { useState, useEffect } from 'react';
import { Download, Check } from 'lucide-react';
import { useApi } from '../hooks/useApi';

/**
 * Displays a video card with download status
 * @param {Object} props
 * @param {string} props.videoId - Unique video identifier
 * @param {string} props.title - Video title
 * @param {function} props.onDownload - Callback when download starts
 */
export function VideoCard({ videoId, title, onDownload }) {
  const [status, setStatus] = useState('idle');
  
  const handleDownload = async () => {
    setStatus('downloading');
    await onDownload(videoId);
    setStatus('complete');
  };

  return (
    <div className="video-card">
      <h3>{title}</h3>
      <button onClick={handleDownload}>
        {status === 'complete' ? <Check /> : <Download />}
      </button>
    </div>
  );
}
```

### CSS Conventions
```css
/* Use BEM-style naming */
.video-card { }
.video-card__title { }
.video-card--highlighted { }

/* Use CSS custom properties for theming */
:root {
  --color-primary: #3B82F6;
  --color-background: #0F172A;
  --spacing-md: 1rem;
}

/* Mobile-first responsive design */
.container {
  padding: var(--spacing-md);
}

@media (min-width: 768px) {
  .container {
    padding: calc(var(--spacing-md) * 2);
  }
}
```

---

## 📁 File Organization

### One Responsibility Per File
```
# ✅ Good: Focused files
services/
├── video_downloader.py    # Only video downloading
├── audio_extractor.py     # Only audio extraction
└── transcriber.py         # Only transcription

# ❌ Bad: Kitchen sink
services/
└── video_utils.py         # Downloads, extracts, transcribes, everything
```

### Test File Naming
```
# Tests mirror source structure
backend/
├── app/
│   └── services/
│       └── video_downloader.py
└── tests/
    └── services/
        └── test_video_downloader.py
```

---

## 🧪 Testing Patterns

### Backend Tests (pytest)
```python
import pytest
from app.services.downloader import download_video

class TestVideoDownloader:
    """Tests for video download functionality."""
    
    def test_download_valid_youtube_url(self, tmp_path):
        """Should download video from valid YouTube URL."""
        url = "https://youtube.com/watch?v=valid123"
        result = download_video(url, output_dir=tmp_path)
        
        assert result.success is True
        assert result.file_path.exists()
    
    def test_download_invalid_url_raises(self):
        """Should raise ValueError for invalid URLs."""
        with pytest.raises(ValueError, match="Invalid video URL"):
            download_video("not-a-url")
    
    @pytest.mark.asyncio
    async def test_async_download(self):
        """Should work with async download."""
        ...
```

### Frontend Tests (Vitest)
```javascript
import { render, screen } from '@testing-library/react';
import { VideoCard } from './VideoCard';

describe('VideoCard', () => {
  it('renders video title', () => {
    render(<VideoCard videoId="123" title="Test Video" />);
    expect(screen.getByText('Test Video')).toBeInTheDocument();
  });
  
  it('calls onDownload when button clicked', async () => {
    const mockDownload = vi.fn();
    render(<VideoCard videoId="123" title="Test" onDownload={mockDownload} />);
    
    await userEvent.click(screen.getByRole('button'));
    expect(mockDownload).toHaveBeenCalledWith('123');
  });
});
```

---

## 📝 Commit Messages

Use conventional commits:
```
type(scope): description

feat(api): add video download endpoint
fix(transcriber): handle empty audio files
docs(readme): update installation instructions
refactor(services): extract audio processing logic
test(downloader): add tests for URL validation
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

---

## 🚨 Security Guidelines

### Never Commit Secrets
```python
# ✅ Good: Environment variable
api_key = os.getenv("OPENAI_API_KEY")

# ❌ Bad: Hardcoded
api_key = "sk-1234567890abcdef"
```

### Validate All Input
```python
# ✅ Good: URL validation before use
from urllib.parse import urlparse

def download_video(url: str) -> Path:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Invalid URL scheme")
    if parsed.netloc not in ALLOWED_DOMAINS:
        raise ValueError("Domain not allowed")
    ...
```

### Parameterize Database Queries
```python
# ✅ Good: Parameterized
db.execute("SELECT * FROM videos WHERE id = :id", {"id": video_id})

# ❌ Bad: String interpolation (SQL injection risk)
db.execute(f"SELECT * FROM videos WHERE id = {video_id}")
```
