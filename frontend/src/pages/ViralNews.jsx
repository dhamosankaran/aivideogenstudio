import { useState, useEffect, useCallback } from 'react';
import { useAppNavigate } from '../context/ProjectContext';
import {
    discoverTrending,
    saveSource,
    analyzeSource,
    generateViralNewsScript,
    generateViralNewsVideo,
    getVoiceOptions,
    listSources,
} from '../services/viralNewsApi';
import './ViralNews.css';

const CATEGORIES = ['All', '🌍 World', '🇨🇳 China', 'Technology', 'Business', 'Politics', 'Science', 'Health', 'Entertainment', 'Elon Musk', 'Humanoid'];

// Convert a display category label (may include emoji) to a backend-safe slug.
// e.g. '🌍 World' → 'world', 'Elon Musk' → 'elon_musk'
const toCategorySlug = (label) =>
    label
        .split('')
        .filter(c => c.codePointAt(0) < 128)   // strip emoji / non-ASCII
        .join('')
        .trim()
        .toLowerCase()
        .replace(/\s+/g, '_');

const VIDEO_DURATIONS = [
    { id: '60s', label: '60 Seconds', desc: 'Short · Reels / TikTok', badge: null },
    { id: '120s', label: '2 Minutes', desc: 'YouTube Shorts · full story', badge: 'Recommended' },
    { id: '300s', label: '5 Minutes', desc: 'Regular video · deep dive', badge: null },
];

const BACKGROUND_MODES = [
    { id: 'auto', label: '✨ Auto Mix', desc: 'Smart mix: videos → images → gradient fallback', badge: 'Recommended' },
    { id: 'images_only', label: '🖼️ Images Only', desc: 'Per-scene stock images with Ken Burns effect', badge: null },
    { id: 'videos_only', label: '🎬 Videos Only', desc: 'Pexels stock videos for all scenes', badge: null },
];

const IMAGE_SOURCES = [
    { id: 'stock', label: 'Stock (Pexels + Google)', desc: 'Free stock photo search' },
    { id: 'ai_generated', label: 'AI Generated', desc: 'Gemini image generation (beta)' },
];

const VIDEO_SOURCES = [
    { id: 'stock', label: 'Stock Videos (Pexels)', desc: 'Free stock video library' },
    { id: 'veo', label: 'Gemini Veo (Beta)', desc: 'AI-generated 8s cinematic clips (~1min/scene)' },
];

function sceneTag(sceneNumber, totalScenes) {
    if (sceneNumber === 1) return 'hook';
    if (sceneNumber === totalScenes) return totalScenes > 2 ? 'cta' : 'impact';
    return 'impact';
}

function ViralNews() {
    const { navigateTo } = useAppNavigate();

    // ── Discovery state ──────────────────────────────────────
    const [activeCategory, setActiveCategory] = useState('All');
    const [searchQuery, setSearchQuery] = useState('');
    const [trending, setTrending] = useState([]);
    const [isLoadingTrending, setIsLoadingTrending] = useState(false);

    // ── Saved sources (library) ───────────────────────────────
    const [library, setLibrary] = useState([]);

    // ── Selected article / source ──────────────────────────────
    const [selectedArticle, setSelectedArticle] = useState(null); // raw trending article
    const [savedSource, setSavedSource] = useState(null);         // ViralNewsSource after save
    const [isSaving, setIsSaving] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    // Selected angle index
    const [selectedAngle, setSelectedAngle] = useState(0);

    // ── Script preview state ───────────────────────────────────
    const [isGeneratingScript, setIsGeneratingScript] = useState(false);
    const [scriptPreview, setScriptPreview] = useState(null);
    const [scriptAccepted, setScriptAccepted] = useState(false);
    const [showScriptView, setShowScriptView] = useState(false);

    // ── TTS / video options ────────────────────────────────────
    const [voiceOptions, setVoiceOptions] = useState(null);
    const [selectedProvider, setSelectedProvider] = useState('openai');
    const [selectedVoice, setSelectedVoice] = useState(null);
    const [backgroundMode, setBackgroundMode] = useState('auto');
    const [imageSource, setImageSource] = useState('stock');
    const [videoSource, setVideoSource] = useState('stock');
    const [videoDuration, setVideoDuration] = useState('120s');

    // ── Video generation ───────────────────────────────────────
    const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
    const [generationStep, setGenerationStep] = useState('');

    // ── UI feedback ─────────────────────────────────────────────
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    // ── Init ─────────────────────────────────────────────────────
    useEffect(() => {
        handleRefresh();
        loadLibrary();
        loadVoiceOptions();
    }, []);

    useEffect(() => {
        if (voiceOptions) {
            const p = voiceOptions.providers?.find(p => p.id === selectedProvider);
            if (p) setSelectedVoice(p.default_voice || null);
        }
    }, [selectedProvider, voiceOptions]);

    // ── Data loading ──────────────────────────────────────────────
    const handleRefresh = useCallback(async (category = activeCategory, query = '') => {
        setIsLoadingTrending(true);
        setError(null);
        try {
            const cat = category === 'All' ? null : toCategorySlug(category);
            const data = await discoverTrending(cat, query || null, 15);
            setTrending(data.articles || []);
        } catch (e) {
            setError('Failed to load trending news: ' + e.message);
        } finally {
            setIsLoadingTrending(false);
        }
    }, [activeCategory]);

    const loadLibrary = async () => {
        try {
            const data = await listSources(50);
            setLibrary(data);
        } catch (_) { }
    };

    const loadVoiceOptions = async () => {
        try {
            const opts = await getVoiceOptions('viral_news');
            setVoiceOptions(opts);
            setSelectedProvider(opts.default_provider || 'openai');
        } catch (_) { }
    };

    // ── Category tab change ────────────────────────────────────────
    const handleCategoryChange = (cat) => {
        setActiveCategory(cat);
        handleRefresh(cat, searchQuery);
    };

    // ── Search ─────────────────────────────────────────────────────
    const handleSearch = () => {
        handleRefresh(activeCategory, searchQuery);
    };

    // ── Select article from trending list ──────────────────────────
    const handleSelectArticle = (article) => {
        setSelectedArticle(article);
        setSavedSource(null);
        setScriptPreview(null);
        setScriptAccepted(false);
        setShowScriptView(false);
        setError(null);
        setSuccess(null);
        setSelectedAngle(0);

        // Check if already in library
        const existing = library.find(s => s.original_url === article.url);
        if (existing) setSavedSource(existing);
    };

    // ── Select from library ─────────────────────────────────────────
    const handleSelectFromLibrary = (source) => {
        setSavedSource(source);
        setSelectedArticle({ title: source.title, url: source.original_url, source_name: source.source_name, description: source.description, image_url: source.image_url, category: source.news_category });
        setScriptPreview(null);
        setScriptAccepted(false);
        setShowScriptView(false);
        setError(null);
        setSuccess(null);
        setSelectedAngle(0);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // ── Analyze virality ────────────────────────────────────────────
    const handleAnalyze = async () => {
        if (!selectedArticle) return;
        setIsSaving(true);
        setError(null);

        let source = savedSource;
        try {
            // Save source first if not saved
            if (!source) {
                source = await saveSource(selectedArticle);
                setSavedSource(source);
                setIsSaving(false);
            }
        } catch (e) {
            setError('Failed to save source: ' + e.message);
            setIsSaving(false);
            return;
        }

        setIsAnalyzing(true);
        try {
            const analyzed = await analyzeSource(source.id);
            setSavedSource(analyzed);
            setSuccess('Virality analysis complete!');
            loadLibrary();
        } catch (e) {
            setError('Analysis failed: ' + e.message);
        } finally {
            setIsAnalyzing(false);
        }
    };

    // ── Generate Script ─────────────────────────────────────────────
    const handleGenerateScript = async () => {
        if (!savedSource) return;
        setIsGeneratingScript(true);
        setError(null);
        setScriptPreview(null);
        setScriptAccepted(false);

        try {
            const result = await generateViralNewsScript(savedSource.id, selectedAngle, null, videoDuration);
            setScriptPreview(result);
            setShowScriptView(true);
            setSuccess('Script ready for review!');
        } catch (e) {
            setError('Script generation failed: ' + e.message);
        } finally {
            setIsGeneratingScript(false);
        }
    };

    // ── Generate Video ──────────────────────────────────────────────
    const handleGenerateVideo = async () => {
        if (!savedSource) return;
        setIsGeneratingVideo(true);
        setError(null);
        setGenerationStep('Generating audio...');

        try {
            const result = await generateViralNewsVideo(
                savedSource.id,
                selectedAngle,
                null,
                scriptPreview?.script_id || null,
                selectedProvider,
                selectedVoice,
                backgroundMode,
                imageSource,
                videoSource,
                videoDuration,
            );
            setGenerationStep('Video rendering in background...');
            setSuccess(`🎬 ${result.message}`);
            setTimeout(() => navigateTo('videos'), 2500);
        } catch (e) {
            setError('Video generation failed: ' + e.message);
        } finally {
            setIsGeneratingVideo(false);
            setGenerationStep('');
        }
    };

    // ── Helpers ─────────────────────────────────────────────────────
    const formatDate = (dateStr) => {
        if (!dateStr) return null;
        try {
            const d = new Date(dateStr);
            const now = new Date();
            const diffH = Math.round((now - d) / 3600000);
            if (diffH < 24) return `${diffH}h ago`;
            return `${Math.round(diffH / 24)}d ago`;
        } catch (_) { return null; }
    };

    const analysisReady = savedSource?.analysis_status === 'completed';
    const angles = savedSource?.suggested_angles || [];

    // ═══════════════════════════════════════
    // RENDER
    // ═══════════════════════════════════════
    return (
        <div className="vn-root">
            {/* ── Header ── */}
            <div className="vn-header">
                <h1><span className="vn-title-icon">🔥</span> Viral News Studio</h1>
                <button className="vn-btn-refresh" onClick={() => handleRefresh(activeCategory, searchQuery)} disabled={isLoadingTrending}>
                    {isLoadingTrending ? <span className="vn-spinner" /> : '↻'} Refresh Trending
                </button>
            </div>

            {/* ── Feedback banners ── */}
            {error && <div className="vn-error">⚠️ {error}</div>}
            {success && <div className="vn-success">✅ {success}</div>}

            {/* ── Category tabs ── */}
            <div className="vn-tabs">
                {CATEGORIES.map(cat => (
                    <button key={cat} className={`vn-tab ${activeCategory === cat ? 'active' : ''}`} onClick={() => handleCategoryChange(cat)}>
                        {cat}
                    </button>
                ))}
            </div>

            {/* ── Search row ── */}
            <div className="vn-search-row">
                <div className="vn-search-wrap">
                    <svg className="vn-search-icon" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" /></svg>
                    <input
                        type="text"
                        className="vn-search-input"
                        placeholder="Search trending topics, events, or people..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleSearch()}
                    />
                </div>
                <button className="vn-btn-search" onClick={handleSearch}>Search</button>
            </div>

            {/* ════════════════════════════════════
          SCRIPT VIEW (full-width 2-col)
      ════════════════════════════════════ */}
            {showScriptView && scriptPreview ? (
                <div className="vn-script-view">
                    {/* Left – Script scenes */}
                    <div className="vn-script-left">
                        <div className="vn-script-header">
                            <div className="vn-script-label">Script Preview</div>
                            <div className="vn-script-title">{scriptPreview.catchy_title}</div>
                            <div className="vn-script-meta">
                                <span className="vn-meta-badge">🎬 {(scriptPreview.scenes || []).length} scenes</span>
                                <span className="vn-meta-badge">📊 {scriptPreview.word_count} words</span>
                                <span className="vn-meta-badge">⏱️ ~{Math.round(scriptPreview.estimated_duration)}s</span>
                                <span className={scriptPreview.is_valid ? 'vn-meta-valid' : 'vn-meta-invalid'}>
                                    {scriptPreview.is_valid ? '✅ Valid' : '⚠️ Issues'}
                                </span>
                            </div>
                        </div>

                        {/* Validation warnings */}
                        {scriptPreview.validation_errors?.length > 0 && (
                            <div className="vn-validation-warns">
                                {scriptPreview.validation_errors.map((w, i) => <div key={i} className="vn-warn">⚠️ {w}</div>)}
                            </div>
                        )}

                        {/* Scene cards */}
                        <div className="vn-scenes-list">
                            {(scriptPreview.scenes || []).map((scene, i) => {
                                const total = (scriptPreview.scenes || []).length;
                                const tag = sceneTag(scene.scene_number, total);
                                const dur = scene.text ? Math.round(scene.text.split(' ').length / 2.5) : null;
                                return (
                                    <div key={i} className="vn-scene">
                                        <div className="vn-scene-head">
                                            <span className={`vn-scene-tag ${tag}`}>
                                                {tag === 'hook' ? '🔥 Hook' : tag === 'cta' ? '📣 CTA' : '⚡ Impact'}
                                            </span>
                                            {dur && <span className="vn-scene-dur">⏱ {dur}s</span>}
                                        </div>
                                        <div className="vn-scene-text">{scene.text}</div>
                                        {scene.image_keywords?.length > 0 && (
                                            <div className="vn-scene-kws">
                                                {scene.image_keywords.map((kw, j) => <span key={j} className="vn-kw">{kw}</span>)}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        <div className="vn-script-footer">
                            <span className="vn-footer-stat">📊 Total: {scriptPreview.word_count} words</span>
                            <span className="vn-footer-stat">⏱️ Est. Duration: {Math.round(scriptPreview.estimated_duration)}s</span>
                        </div>

                        {/* Script action buttons */}
                        <div className="vn-divider" />
                        <div className="vn-actions">
                            <button className="vn-btn-generate-script" onClick={() => setScriptAccepted(true)} disabled={scriptAccepted} style={scriptAccepted ? { background: 'rgba(34,197,94,0.2)', color: '#4ade80', cursor: 'default' } : {}}>
                                {scriptAccepted ? '✅ Script Accepted' : '✅ Accept Script'}
                            </button>
                            <button className="vn-btn-regen" onClick={handleGenerateScript} disabled={isGeneratingScript}>
                                {isGeneratingScript ? <><span className="vn-spinner" /> Regenerating...</> : '🔄 Regenerate Script'}
                            </button>
                            <button className="vn-btn-back" onClick={() => { setShowScriptView(false); setScriptAccepted(false); }}>
                                ← Back to Analysis
                            </button>
                        </div>
                    </div>

                    {/* Right – VIDEO OPTIONS panel */}
                    <div className="vn-video-options">
                        <div className="vn-vo-title">Video Options</div>

                        {/* Video Duration */}
                        <label className="vn-vo-label">Video Duration</label>
                        <div className="vn-tts-grid vn-duration-grid">
                            {VIDEO_DURATIONS.map(d => (
                                <label key={d.id} className={`vn-tts-card ${videoDuration === d.id ? 'selected' : ''}`}>
                                    <input type="radio" name="duration" value={d.id} checked={videoDuration === d.id} onChange={() => setVideoDuration(d.id)} />
                                    <div className="vn-tts-text">
                                        <span className="vn-tts-name">{d.label}</span>
                                        <span className="vn-tts-cost">{d.desc}</span>
                                    </div>
                                    {d.badge && <span className="vn-tts-rec">{d.badge}</span>}
                                </label>
                            ))}
                        </div>
                        <div className="vn-duration-hint">Changing duration requires regenerating the script</div>

                        {/* TTS Provider */}
                        <label className="vn-vo-label">TTS Provider</label>
                        <div className="vn-tts-grid">
                            {(voiceOptions?.providers || [
                                { id: 'openai', name: 'OpenAI', cost_label: '~$0.02/video', default_voice: 'onyx' },
                                { id: 'google', name: 'Google TTS', cost_label: 'Free tier', default_voice: 'en-US-Studio-Q' },
                                { id: 'elevenlabs', name: 'ElevenLabs', cost_label: '~$0.04/video', default_voice: null },
                            ]).map(p => (
                                <label key={p.id} className={`vn-tts-card ${selectedProvider === p.id ? 'selected' : ''}`}>
                                    <input type="radio" name="tts" value={p.id} checked={selectedProvider === p.id} onChange={() => setSelectedProvider(p.id)} />
                                    <div className="vn-tts-text">
                                        <span className="vn-tts-name">{p.name}</span>
                                        <span className="vn-tts-cost">{p.cost_label}</span>
                                    </div>
                                    {(voiceOptions?.default_provider || 'openai') === p.id && <span className="vn-tts-rec">✨</span>}
                                </label>
                            ))}
                        </div>

                        {/* Voice */}
                        <label className="vn-vo-label">Voice</label>
                        <div className="vn-voice-wrap">
                            <select className="vn-select" value={selectedVoice || ''} onChange={e => setSelectedVoice(e.target.value)}>
                                {(voiceOptions?.voices?.[selectedProvider] || [
                                    { id: 'onyx', name: 'Onyx', tone: 'Deep, authoritative' },
                                    { id: 'nova', name: 'Nova', tone: 'Bright, energetic' },
                                    { id: 'alloy', name: 'Alloy', tone: 'Neutral, clear' },
                                    { id: 'echo', name: 'Echo', tone: 'Smooth, confident' },
                                    { id: 'fable', name: 'Fable', tone: 'Warm, storytelling' },
                                    { id: 'shimmer', name: 'Shimmer', tone: 'Soft, professional' },
                                ]).map(v => (
                                    <option key={v.id} value={v.id}>{v.name} — {v.tone}</option>
                                ))}
                            </select>
                            {voiceOptions?.voices?.[selectedProvider] && (
                                <div className="vn-voice-hint">
                                    {voiceOptions.voices[selectedProvider].find(v => v.id === selectedVoice)?.tone || ''}
                                </div>
                            )}
                        </div>

                        {/* Background Mode */}
                        <label className="vn-vo-label">Background mode</label>
                        <div className="vn-tts-grid">
                            {BACKGROUND_MODES.map(m => (
                                <label key={m.id} className={`vn-tts-card ${backgroundMode === m.id ? 'selected' : ''}`}>
                                    <input type="radio" name="bg" value={m.id} checked={backgroundMode === m.id} onChange={() => setBackgroundMode(m.id)} />
                                    <div className="vn-tts-text">
                                        <span className="vn-tts-name">{m.label}</span>
                                        <span className="vn-tts-cost">{m.desc}</span>
                                    </div>
                                    {m.badge && <span className="vn-tts-rec">{m.badge}</span>}
                                </label>
                            ))}
                        </div>

                        {/* Image Source */}
                        <label className="vn-vo-label">Image source</label>
                        <div className="vn-tts-grid">
                            {IMAGE_SOURCES.map(s => (
                                <label key={s.id} className={`vn-tts-card ${imageSource === s.id ? 'selected' : ''}`}>
                                    <input type="radio" name="img-src" value={s.id} checked={imageSource === s.id} onChange={() => setImageSource(s.id)} />
                                    <div className="vn-tts-text">
                                        <span className="vn-tts-name">{s.label}</span>
                                        <span className="vn-tts-cost">{s.desc}</span>
                                    </div>
                                    {s.id === 'ai_generated' && <span className="vn-tts-rec">Beta</span>}
                                </label>
                            ))}
                        </div>

                        {/* Video Source */}
                        <label className="vn-vo-label">Video source</label>
                        <div className="vn-tts-grid">
                            {VIDEO_SOURCES.map(s => (
                                <label key={s.id} className={`vn-tts-card ${videoSource === s.id ? 'selected' : ''}`}>
                                    <input type="radio" name="vid-src" value={s.id} checked={videoSource === s.id} onChange={() => setVideoSource(s.id)} />
                                    <div className="vn-tts-text">
                                        <span className="vn-tts-name">{s.label}</span>
                                        <span className="vn-tts-cost">{s.desc}</span>
                                    </div>
                                    {s.id === 'veo' && <span className="vn-tts-rec">Beta</span>}
                                </label>
                            ))}
                        </div>

                        {/* Cost estimate */}
                        <div className="vn-cost-row">
                            <span className="vn-cost-label">Estimated cost</span>
                            <span className="vn-cost-val">
                                {selectedProvider === 'openai' ? '~$0.03' : selectedProvider === 'elevenlabs' ? '~$0.05' : '~$0.01'}
                            </span>
                        </div>

                        {/* Approve & Generate Video */}
                        <button
                            className="vn-btn-generate-video"
                            onClick={handleGenerateVideo}
                            disabled={!scriptAccepted || isGeneratingVideo}
                        >
                            {isGeneratingVideo ? (
                                <><span className="vn-spinner" />{generationStep || 'Processing...'}</>
                            ) : (
                                <>🚀 Approve &amp; Generate Video</>
                            )}
                        </button>

                        {!scriptAccepted && (
                            <div style={{ textAlign: 'center', fontSize: '0.72rem', color: '#666', marginTop: '0.5rem' }}>
                                Accept the script first to unlock video generation
                            </div>
                        )}

                        {isGeneratingVideo && (
                            <div className="vn-progress-steps">
                                <span className="vn-step active">🔊 Audio</span>
                                <span className="vn-step-arrow">→</span>
                                <span className={`vn-step ${generationStep.includes('render') ? 'active' : ''}`}>🎬 Video</span>
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                /* ════════════════════════════════════
                   DEFAULT VIEW: Trending | Analysis
                ════════════════════════════════════ */
                <div className="vn-grid">
                    {/* ── Left: Trending articles ── */}
                    <div className="vn-trending-panel">
                        <div className="vn-section-title">Trending Now</div>

                        {isLoadingTrending && (
                            <div className="vn-empty">
                                <div className="vn-empty-icon">⏳</div>
                                <p>Fetching trending news...</p>
                            </div>
                        )}

                        {!isLoadingTrending && trending.length === 0 && (
                            <div className="vn-empty">
                                <div className="vn-empty-icon">📰</div>
                                <p>No articles found.<br />Try a different category or refresh.</p>
                            </div>
                        )}

                        {!isLoadingTrending && trending.map((article, i) => (
                            <div
                                key={i}
                                className={`vn-card ${selectedArticle?.url === article.url ? 'selected' : ''}`}
                                onClick={() => handleSelectArticle(article)}
                            >
                                {/* Virality badge if saved & analyzed */}
                                {library.find(s => s.original_url === article.url && s.virality_score)?.virality_score && (
                                    <div className="vn-vbadge">
                                        🔥 {library.find(s => s.original_url === article.url).virality_score.toFixed(1)}
                                    </div>
                                )}

                                {article.image_url
                                    ? <img src={article.image_url} alt="" className="vn-thumb" />
                                    : <div className="vn-thumb-placeholder">📰</div>
                                }

                                <div className="vn-card-body">
                                    <div className="vn-card-title">{article.title}</div>
                                    <div className="vn-card-meta">
                                        <span className="vn-card-source">{article.source_name}</span>
                                        {article.published_at && <><span className="vn-card-dot">•</span><span>{formatDate(article.published_at)}</span></>}
                                    </div>
                                    {article.category && <div className="vn-cat-pill">{article.category}</div>}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* ── Right: Analysis panel ── */}
                    <div className="vn-analysis-panel">
                        {!selectedArticle ? (
                            <div className="vn-panel-empty">
                                <div className="vn-empty-icon">🔥</div>
                                <p>Select an article from the trending list to analyze its viral potential and generate a short video.</p>
                            </div>
                        ) : (
                            <>
                                <div className="vn-analysis-label">Analysis</div>
                                <div className="vn-analysis-title">{selectedArticle.title}</div>
                                <div className="vn-analysis-source">
                                    {selectedArticle.source_name || 'Unknown'}
                                    {selectedArticle.published_at && ` • ${formatDate(selectedArticle.published_at)}`}
                                </div>

                                {selectedArticle.description && (
                                    <div className="vn-desc-text">{selectedArticle.description}</div>
                                )}

                                {/* Virality score */}
                                {analysisReady && savedSource.virality_score && (
                                    <>
                                        <div className="vn-score-row">
                                            <span className="vn-score-label">🔥 Virality Score</span>
                                            <span className="vn-score-value">{savedSource.virality_score.toFixed(1)}/10</span>
                                        </div>
                                        <div className="vn-score-bar">
                                            <div className="vn-score-fill" style={{ width: `${savedSource.virality_score * 10}%` }} />
                                        </div>
                                    </>
                                )}

                                {/* Why It's Viral */}
                                {analysisReady && savedSource.virality_reasons?.length > 0 && (
                                    <div className="vn-info-block">
                                        <h3>💡 Why It&apos;s Viral</h3>
                                        <ul>{savedSource.virality_reasons.slice(0, 4).map((r, i) => <li key={i}>{r}</li>)}</ul>
                                    </div>
                                )}

                                {/* Video Angles */}
                                {analysisReady && angles.length > 0 && (
                                    <div className="vn-info-block">
                                        <h3>🎬 Suggested Video Angles</h3>
                                        <div className="vn-angles-grid">
                                            {angles.map((angle, i) => (
                                                <button
                                                    key={i}
                                                    className={`vn-angle-pill ${selectedAngle === i ? 'selected' : ''}`}
                                                    onClick={() => setSelectedAngle(i)}
                                                >
                                                    {angle}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Key Facts */}
                                {analysisReady && savedSource.key_facts?.length > 0 && (
                                    <div className="vn-info-block">
                                        <h3>📌 Key Facts</h3>
                                        <ul>{savedSource.key_facts.slice(0, 5).map((f, i) => <li key={i}>{f}</li>)}</ul>
                                    </div>
                                )}

                                {/* Emotional hook / audience */}
                                {analysisReady && (savedSource.emotional_hook || savedSource.target_audience) && (
                                    <div className="vn-info-block">
                                        {savedSource.emotional_hook && (
                                            <><h3>❤️ Emotional Hook</h3><ul><li>{savedSource.emotional_hook}</li></ul></>
                                        )}
                                        {savedSource.target_audience && (
                                            <><h3 style={{ marginTop: '0.5rem' }}>👥 Target Audience</h3><ul><li>{savedSource.target_audience}</li></ul></>
                                        )}
                                    </div>
                                )}

                                <div className="vn-divider" />

                                {/* Action buttons */}
                                <div className="vn-actions">
                                    {/* Not yet analyzed */}
                                    {(!savedSource || savedSource.analysis_status === 'pending') && (
                                        <button className="vn-btn-analyze" onClick={handleAnalyze} disabled={isAnalyzing || isSaving}>
                                            {(isAnalyzing || isSaving) ? <><span className="vn-spinner" />Analyzing...</> : '🔥 Analyze Virality'}
                                        </button>
                                    )}

                                    {/* Analyzing in progress */}
                                    {savedSource?.analysis_status === 'analyzing' && (
                                        <button className="vn-btn-analyze" disabled>
                                            <span className="vn-spinner" /> Analyzing with AI...
                                        </button>
                                    )}

                                    {/* Failed – retry */}
                                    {savedSource?.analysis_status === 'failed' && (
                                        <>
                                            <div className="vn-error">Analysis failed: {savedSource.error_message}</div>
                                            <button className="vn-btn-analyze" onClick={handleAnalyze} disabled={isAnalyzing}>
                                                🔄 Retry Analysis
                                            </button>
                                        </>
                                    )}

                                    {/* Duration selector — shown when analysis is complete */}
                                    {analysisReady && (
                                        <div className="vn-duration-selector">
                                            <div className="vn-duration-label">Video Duration</div>
                                            <div className="vn-duration-pills">
                                                {VIDEO_DURATIONS.map(d => (
                                                    <button
                                                        key={d.id}
                                                        className={`vn-duration-pill ${videoDuration === d.id ? 'selected' : ''}`}
                                                        onClick={() => setVideoDuration(d.id)}
                                                    >
                                                        {d.label}
                                                        {d.badge && <span className="vn-duration-badge">{d.badge}</span>}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Analysis complete */}
                                    {analysisReady && (
                                        <>
                                            <button className="vn-btn-generate-script" onClick={handleGenerateScript} disabled={isGeneratingScript}>
                                                {isGeneratingScript ? <><span className="vn-spinner" />Generating Script...</> : '📝 Generate Script ▶'}
                                            </button>
                                            <button className="vn-btn-generate-video" onClick={async () => {
                                                // One-click flow without script review
                                                setIsGeneratingVideo(true);
                                                setError(null);
                                                setGenerationStep('Generating audio...');
                                                try {
                                                    const result = await generateViralNewsVideo(savedSource.id, selectedAngle, null, null, selectedProvider, selectedVoice, backgroundMode, imageSource, videoSource, videoDuration);
                                                    setSuccess(`🎬 ${result.message}`);
                                                    setTimeout(() => navigateTo('videos'), 2500);
                                                } catch (e) {
                                                    setError('Video generation failed: ' + e.message);
                                                } finally {
                                                    setIsGeneratingVideo(false);
                                                    setGenerationStep('');
                                                }
                                            }} disabled={isGeneratingVideo}>
                                                {isGeneratingVideo ? <><span className="vn-spinner" />{generationStep}</> : '🎬 Generate Video 🚀'}
                                            </button>
                                        </>
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* ── My Library Table ── */}
            {library.length > 0 && !showScriptView && (
                <div className="vn-library">
                    <div className="vn-library-title">📚 My Library</div>
                    <table className="vn-table">
                        <thead>
                            <tr>
                                <th>Source</th>
                                <th>Category</th>
                                <th>Status</th>
                                <th>Virality</th>
                            </tr>
                        </thead>
                        <tbody>
                            {library.map(source => (
                                <tr key={source.id} onClick={() => handleSelectFromLibrary(source)}>
                                    <td style={{ maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {source.title}
                                    </td>
                                    <td>{source.news_category || '—'}</td>
                                    <td>
                                        <span className={`vn-status-pill ${source.analysis_status}`}>
                                            {source.analysis_status}
                                        </span>
                                    </td>
                                    <td>
                                        {source.virality_score
                                            ? <span className="vn-score-chip">🔥 {source.virality_score.toFixed(1)}</span>
                                            : '—'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

export default ViralNews;
