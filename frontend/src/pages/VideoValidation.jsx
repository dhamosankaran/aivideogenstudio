import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchPendingVideos, fetchVideoDetail, updateVideoMetadata, approveVideo, rejectVideo, getVideoUrl, generateMetadata, generateThumbnail, getThumbnailPrompt } from '../services/videoApi';
import './VideoValidation.css';

export default function VideoValidation() {
    const [searchParams] = useSearchParams();
    const initialVideoId = searchParams.get('videoId');

    const [videos, setVideos] = useState([]);
    const [selectedVideoId, setSelectedVideoId] = useState(null);
    const [videoDetail, setVideoDetail] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [saving, setSaving] = useState(false);
    const pollingInterval = useRef(null);

    // Editable fields
    const [editedTitle, setEditedTitle] = useState('');
    const [editedDescription, setEditedDescription] = useState('');
    const [editedHashtags, setEditedHashtags] = useState('');
    const [editedTags, setEditedTags] = useState('');

    // Generation states
    const [generatingMetadata, setGeneratingMetadata] = useState(false);
    const [generatingThumbnail, setGeneratingThumbnail] = useState(false);
    const [thumbnailPrompt, setThumbnailPrompt] = useState('');
    const [showPromptEditor, setShowPromptEditor] = useState(false);
    const [loadingPrompt, setLoadingPrompt] = useState(false);

    // Handle initial navigation from query params
    useEffect(() => {
        if (initialVideoId) {
            handleSelectVideo(initialVideoId);
        }
    }, [initialVideoId]);

    // Initial load
    useEffect(() => {
        loadPendingVideos();
    }, []);

    // Polling Logic
    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                // 1. Update list silently
                const data = await fetchPendingVideos();
                setVideos(data);

                // 2. If specific video is selected and "rendering", check its status specifically
                if (selectedVideoId) {
                    updateDetailIfRendering(selectedVideoId);
                }
            } catch (err) {
                console.error("Polling error", err);
            }
        }, 5000); // Poll every 5 seconds

        return () => clearInterval(interval);
    }, [selectedVideoId]);

    const updateDetailIfRendering = async (id) => {
        try {
            const data = await fetchVideoDetail(id);
            setVideoDetail(prev => {
                if (!prev) return data;
                // Update if status changed (render done) or metadata updated (SEO auto-generated)
                if (prev.video.status !== data.video.status ||
                    prev.video.file_path !== data.video.file_path ||
                    prev.video.youtube_description !== data.video.youtube_description) {
                    // Auto-refresh editable fields when metadata arrives
                    if (data.video.youtube_title) setEditedTitle(data.video.youtube_title);
                    if (data.video.youtube_description) setEditedDescription(data.video.youtube_description);
                    if (data.video.youtube_tags) setEditedTags(data.video.youtube_tags.join(', '));
                    return data;
                }
                return prev;
            });
        } catch (e) { console.error(e) }
    };

    const loadPendingVideos = async (showSpinner = true) => {
        if (showSpinner) setLoading(true);
        setError(null);

        try {
            const data = await fetchPendingVideos();
            setVideos(data);
        } catch (err) {
            setError(err.message);
            console.error('Failed to load pending videos:', err);
        } finally {
            if (showSpinner) setLoading(false);
        }
    };

    const handleSelectVideo = async (videoId) => {
        setLoading(true); // Detail loading
        setError(null);
        setSelectedVideoId(videoId);

        try {
            const data = await fetchVideoDetail(videoId);
            setVideoDetail(data);
            setEditedTitle(data.video.youtube_title || data.script?.catchy_title || '');
            setEditedDescription(data.video.youtube_description || data.script?.video_description || '');
            setEditedHashtags(data.script?.hashtags?.join(' ') || '');
            setEditedTags(data.video.youtube_tags?.join(', ') || '');
        } catch (err) {
            setError(err.message);
            console.error('Failed to load video detail:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (!selectedVideoId) return;

        setSaving(true);
        try {
            const hashtags = editedHashtags.split(' ').filter(h => h.trim());
            const tags = editedTags.split(',').map(t => t.trim()).filter(t => t);
            await updateVideoMetadata(selectedVideoId, {
                youtube_title: editedTitle,
                youtube_description: editedDescription,
                hashtags: hashtags,
                youtube_tags: tags
            });

            alert('Metadata saved successfully!');
            await handleSelectVideo(selectedVideoId); // Reload detail
        } catch (err) {
            alert(`Failed to save: ${err.message}`);
        } finally {
            setSaving(false);
        }
    };

    const handleApprove = async () => {
        if (!selectedVideoId) return;
        if (!confirm('Approve this video and upload to YouTube as Private?')) return;

        setSaving(true);
        try {
            const hashtags = editedHashtags.split(' ').filter(h => h.trim());
            const tags = editedTags.split(',').map(t => t.trim()).filter(t => t);

            const result = await approveVideo(selectedVideoId, {
                youtube_title: editedTitle,
                youtube_description: editedDescription,
                hashtags: hashtags,
                youtube_tags: tags,
                privacy_status: 'private',  // Safe zone: always start private
            });

            if (result.youtube_uploaded) {
                alert(`✅ Video approved and uploaded to YouTube!\n\nURL: ${result.youtube_url}\nStatus: ${result.privacy_status}\n\nCheck YouTube Studio to set it public when ready.`);
            } else if (result.upload_warning) {
                alert(`⚠️ Video approved locally.\n\n${result.upload_warning}\n\nTo enable YouTube uploads, run:\npython -m app.services.youtube_upload_service --auth`);
            } else {
                alert('Video approved! Ready for YouTube upload.');
            }

            setVideoDetail(null);
            setSelectedVideoId(null);
            await loadPendingVideos();
        } catch (err) {
            alert(`Failed to approve: ${err.message}`);
        } finally {
            setSaving(false);
        }
    };

    const handleReject = async () => {
        if (!selectedVideoId) return;
        const reason = prompt('Reason for rejection:');
        if (!reason) return;

        setSaving(true);
        try {
            await rejectVideo(selectedVideoId, reason);
            alert('Video rejected.');
            setVideoDetail(null);
            setSelectedVideoId(null);
            await loadPendingVideos();
        } catch (err) {
            alert(`Failed to reject: ${err.message}`);
        } finally {
            setSaving(false);
        }
    };

    const handleDownload = () => {
        if (!selectedVideoId) return;
        window.open(getVideoUrl(selectedVideoId), '_blank');
    };

    const formatFileSize = (bytes) => {
        if (!bytes) return 'Unknown';
        const mb = bytes / (1024 * 1024);
        return `${mb.toFixed(1)} MB`;
    };

    const formatDuration = (seconds) => {
        if (!seconds) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Render Logic
    const isRendering = (status) => status === 'rendering' || status === 'pending';

    return (
        <div className="video-validation">
            <header className="video-validation-header">
                <div className="header-content">
                    <h1>Video Validation</h1>
                    <p className="subtitle">Review and approve content for publication</p>
                </div>
                <div className="header-actions">
                    <button
                        onClick={() => loadPendingVideos(true)}
                        className={`btn-refresh ${loading ? 'spinning' : ''}`}
                        title="Refresh List"
                    >
                        <span className="icon">🔄</span> Refresh
                    </button>
                </div>
            </header>

            {error && (
                <div className="error-message">
                    <strong>Error:</strong> {error}
                </div>
            )}

            {!selectedVideoId ? (
                // GRID VIEW
                <div className="video-list-view">
                    {loading && videos.length === 0 ? (
                        <div className="loading-state">
                            <div className="spinner"></div>
                            <p>Loading videos...</p>
                        </div>
                    ) : videos.length === 0 ? (
                        <div className="empty-state">
                            <span className="empty-state-illustration">🎬</span>
                            <h3>No pending videos</h3>
                            <p>Approved scripts will appear here automatically.</p>
                        </div>
                    ) : (
                        <div className="videos-grid">
                            {videos.map(video => (
                                <div key={video.id} className="video-card" onClick={() => handleSelectVideo(video.id)}>
                                    <div className="video-thumbnail">
                                        {video.thumbnail_path ? (
                                            <img src={video.thumbnail_path} alt="Thumbnail" />
                                        ) : (
                                            <div className="thumbnail-placeholder">
                                                {/* Gradient background handles the visual */}
                                                ▶
                                            </div>
                                        )}
                                        <div className={`status-badge ${video.status}`}>
                                            {video.status === 'rendering' ? '⚙️ Rendering' :
                                                video.status === 'completed' ? '✅ Ready' :
                                                    video.status}
                                        </div>
                                    </div>
                                    <div className="video-info">
                                        <h3>{video.article_title || video.youtube_title || `Video #${video.id}`}</h3>
                                        <div className="video-meta">
                                            <span>⏱ {formatDuration(video.duration)}</span>
                                            {video.file_size && <span>💾 {formatFileSize(video.file_size)}</span>}
                                        </div>
                                        <div className="video-footer">
                                            <span className="created">{new Date(video.created_at).toLocaleDateString()}</span>
                                            <button className="btn-review-sm">Review →</button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            ) : (
                // SPLIT / DETAIL VIEW
                <div className="detail-container">
                    {/* Left Sidebar List */}
                    <div className="sidebar-list">
                        {videos.map(v => (
                            <div
                                key={v.id}
                                className={`sidebar-item ${v.id === selectedVideoId ? 'active' : ''}`}
                                onClick={() => handleSelectVideo(v.id)}
                            >
                                <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                                    {v.article_title || v.youtube_title || `Video #${v.id}`}
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#666' }}>
                                    <span>{formatDuration(v.duration)}</span>
                                    {v.status === 'failed' ? (
                                        <button
                                            className="btn-regenerate-sm"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                alert("Please go to Script Review to regenerate this video.");
                                            }}
                                            style={{
                                                fontSize: '0.75rem',
                                                padding: '0.2rem 0.5rem',
                                                background: '#fee2e2',
                                                color: '#dc2626',
                                                border: '1px solid #fecaca',
                                                borderRadius: '4px',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            ⚠️ Failed (Regenerate)
                                        </button>
                                    ) : (
                                        <span style={{ textTransform: 'capitalize' }}>{v.status}</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Main Content */}
                    <div className="main-detail">
                        {/* Back button for mobile mainly, or just quick exit */}
                        <div style={{ marginBottom: '1rem' }}>
                            <button onClick={() => setSelectedVideoId(null)} className="btn-secondary" style={{ padding: '0.5rem 1rem' }}>
                                ← Back to Grid
                            </button>
                        </div>

                        {!videoDetail ? (
                            <div className="loading-state"><div className="spinner"></div></div>
                        ) : (
                            <>
                                <div className="video-player-section">
                                    <div className="player-header" style={{ padding: '0 0 1rem 0', borderBottom: '1px solid #eee', marginBottom: '1rem' }}>
                                        <h2 style={{ margin: 0, fontSize: '1.2rem' }}>{videoDetail.article?.title || 'Video Preview'}</h2>
                                        {videoDetail.script?.catchy_title && (
                                            <p style={{ margin: '0.5rem 0 0 0', color: '#666', fontSize: '0.9rem' }}>
                                                {videoDetail.script.catchy_title}
                                            </p>
                                        )}
                                    </div>

                                    <div className="video-player-wrapper">
                                        {isRendering(videoDetail.video.status) ? (
                                            <div className="empty-state">
                                                <div className="spinner"></div>
                                                <h3>Rendering Video...</h3>
                                                <p>This usually takes 3-5 minutes. The page will auto-update.</p>
                                            </div>
                                        ) : (
                                            <div className="player-container relative">
                                                <video
                                                    controls
                                                    className="video-player"
                                                    src={getVideoUrl(selectedVideoId)}
                                                    onError={(e) => {
                                                        console.error("Video Error:", e);
                                                        e.target.parentElement.innerHTML = `
                                                            <div class="error-message" style="margin:2rem; text-align:center; color: white;">
                                                                <p>⚠️ Failed to load video.</p>
                                                                <p style="font-size:0.8rem; color:#aaa">The file might be missing or corrupt.</p>
                                                                <button onclick="window.location.reload()" style="margin-top:1rem; padding:0.5rem 1rem; background:#333; color: white; border:1px solid #555; border-radius:4px; cursor:pointer">
                                                                    Retry
                                                                </button>
                                                            </div>
                                                        `;
                                                    }}
                                                >
                                                    Your browser does not support the video tag.
                                                </video>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="metadata-grid">
                                    <div className="metadata-form">
                                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginBottom: '1rem', flexWrap: 'wrap' }}>
                                            <button
                                                onClick={async () => {
                                                    if (!selectedVideoId) return;
                                                    setGeneratingMetadata(true);
                                                    try {
                                                        const result = await generateMetadata(selectedVideoId);
                                                        if (result.success && result.metadata) {
                                                            setEditedTitle(result.metadata.title || '');
                                                            setEditedDescription(result.metadata.description || '');
                                                            setEditedHashtags(result.metadata.hashtags?.join(' ') || '');
                                                            setEditedTags(result.metadata.tags?.join(', ') || '');
                                                        }
                                                    } catch (err) {
                                                        alert(`Failed to generate metadata: ${err.message}`);
                                                    } finally {
                                                        setGeneratingMetadata(false);
                                                    }
                                                }}
                                                disabled={generatingMetadata || generatingThumbnail}
                                                className="btn-secondary"
                                                style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem', background: generatingMetadata ? '#e5e7eb' : 'linear-gradient(135deg, #8b5cf6, #6366f1)', color: generatingMetadata ? '#666' : 'white', border: 'none' }}
                                            >
                                                {generatingMetadata ? '⏳ Generating...' : '✨ AI Auto-Fill'}
                                            </button>
                                            <button
                                                onClick={async () => {
                                                    if (!selectedVideoId) return;
                                                    setLoadingPrompt(true);
                                                    try {
                                                        const result = await getThumbnailPrompt(selectedVideoId);
                                                        if (result.success) {
                                                            setThumbnailPrompt(result.prompt);
                                                            setShowPromptEditor(true);
                                                        }
                                                    } catch (err) {
                                                        alert(`Failed to load prompt: ${err.message}`);
                                                    } finally {
                                                        setLoadingPrompt(false);
                                                    }
                                                }}
                                                disabled={generatingMetadata || generatingThumbnail || loadingPrompt}
                                                className="btn-secondary"
                                                style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem', background: loadingPrompt ? '#e5e7eb' : 'linear-gradient(135deg, #f59e0b, #ef4444)', color: loadingPrompt ? '#666' : 'white', border: 'none' }}
                                            >
                                                {loadingPrompt ? '⏳ Loading...' : '🎨 AI Thumbnail'}
                                            </button>
                                        </div>

                                        {/* Thumbnail Prompt Editor */}
                                        {showPromptEditor && (
                                            <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'linear-gradient(135deg, #fef3c7, #fed7aa)', borderRadius: '12px', border: '1px solid #f59e0b' }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                                                    <label style={{ fontWeight: '600', color: '#92400e' }}>🎨 Thumbnail Prompt</label>
                                                    <button
                                                        onClick={() => setShowPromptEditor(false)}
                                                        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem' }}
                                                    >×</button>
                                                </div>
                                                <textarea
                                                    className="form-input"
                                                    rows={8}
                                                    value={thumbnailPrompt}
                                                    onChange={(e) => setThumbnailPrompt(e.target.value)}
                                                    placeholder="AI thumbnail generation prompt..."
                                                    style={{ fontFamily: 'monospace', fontSize: '0.85rem', marginBottom: '0.75rem' }}
                                                />
                                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                                    <button
                                                        onClick={async () => {
                                                            if (!selectedVideoId) return;
                                                            setGeneratingThumbnail(true);
                                                            try {
                                                                const result = await generateThumbnail(selectedVideoId, thumbnailPrompt);
                                                                if (result.success) {
                                                                    alert('Thumbnail generated! Refreshing...');
                                                                    setShowPromptEditor(false);
                                                                    await handleSelectVideo(selectedVideoId);
                                                                }
                                                            } catch (err) {
                                                                alert(`Failed to generate thumbnail: ${err.message}`);
                                                            } finally {
                                                                setGeneratingThumbnail(false);
                                                            }
                                                        }}
                                                        disabled={generatingThumbnail}
                                                        style={{ flex: 1, padding: '0.6rem 1rem', background: generatingThumbnail ? '#e5e7eb' : 'linear-gradient(135deg, #f59e0b, #ef4444)', color: 'white', border: 'none', borderRadius: '8px', fontWeight: '600', cursor: generatingThumbnail ? 'not-allowed' : 'pointer' }}
                                                    >
                                                        {generatingThumbnail ? '⏳ Generating Thumbnail...' : '🚀 Generate with This Prompt'}
                                                    </button>
                                                </div>
                                                <small style={{ color: '#92400e', display: 'block', marginTop: '0.5rem' }}>
                                                    Edit the prompt above to customize your thumbnail. Uses Gemini AI image generation.
                                                </small>
                                            </div>
                                        )}

                                        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                                            <label>YouTube Title ({editedTitle.length}/100)</label>
                                            <input
                                                type="text"
                                                className="form-input"
                                                value={editedTitle}
                                                onChange={(e) => setEditedTitle(e.target.value.slice(0, 100))}
                                                placeholder="Enter engaging title..."
                                            />
                                        </div>

                                        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                                            <label>Description ({editedDescription.length}/5000)
                                                <span style={{
                                                    fontSize: '0.75rem',
                                                    color: editedDescription.length < 300 ? '#ef4444' : editedDescription.length <= 1500 ? '#22c55e' : '#666',
                                                    marginLeft: '0.5rem'
                                                }}>
                                                    {editedDescription.length < 300 ? '⚠️ Too short for SEO' : editedDescription.length <= 1500 ? '✅ Great length' : ''}
                                                </span>
                                            </label>
                                            <textarea
                                                className="form-input"
                                                rows={8}
                                                value={editedDescription}
                                                onChange={(e) => setEditedDescription(e.target.value.slice(0, 5000))}
                                                placeholder="Video description..."
                                            />
                                            <small style={{ color: '#666', fontSize: '0.75rem' }}>Aim for 500-1500 chars for optimal YouTube SEO. Include key takeaways, book context, and CTA.</small>
                                        </div>

                                        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                                            <label>Hashtags</label>
                                            <input
                                                type="text"
                                                className="form-input"
                                                value={editedHashtags}
                                                onChange={(e) => setEditedHashtags(e.target.value)}
                                                placeholder="#AI #Tech #Trending"
                                            />
                                            <small style={{ color: '#666', fontSize: '0.75rem' }}>Space-separated hashtags for description</small>
                                        </div>

                                        <div className="form-group">
                                            <label>Tags (for YouTube search) ({editedTags.length}/500)
                                                <span style={{
                                                    fontSize: '0.75rem',
                                                    color: editedTags.length < 200 ? '#f59e0b' : editedTags.length <= 480 ? '#22c55e' : '#ef4444',
                                                    marginLeft: '0.5rem'
                                                }}>
                                                    {(() => {
                                                        const tagCount = editedTags.split(',').filter(t => t.trim()).length;
                                                        if (editedTags.length < 200) return `📊 ${tagCount} tags — add more for better reach`;
                                                        if (editedTags.length <= 480) return `✅ ${tagCount} tags — great coverage`;
                                                        return `⚠️ ${tagCount} tags — near limit`;
                                                    })()}
                                                </span>
                                            </label>
                                            <textarea
                                                className="form-input"
                                                rows={3}
                                                value={editedTags}
                                                onChange={(e) => setEditedTags(e.target.value.slice(0, 500))}
                                                placeholder="atomic habits summary, james clear books, book review shorts, 60 second book review..."
                                                maxLength={500}
                                            />
                                            <small style={{ color: editedTags.length > 450 ? '#ef4444' : '#666', fontSize: '0.75rem' }}>Comma-separated. Aim for 15-20 long-tail keywords filling 400-500 chars for maximum YouTube discoverability.</small>
                                        </div>
                                    </div>

                                    <div className="info-sidebar">
                                        {/* Book Context Panel (for book reviews) */}
                                        {videoDetail.article?.book_source && (
                                            <div style={{ background: 'linear-gradient(135deg, #fef3c7, #fed7aa)', padding: '1.25rem', borderRadius: '12px', marginBottom: '1rem', border: '1px solid #f59e0b' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                                                    <span style={{ fontSize: '1.2rem' }}>📚</span>
                                                    <h4 style={{ margin: 0, color: '#92400e', fontSize: '0.95rem' }}>Book Review</h4>
                                                </div>
                                                <div style={{ fontSize: '0.85rem', color: '#78350f' }}>
                                                    <p style={{ margin: '0 0 0.4rem 0', fontWeight: '600' }}>
                                                        {videoDetail.article.book_source.title}
                                                    </p>
                                                    {videoDetail.article.book_source.author && (
                                                        <p style={{ margin: '0 0 0.4rem 0' }}>
                                                            ✍️ {videoDetail.article.book_source.author}
                                                        </p>
                                                    )}
                                                    {videoDetail.article.book_source.first_publish_year && (
                                                        <p style={{ margin: '0 0 0.4rem 0', fontSize: '0.8rem', color: '#92400e' }}>
                                                            📅 First published: {videoDetail.article.book_source.first_publish_year}
                                                        </p>
                                                    )}
                                                    {videoDetail.article.book_source.subjects && videoDetail.article.book_source.subjects.length > 0 && (
                                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', margin: '0.5rem 0' }}>
                                                            {videoDetail.article.book_source.subjects.slice(0, 4).map((subj, idx) => (
                                                                <span key={idx} style={{
                                                                    background: '#fbbf24',
                                                                    color: '#78350f',
                                                                    padding: '0.15rem 0.5rem',
                                                                    borderRadius: '12px',
                                                                    fontSize: '0.7rem',
                                                                    fontWeight: '500'
                                                                }}>{subj}</span>
                                                            ))}
                                                        </div>
                                                    )}
                                                    {videoDetail.article.book_source.key_takeaways && videoDetail.article.book_source.key_takeaways.length > 0 && (
                                                        <div style={{ marginTop: '0.6rem', borderTop: '1px solid #fbbf24', paddingTop: '0.5rem' }}>
                                                            <p style={{ margin: '0 0 0.3rem 0', fontWeight: '600', fontSize: '0.8rem' }}>📌 Key Takeaways:</p>
                                                            {videoDetail.article.book_source.key_takeaways.slice(0, 4).map((tk, idx) => (
                                                                <p key={idx} style={{ margin: '0 0 0.25rem 0', fontSize: '0.75rem', lineHeight: '1.3' }}>
                                                                    • {typeof tk === 'object' ? (tk.point || tk.hook || JSON.stringify(tk)) : tk}
                                                                </p>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        )}

                                        {/* Read-only file info */}
                                        <div style={{ background: '#f9fafb', padding: '1.5rem', borderRadius: '12px' }}>
                                            <h4 style={{ marginTop: 0, marginBottom: '1rem' }}>File Info</h4>
                                            {videoDetail.script?.content_type && (
                                                <p style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                                    <strong>Type:</strong>
                                                    <span style={{
                                                        background: videoDetail.script.content_type === 'book_review' ? '#fef3c7' : '#e0f2fe',
                                                        color: videoDetail.script.content_type === 'book_review' ? '#92400e' : '#0369a1',
                                                        padding: '0.15rem 0.5rem',
                                                        borderRadius: '8px',
                                                        fontSize: '0.8rem',
                                                        fontWeight: '500'
                                                    }}>
                                                        {videoDetail.script.content_type === 'book_review' ? '📚 Book Review' :
                                                            videoDetail.script.content_type === 'big_tech' ? '🏢 Big Tech' :
                                                                videoDetail.script.content_type === 'daily_update' ? '📰 Daily Update' :
                                                                    videoDetail.script.content_type}
                                                    </span>
                                                </p>
                                            )}
                                            <p style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                                <strong>Size:</strong> <span>{formatFileSize(videoDetail.video.file_size)}</span>
                                            </p>
                                            <p style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                                <strong>Duration:</strong> <span>{formatDuration(videoDetail.video.duration)}</span>
                                            </p>
                                            <p style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <strong>Date:</strong> <span>{new Date(videoDetail.video.created_at).toLocaleDateString()}</span>
                                            </p>
                                            <hr style={{ margin: '1.5rem 0', border: 'none', borderTop: '1px solid #e5e7eb' }} />
                                            <div style={{ display: 'grid', gap: '0.5rem' }}>
                                                <button onClick={handleDownload} disabled={saving || isRendering(videoDetail.video.status)} className="action-btn btn-secondary" style={{ width: '100%' }}>
                                                    Download MP4
                                                </button>
                                                <button onClick={handleSave} disabled={saving} className="action-btn btn-secondary" style={{ width: '100%' }}>
                                                    {saving ? 'Saving...' : 'Save Metadata'}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="detail-actions">
                                    <button onClick={handleReject} disabled={saving} className="action-btn btn-danger">
                                        Reject Video
                                    </button>
                                    <button onClick={handleApprove} disabled={saving || isRendering(videoDetail.video.status)} className="action-btn btn-primary">
                                        Approve & Publish
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
