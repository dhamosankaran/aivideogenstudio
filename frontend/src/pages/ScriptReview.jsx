import { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { fetchPendingScripts, fetchScriptDetail, updateScriptContent, approveScript, generateVideo, rejectScript, regenerateScript, deleteScript } from '../services/scriptApi';
import './ScriptReview.css';

export default function ScriptReview() {
    const { navigateTo } = useProject();
    const [scripts, setScripts] = useState([]);
    const [selectedScriptId, setSelectedScriptId] = useState(null);
    const [scriptDetail, setScriptDetail] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [saving, setSaving] = useState(false);
    const [generating, setGenerating] = useState(false);

    // Editable fields
    const [editedTitle, setEditedTitle] = useState('');
    const [editedScenes, setEditedScenes] = useState([]);

    useEffect(() => {
        loadPendingScripts();
    }, []);

    const loadPendingScripts = async () => {
        setLoading(true);
        setError(null);

        try {
            const data = await fetchPendingScripts();
            setScripts(data);
        } catch (err) {
            setError(err.message);
            console.error('Failed to load pending scripts:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSelectScript = async (scriptId) => {
        setLoading(true);
        setError(null);
        setSelectedScriptId(scriptId);

        try {
            const data = await fetchScriptDetail(scriptId);
            setScriptDetail(data);
            setEditedTitle(data.catchy_title || data.script.catchy_title || '');
            setEditedScenes(data.script.scenes || []);
        } catch (err) {
            setError(err.message);
            console.error('Failed to load script detail:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (!selectedScriptId) return;

        setSaving(true);
        try {
            await updateScriptContent(selectedScriptId, {
                catchy_title: editedTitle,
                scenes: editedScenes
            });
            alert('Script saved successfully!');
            await handleSelectScript(selectedScriptId);
        } catch (err) {
            alert(`Failed to save: ${err.message}`);
        } finally {
            setSaving(false);
        }
    };

    const handleApprove = async () => {
        if (!selectedScriptId) return;
        if (!confirm('Approve this script? You can then generate the video.')) return;

        setSaving(true);
        try {
            await approveScript(selectedScriptId);
            // Reload detail to show Generate Video button
            await handleSelectScript(selectedScriptId);
            await loadPendingScripts();
            // Show success message inline instead of alert
        } catch (err) {
            alert(`Failed to approve: ${err.message}`);
        } finally {
            setSaving(false);
        }
    };

    const handleGenerateVideo = async () => {
        if (!selectedScriptId) return;
        if (!confirm('Generate video? This will take 3-5 minutes.')) return;

        setGenerating(true);
        try {
            const video = await generateVideo(selectedScriptId);
            alert('Video generation started! You will be redirected to the Video Validation tab.');

            setScriptDetail(null);
            setSelectedScriptId(null);
            await loadPendingScripts();

            navigateTo('videos', { videoId: video.video_id });
        } catch (err) {
            alert(`Failed to generate video: ${err.message}`);
        } finally {
            setGenerating(false);
        }
    };

    const handleReject = async () => {
        if (!selectedScriptId) return;
        const reason = prompt('Reason for rejection:');
        if (!reason) return;

        setSaving(true);
        try {
            await rejectScript(selectedScriptId, reason);
            alert('Script rejected.');
            setScriptDetail(null);
            setSelectedScriptId(null);
            await loadPendingScripts();
        } catch (err) {
            alert(`Failed to reject: ${err.message}`);
        } finally {
            setSaving(false);
        }
    };

    const handleRegenerate = async () => {
        if (!selectedScriptId) return;
        if (!confirm('Regenerate this script? The current version will be discarded.')) return;

        setSaving(true);
        try {
            await regenerateScript(selectedScriptId);
            alert('Script regenerated! Loading new version...');
            await loadPendingScripts();
            setScriptDetail(null);
            setSelectedScriptId(null);
        } catch (err) {
            alert(`Failed to regenerate: ${err.message}`);
        } finally {
            setSaving(false);
        }
    };

    const updateSceneText = (index, newText) => {
        const updated = [...editedScenes];
        updated[index] = { ...updated[index], text: newText };
        setEditedScenes(updated);
    };

    const handleDelete = async (e, scriptId) => {
        e.stopPropagation();
        if (!window.confirm('Delete this script draft permanently?')) return;

        try {
            await deleteScript(scriptId);
            await loadPendingScripts();
            if (selectedScriptId === scriptId) {
                setSelectedScriptId(null);
                setScriptDetail(null);
            }
        } catch (err) {
            alert(`Failed to delete: ${err.message}`);
        }
    };

    return (
        <div className="script-review">
            <header className="script-review-header">
                <div>
                    <h1>Script Review</h1>
                    <p className="subtitle">Craft engaging narratives with AI assistance</p>
                </div>
                <div className="pipeline-steps">
                    <span className="step done">Content Library</span>
                    <span className="arrow">→</span>
                    <span className="step active">Script Review</span>
                    <span className="arrow">→</span>
                    <span className="step">Video Validation</span>
                </div>
            </header>

            {error && <div className="error-message"><strong>Error:</strong> {error}</div>}

            {!selectedScriptId ? (
                // GRID VIEW
                <div className="script-list-view">
                    {loading && scripts.length === 0 ? (
                        <div className="loading-state">
                            <div className="spinner"></div>
                            <p>Loading scripts...</p>
                        </div>
                    ) : scripts.length === 0 ? (
                        <div className="empty-state">
                            <span className="empty-state-illustration">📝</span>
                            <h3>No pending scripts</h3>
                            <p>Generate scripts from the Content Library to review them here.</p>
                        </div>
                    ) : (
                        <div className="scripts-grid">
                            {scripts.map(script => (
                                <div key={script.id} className="script-card" onClick={() => handleSelectScript(script.id)}>
                                    <div className="card-header">
                                        <h3>{script.catchy_title || script.article_title || `Script #${script.id}`}</h3>
                                        <button
                                            className="btn-delete-icon"
                                            onClick={(e) => handleDelete(e, script.id)}
                                            title="Delete Draft"
                                        >✕</button>
                                    </div>
                                    {script.article_title && (
                                        <div className="article-source-title">{script.article_title}</div>
                                    )}
                                    <div className="script-meta">
                                        <span className="duration">⏱ {script.estimated_duration?.toFixed(0)}s</span>
                                        <span className="scenes">🎬 {script.scenes?.length || 0} scenes</span>
                                        <span className="words">📝 {script.word_count} words</span>
                                    </div>
                                    <div className="script-footer">
                                        <span className="created">{new Date(script.created_at).toLocaleDateString()}</span>
                                        <button className="btn-review-sm">Edit Script →</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            ) : (
                // SPLIT DETAIL VIEW
                <div className="detail-container">
                    {/* Sidebar List */}
                    <div className="sidebar-list">
                        {scripts.map(s => (
                            <div
                                key={s.id}
                                className={`sidebar-item ${s.id === selectedScriptId ? 'active' : ''}`}
                                onClick={() => handleSelectScript(s.id)}
                            >
                                <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                                    {s.catchy_title || s.article_title || `Script #${s.id}`}
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#666' }}>
                                    <span>{s.estimated_duration?.toFixed(0)}s</span>
                                    <span style={{
                                        textTransform: 'capitalize',
                                        background: s.script_status === 'approved' ? '#dcfce7' : '#fef3c7',
                                        color: s.script_status === 'approved' ? '#166534' : '#92400e',
                                        padding: '2px 8px',
                                        borderRadius: '4px',
                                        fontWeight: '500'
                                    }}>
                                        {s.script_status === 'approved' ? '✓ Ready' : 'Pending'}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Main Editor */}
                    <div className="main-detail">
                        <div className="detail-header-actions">
                            <button onClick={() => setSelectedScriptId(null)} className="btn-outline" style={{ marginRight: 'auto', border: 'none', background: 'transparent' }}>
                                ← Back to Grid
                            </button>
                        </div>

                        {!scriptDetail ? (
                            <div className="loading-state"><div className="spinner"></div></div>
                        ) : (
                            <div className="editor-split">
                                {/* Left: Article Source */}
                                <div className="article-view">
                                    <h2>📄 Source Article</h2>
                                    {scriptDetail.article && (
                                        <>
                                            <h3 style={{ marginBottom: '1rem' }}>{scriptDetail.article.title}</h3>
                                            <div className="article-content">
                                                {scriptDetail.article.description}
                                            </div>
                                            {scriptDetail.article.key_points && (
                                                <div className="key-points-box">
                                                    <h4>💡 Key Points used for AI generation</h4>
                                                    <ul>
                                                        {scriptDetail.article.key_points.map((point, idx) => (
                                                            <li key={idx}>{point}</li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>

                                {/* Right: Script Editor */}
                                <div className="script-editor-view">
                                    <h2 style={{ justifyContent: 'space-between' }}>
                                        <span>🎬 Script Editor</span>
                                        <span style={{ fontSize: '0.9rem', fontWeight: '400', background: '#f3f4f6', padding: '0.2rem 0.6rem', borderRadius: '6px' }}>
                                            {scriptDetail.script.word_count} words / ~{scriptDetail.script.estimated_duration?.toFixed(0)}s
                                        </span>
                                    </h2>

                                    <div className="editor-field">
                                        <label>Catchy Title</label>
                                        <input
                                            type="text"
                                            className="editor-input"
                                            value={editedTitle}
                                            onChange={(e) => setEditedTitle(e.target.value.slice(0, 60))}
                                            placeholder="Enter click-worthy title..."
                                        />
                                    </div>

                                    <div className="scenes-list">
                                        <label style={{ display: 'block', marginBottom: '1rem', fontWeight: '600' }}>Scene Breakdown</label>
                                        {editedScenes.map((scene, idx) => (
                                            <div key={idx} className="scene-card">
                                                <div className="scene-header">
                                                    <span className="scene-badge">Scene {idx + 1}</span>
                                                    <span className="scene-duration">~{scene.duration || 5}s</span>
                                                </div>
                                                <textarea
                                                    className="editor-textarea"
                                                    rows={4}
                                                    value={scene.text}
                                                    onChange={(e) => updateSceneText(idx, e.target.value)}
                                                />
                                            </div>
                                        ))}
                                    </div>

                                    {/* Generous padding at bottom for sticky action bar */}
                                    <div style={{ height: '100px' }}></div>
                                </div>
                            </div>
                        )}

                        {/* Sticky Action Footer */}
                        {scriptDetail && (
                            <div className="editor-actions">
                                {scriptDetail?.script?.status === 'approved' ? (
                                    /* Approved state - show Generate Video prominently */
                                    <>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#166534', background: '#dcfce7', padding: '8px 16px', borderRadius: '8px' }}>
                                            <span style={{ fontSize: '1.2rem' }}>✓</span>
                                            <span style={{ fontWeight: '600' }}>Script Approved!</span>
                                        </div>
                                        <button
                                            onClick={handleGenerateVideo}
                                            disabled={saving || generating}
                                            className="action-btn btn-primary"
                                            style={{ background: 'linear-gradient(135deg, #8b5cf6, #6366f1)', fontSize: '1.1rem', padding: '12px 32px' }}
                                        >
                                            {generating ? '⏳ Generating Video...' : '🎬 Generate Video'}
                                        </button>
                                    </>
                                ) : (
                                    /* Pending state - show review actions */
                                    <>
                                        <button onClick={handleReject} disabled={saving || generating} className="action-btn btn-danger-ghost">
                                            Reject Draft
                                        </button>
                                        <div style={{ display: 'flex', gap: '1rem' }}>
                                            <button onClick={handleRegenerate} disabled={saving || generating} className="action-btn btn-outline">
                                                Regenerate
                                            </button>
                                            <button onClick={handleSave} disabled={saving || generating} className="action-btn btn-outline">
                                                Save Draft
                                            </button>
                                            <button onClick={handleApprove} disabled={saving || generating} className="action-btn btn-primary">
                                                ✓ Approve Script
                                            </button>
                                        </div>
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
