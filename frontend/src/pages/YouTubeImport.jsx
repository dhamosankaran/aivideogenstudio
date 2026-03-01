import { useState, useEffect, useCallback, useRef } from 'react';
import { useAppNavigate } from '../context/ProjectContext';
import {
    analyzeYouTubeVideo,
    getYouTubeSources,
    getYouTubeSource,
    getVideoSummary,
    getVideoInfo,
    downloadVideo,
    getTranscript,
    getMusicLibrary,
    editorGenerate,
    generateScript,
    approveAndRender,
    generateModeA,
    generateModeB,
    trimAndGenerate
} from '../services/youtubeApi';
import './YouTubeImport.css';

// ── Wizard Step Constants ──────────────────────────────────────
const STEPS = {
    URL_INPUT: 0,
    VIDEO_OVERVIEW: 1,
    EDITOR: 2,
    MUSIC_CAPTIONS: 3,
    GENERATE: 4,
};

const STEP_LABELS = [
    'Import',
    'Overview',
    'Editor',
    'Audio & Captions',
    'Generate',
];

// ── Platform Icons ─────────────────────────────────────────────
const PLATFORM_ICONS = {
    youtube: '🔴',
    twitter: '🐦',
    linkedin: '💼',
    unknown: '🔗',
};

function YouTubeImport() {
    const { navigateTo } = useAppNavigate();

    // ── Wizard state ───────────────────────────────────────────
    const [currentStep, setCurrentStep] = useState(STEPS.URL_INPUT);

    // ── Step 1: URL Input state ────────────────────────────────
    const [videoUrl, setVideoUrl] = useState('');
    const [detectedPlatform, setDetectedPlatform] = useState(null);
    const [isDownloading, setIsDownloading] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [sources, setSources] = useState([]);

    // ── Step 2: Overview state ─────────────────────────────────
    const [selectedSource, setSelectedSource] = useState(null);
    const [videoSummary, setVideoSummary] = useState(null);
    const [isLoadingSummary, setIsLoadingSummary] = useState(false);
    const [transcript, setTranscript] = useState(null);
    const [isLoadingTranscript, setIsLoadingTranscript] = useState(false);

    // ── Step 3: Editor state ───────────────────────────────────
    const [trimStart, setTrimStart] = useState(0);
    const [trimEnd, setTrimEnd] = useState(60);
    const [stripAudio, setStripAudio] = useState(true);

    // ── Step 4: Music & Captions state ─────────────────────────
    const [musicLibrary, setMusicLibrary] = useState([]);
    const [selectedMusic, setSelectedMusic] = useState(null);
    const [musicVolume, setMusicVolume] = useState(0.12);
    const [captionSource, setCaptionSource] = useState('transcript');

    // ── Step 5: Generate state ─────────────────────────────────
    const [commentaryStyle, setCommentaryStyle] = useState('reaction');
    const [contentType, setContentType] = useState('youtube_import');
    const [isGenerating, setIsGenerating] = useState(false);
    const [isApproving, setIsApproving] = useState(false);
    const [generationResult, setGenerationResult] = useState(null);
    const [scriptPreview, setScriptPreview] = useState(null);

    // ── Shared state ───────────────────────────────────────────
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);
    const [pollingId, setPollingId] = useState(null);

    // ── Refs ────────────────────────────────────────────────────
    const timelineRef = useRef(null);
    const playerRef = useRef(null);
    const seekTimerRef = useRef(null);

    // ── Effects ────────────────────────────────────────────────
    useEffect(() => { loadSources(); }, []);
    useEffect(() => () => { if (pollingId) clearInterval(pollingId); }, [pollingId]);

    // Auto-detect platform as user types URL
    useEffect(() => {
        if (!videoUrl.trim()) {
            setDetectedPlatform(null);
            return;
        }
        if (/youtube\.com|youtu\.be/i.test(videoUrl)) setDetectedPlatform('youtube');
        else if (/twitter\.com|x\.com/i.test(videoUrl)) setDetectedPlatform('twitter');
        else if (/linkedin\.com/i.test(videoUrl)) setDetectedPlatform('linkedin');
        else setDetectedPlatform('unknown');
    }, [videoUrl]);

    // ── Data loaders ───────────────────────────────────────────

    const loadSources = async () => {
        try {
            const data = await getYouTubeSources(20);
            setSources(data);
        } catch (err) {
            console.error('Failed to load sources:', err);
        }
    };

    const loadTranscript = useCallback(async (sourceId) => {
        setIsLoadingTranscript(true);
        try {
            const data = await getTranscript(sourceId);
            setTranscript(data);
        } catch (err) {
            console.error('Transcript load failed:', err);
            setTranscript(null);
        } finally {
            setIsLoadingTranscript(false);
        }
    }, []);

    const loadSummary = useCallback(async (sourceId) => {
        setIsLoadingSummary(true);
        try {
            const data = await getVideoSummary(sourceId);
            setVideoSummary(data);
        } catch (err) {
            console.error('Summary load failed:', err);
        } finally {
            setIsLoadingSummary(false);
        }
    }, []);

    const loadMusicLibrary = useCallback(async () => {
        try {
            const data = await getMusicLibrary();
            setMusicLibrary(data.tracks || []);
            if (data.tracks?.length > 0 && !selectedMusic) {
                setSelectedMusic(data.tracks[0].filename);
            }
        } catch (err) {
            console.error('Music library load failed:', err);
        }
    }, [selectedMusic]);

    // ── Polling ────────────────────────────────────────────────

    const startPolling = (sourceId) => {
        if (pollingId) clearInterval(pollingId);
        const id = setInterval(async () => {
            try {
                const source = await getYouTubeSource(sourceId);
                setSelectedSource(source);
                if (source.analysis_status === 'completed' || source.analysis_status === 'failed') {
                    clearInterval(id);
                    setPollingId(null);
                    loadSources();
                    if (source.analysis_status === 'completed') {
                        setTrimEnd(Math.min(source.duration_seconds || 60, 60));
                        // Auto-load summary and transcript when analysis completes
                        loadSummary(source.id);
                        loadTranscript(source.id);
                    }
                }
            } catch (err) {
                clearInterval(id);
                setPollingId(null);
            }
        }, 2000);
        setPollingId(id);
    };

    // ── Step 1 Handlers ────────────────────────────────────────

    const handleAnalyzeAndDownload = async () => {
        if (!videoUrl.trim()) {
            setError('Please enter a video URL');
            return;
        }
        setIsDownloading(true);
        setIsAnalyzing(true);
        setError(null);
        setSuccessMessage(null);

        try {
            // Step A: Try to analyze (creates source + extracts transcript + insights)
            const source = await analyzeYouTubeVideo(videoUrl);
            setSelectedSource(source);

            // Download in parallel (background task on backend handles transcript)
            try {
                await downloadVideo(videoUrl, false);
            } catch (dlErr) {
                console.warn('Download step skipped:', dlErr.message);
            }

            setVideoUrl('');
            startPolling(source.id);
            setCurrentStep(STEPS.VIDEO_OVERVIEW);
            setSuccessMessage('Video imported! Analyzing...');
        } catch (err) {
            setError(err.message);
        } finally {
            setIsDownloading(false);
            setIsAnalyzing(false);
        }
    };

    const handleQuickDownload = async () => {
        if (!videoUrl.trim()) {
            setError('Please enter a video URL');
            return;
        }
        setIsDownloading(true);
        setError(null);

        try {
            const result = await downloadVideo(videoUrl, false);
            setSuccessMessage(`Downloaded from ${result.platform}!`);
            if (result.source_id) {
                const source = await getYouTubeSource(result.source_id);
                setSelectedSource(source);
                setTrimEnd(Math.min(source.duration_seconds || 60, 60));
                setCurrentStep(STEPS.VIDEO_OVERVIEW);
                // Load transcript/summary for quick-downloaded source
                loadTranscript(source.id);
                loadSummary(source.id);
            }
            setVideoUrl('');
            loadSources();
        } catch (err) {
            setError(err.message);
        } finally {
            setIsDownloading(false);
        }
    };

    const handleSelectSource = async (source) => {
        try {
            const fullSource = await getYouTubeSource(source.id);
            setSelectedSource(fullSource);
            setTrimStart(0);
            setTrimEnd(Math.min(fullSource.duration_seconds || 60, 60));
            setCurrentStep(STEPS.VIDEO_OVERVIEW);

            if (fullSource.analysis_status === 'analyzing') {
                startPolling(fullSource.id);
            } else if (fullSource.analysis_status === 'completed' || fullSource.analysis_status === 'transcript_ready') {
                // Source already analyzed — load data immediately
                loadSummary(fullSource.id);
                loadTranscript(fullSource.id);
            }
        } catch (err) {
            setError(err.message);
        }
    };

    // ── Step navigation ────────────────────────────────────────

    const goToStep = (step) => {
        if (step === STEPS.VIDEO_OVERVIEW && selectedSource) {
            loadTranscript(selectedSource.id);
            loadSummary(selectedSource.id);
        }
        if (step === STEPS.MUSIC_CAPTIONS) {
            loadMusicLibrary();
        }
        setCurrentStep(step);
    };

    const canProceed = () => {
        switch (currentStep) {
            case STEPS.URL_INPUT: return !!selectedSource;
            case STEPS.VIDEO_OVERVIEW: return !!selectedSource;
            case STEPS.EDITOR: return trimStart < trimEnd;
            case STEPS.MUSIC_CAPTIONS: return true;
            case STEPS.GENERATE: return false;
            default: return false;
        }
    };

    // ── Step 5: Generate Script → Review → Render ──────────────

    const handleGenerateScript = async () => {
        if (!selectedSource) return;
        setIsGenerating(true);
        setError(null);
        setScriptPreview(null);

        try {
            const result = await generateScript(selectedSource.id, {
                trimStart,
                trimEnd,
                stripAudio,
                musicTrack: selectedMusic,
                musicVolume,
                generateCaptions: captionSource !== 'none',
                captionSource,
                commentaryStyle,
                contentType,
            });

            setGenerationResult(result);

            // Store script preview data
            setScriptPreview({
                script_preview: result.script_preview,
                catchy_title: result.catchy_title,
                scenes: result.scenes,
                script_id: result.script_id,
                article_id: result.article_id,
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleApproveAndRender = async () => {
        if (!scriptPreview?.script_id) return;
        setIsApproving(true);
        setError(null);

        try {
            const result = await approveAndRender(scriptPreview.script_id, {
                trimStart,
                trimEnd,
                stripAudio,
                musicTrack: selectedMusic,
                musicVolume,
            });
            setGenerationResult(result);
            setSuccessMessage(result.message || 'Video rendering started!');

            if (result.redirect_to) {
                setTimeout(() => navigateTo(result.redirect_to.replace('/', '')), 2500);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setIsApproving(false);
        }
    };

    // ── YouTube IFrame API (for Editor step) ───────────────────

    useEffect(() => {
        if (currentStep !== STEPS.EDITOR || !selectedSource?.youtube_video_id) return;

        // Load YouTube IFrame API if not already loaded
        if (!window.YT) {
            const tag = document.createElement('script');
            tag.src = 'https://www.youtube.com/iframe_api';
            document.body.appendChild(tag);
        }

        const initPlayer = () => {
            const container = document.getElementById('yt-editor-player');
            if (!container) return;

            // Destroy previous player if exists
            if (playerRef.current && playerRef.current.destroy) {
                try { playerRef.current.destroy(); } catch (e) { /* ignore */ }
            }

            playerRef.current = new window.YT.Player('yt-editor-player', {
                videoId: selectedSource.youtube_video_id,
                playerVars: {
                    start: Math.floor(trimStart),
                    rel: 0,
                    modestbranding: 1,
                    playsinline: 1,
                },
                events: {
                    onReady: (event) => {
                        event.target.seekTo(Math.floor(trimStart), true);
                    },
                },
            });
        };

        if (window.YT && window.YT.Player) {
            // Small delay to ensure DOM element is rendered
            setTimeout(initPlayer, 100);
        } else {
            window.onYouTubeIframeAPIReady = initPlayer;
        }

        return () => {
            if (playerRef.current && playerRef.current.destroy) {
                try { playerRef.current.destroy(); } catch (e) { /* ignore */ }
                playerRef.current = null;
            }
        };
    }, [currentStep, selectedSource?.youtube_video_id]);

    // Debounced seek when sliders change
    useEffect(() => {
        if (currentStep !== STEPS.EDITOR) return;
        if (!playerRef.current || !playerRef.current.seekTo) return;

        // Debounce: wait 400ms after slider stops moving before seeking
        if (seekTimerRef.current) clearTimeout(seekTimerRef.current);
        seekTimerRef.current = setTimeout(() => {
            try {
                playerRef.current.seekTo(Math.floor(trimStart), true);
            } catch (e) { /* player might not be ready */ }
        }, 400);

        return () => {
            if (seekTimerRef.current) clearTimeout(seekTimerRef.current);
        };
    }, [trimStart, currentStep]);

    // ── Helpers ─────────────────────────────────────────────────

    const formatDuration = (seconds) => {
        if (!seconds) return '--:--';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const formatTimestamp = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // ── Render ──────────────────────────────────────────────────

    return (
        <div className="youtube-import wizard-mode">
            {/* Progress Steps */}
            <div className="wizard-steps">
                {STEP_LABELS.map((label, idx) => (
                    <div
                        key={idx}
                        className={`wizard-step ${idx === currentStep ? 'active' : ''} ${idx < currentStep ? 'completed' : ''}`}
                        onClick={() => idx <= currentStep && goToStep(idx)}
                    >
                        <div className="step-number">
                            {idx < currentStep ? '✓' : idx + 1}
                        </div>
                        <div className="step-label">{label}</div>
                    </div>
                ))}
            </div>

            {/* Error / Success */}
            {error && <div className="yt-error">{error} <button className="dismiss-btn" onClick={() => setError(null)}>×</button></div>}
            {successMessage && <div className="yt-success">{successMessage} <button className="dismiss-btn" onClick={() => setSuccessMessage(null)}>×</button></div>}

            {/* === STEP 1: URL INPUT === */}
            {currentStep === STEPS.URL_INPUT && (
                <div className="wizard-panel step-url-input">
                    <div className="wizard-panel-header">
                        <div className="yt-header-icon">🎬</div>
                        <div>
                            <h2>Import Video</h2>
                            <p>Paste a URL from YouTube, X/Twitter, or LinkedIn</p>
                        </div>
                    </div>

                    <div className="yt-input-section">
                        <div className="yt-input-wrapper">
                            {detectedPlatform && (
                                <span className="platform-badge" title={detectedPlatform}>
                                    {PLATFORM_ICONS[detectedPlatform] || '🔗'}
                                </span>
                            )}
                            <input
                                type="text"
                                placeholder="Paste video URL here..."
                                value={videoUrl}
                                onChange={(e) => setVideoUrl(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleAnalyzeAndDownload()}
                                className="yt-url-input"
                            />
                        </div>
                        <div className="url-actions">
                            <button
                                onClick={handleAnalyzeAndDownload}
                                disabled={isAnalyzing || isDownloading}
                                className="yt-analyze-btn primary"
                            >
                                {isAnalyzing ? <span className="loading-spinner" /> : <>🔍 Analyze & Import</>}
                            </button>
                            <button
                                onClick={handleQuickDownload}
                                disabled={isDownloading}
                                className="yt-analyze-btn secondary"
                                title="Download video without full analysis"
                            >
                                {isDownloading ? <span className="loading-spinner" /> : <>⬇️ Quick Download</>}
                            </button>
                        </div>
                    </div>

                    {/* Recent imports sidebar */}
                    <div className="recent-imports">
                        <h3>📹 Recent Imports</h3>
                        <div className="yt-source-list">
                            {sources.map(source => (
                                <div
                                    key={source.id}
                                    className={`yt-source-card ${selectedSource?.id === source.id ? 'active' : ''}`}
                                    onClick={() => handleSelectSource(source)}
                                >
                                    <img
                                        src={source.thumbnail_url || '/placeholder-thumb.png'}
                                        alt=""
                                        className="yt-source-thumb"
                                    />
                                    <div className="yt-source-info">
                                        <div className="yt-source-title">{source.title || 'Untitled Video'}</div>
                                        <div className="yt-source-meta">
                                            <span className={`status-badge ${source.analysis_status}`}>
                                                {source.analysis_status}
                                            </span>
                                            {source.insights_count > 0 && (
                                                <span className="insight-count">{source.insights_count} insights</span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {sources.length === 0 && (
                                <div className="yt-empty-state">
                                    No videos imported yet. Paste a URL above to get started!
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* === STEP 2: VIDEO OVERVIEW === */}
            {currentStep === STEPS.VIDEO_OVERVIEW && selectedSource && (
                <div className="wizard-panel step-overview">
                    {/* Video header with embedded player */}
                    <div className="yt-video-header">
                        {selectedSource.youtube_video_id ? (
                            <div className="video-player-wrapper">
                                <iframe
                                    src={`https://www.youtube.com/embed/${selectedSource.youtube_video_id}?rel=0&modestbranding=1`}
                                    title={selectedSource.title || 'Video'}
                                    frameBorder="0"
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowFullScreen
                                    className="video-player-iframe"
                                />
                            </div>
                        ) : (
                            <img
                                src={selectedSource.thumbnail_url}
                                alt=""
                                className="yt-video-thumb"
                            />
                        )}
                        <div className="yt-video-info">
                            <h2>{selectedSource.title || 'Analyzing...'}</h2>
                            <div className="yt-video-meta">
                                {selectedSource.channel_name && (
                                    <span className="channel-name">👤 {selectedSource.channel_name}</span>
                                )}
                                <span className="duration">⏱️ {formatDuration(selectedSource.duration_seconds)}</span>
                                <span className={`status-badge ${selectedSource.analysis_status}`}>
                                    {selectedSource.analysis_status === 'analyzing' && '⏳ '}
                                    {selectedSource.analysis_status}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Analyzing state */}
                    {selectedSource.analysis_status === 'analyzing' && (
                        <div className="yt-analyzing-state">
                            <div className="analyzing-animation">
                                <div className="brain-icon">🧠</div>
                                <div className="analyzing-text">AI is extracting transcript & finding insights...</div>
                                <div className="analyzing-subtext">This usually takes 15-30 seconds</div>
                            </div>
                        </div>
                    )}

                    {/* Two-column: Summary + Transcript */}
                    {(selectedSource.analysis_status === 'completed' || selectedSource.analysis_status === 'downloaded' || selectedSource.analysis_status === 'transcript_ready') && (
                        <div className="overview-columns">
                            {/* Summary Panel */}
                            <div className="overview-panel summary-panel">
                                <h3>📋 AI Summary</h3>
                                {isLoadingSummary ? (
                                    <div className="panel-loading"><span className="loading-spinner" /> Generating...</div>
                                ) : videoSummary ? (
                                    <div className="summary-text-block">
                                        {videoSummary.video_summary}
                                    </div>
                                ) : (
                                    <div className="panel-empty">Summary will be available after analysis completes.</div>
                                )}
                            </div>

                            {/* Transcript Panel */}
                            <div className="overview-panel transcript-panel">
                                <h3>📝 Transcript</h3>
                                {isLoadingTranscript ? (
                                    <div className="panel-loading"><span className="loading-spinner" /> Loading...</div>
                                ) : transcript && transcript.segments?.length > 0 ? (
                                    <div className="transcript-scroll">
                                        {transcript.segments.map((seg, i) => (
                                            <div
                                                key={i}
                                                className="transcript-segment"
                                                onClick={() => {
                                                    setTrimStart(Math.floor(seg.start));
                                                    setTrimEnd(Math.min(Math.ceil(seg.end), selectedSource.duration_seconds || 60));
                                                }}
                                                title="Click to set trim range"
                                            >
                                                <span className="ts-time">{formatTimestamp(seg.start)}</span>
                                                <span className="ts-text">{seg.text}</span>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="panel-empty">
                                        No transcript available yet. It will appear once analysis finishes.
                                    </div>
                                )}
                                {transcript && (
                                    <div className="transcript-source-tag">
                                        Source: {transcript.transcript_source || 'youtube_captions'}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Insights (if available) */}
                    {selectedSource.insights && selectedSource.insights.length > 0 && (
                        <div className="overview-insights">
                            <h3>🎯 Key Insights ({selectedSource.insights.length})</h3>
                            <div className="insights-grid">
                                {selectedSource.insights.slice(0, 6).map((insight, idx) => (
                                    <div
                                        key={idx}
                                        className="insight-mini-card"
                                        onClick={() => {
                                            setTrimStart(Math.floor(insight.start_time));
                                            setTrimEnd(Math.ceil(insight.end_time || insight.start_time + 30));
                                            goToStep(STEPS.EDITOR);
                                        }}
                                    >
                                        <div className="insight-mini-time">
                                            [{insight.formatted_time}] ⭐ {insight.viral_score}/10
                                        </div>
                                        <div className="insight-mini-summary">{insight.summary}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="wizard-nav">
                        <button className="nav-btn back" onClick={() => goToStep(STEPS.URL_INPUT)}>
                            ← Back
                        </button>
                        <button
                            className="nav-btn next"
                            onClick={() => goToStep(STEPS.EDITOR)}
                        >
                            Next: Edit Video →
                        </button>
                    </div>
                </div>
            )}

            {/* === STEP 3: VIDEO EDITOR === */}
            {currentStep === STEPS.EDITOR && selectedSource && (
                <div className="wizard-panel step-editor">
                    <div className="wizard-panel-header">
                        <h2>✂️ Video Editor</h2>
                        <p>Trim your clip and control audio</p>
                    </div>

                    {/* Video Preview with YouTube IFrame API */}
                    {selectedSource.youtube_video_id && (
                        <div className="editor-video-preview">
                            <div className="video-player-wrapper editor-player">
                                <div id="yt-editor-player" />
                            </div>
                            <div className="preview-controls">
                                <button
                                    className="play-selection-btn"
                                    onClick={() => {
                                        if (playerRef.current && playerRef.current.seekTo) {
                                            playerRef.current.seekTo(Math.floor(trimStart), true);
                                            playerRef.current.playVideo();
                                        }
                                    }}
                                >
                                    ▶ Play Selection ({formatTimestamp(trimStart)} → {formatTimestamp(trimEnd)})
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Timeline */}
                    <div className="editor-timeline" ref={timelineRef}>
                        <div className="timeline-bar">
                            <div
                                className="timeline-selection"
                                style={{
                                    left: `${(trimStart / (selectedSource.duration_seconds || 60)) * 100}%`,
                                    width: `${((trimEnd - trimStart) / (selectedSource.duration_seconds || 60)) * 100}%`
                                }}
                            />
                            <div
                                className="timeline-handle start"
                                style={{ left: `${(trimStart / (selectedSource.duration_seconds || 60)) * 100}%` }}
                                title={`Start: ${formatTimestamp(trimStart)}`}
                            />
                            <div
                                className="timeline-handle end"
                                style={{ left: `${(trimEnd / (selectedSource.duration_seconds || 60)) * 100}%` }}
                                title={`End: ${formatTimestamp(trimEnd)}`}
                            />
                        </div>
                        <div className="timeline-labels">
                            <span>0:00</span>
                            <span>{formatDuration(selectedSource.duration_seconds)}</span>
                        </div>
                    </div>

                    {/* Trim inputs */}
                    <div className="editor-controls">
                        <div className="control-group">
                            <label>Start Time</label>
                            <div className="time-input-wrapper">
                                <input
                                    type="range"
                                    min={0}
                                    max={selectedSource.duration_seconds || 60}
                                    value={trimStart}
                                    onChange={(e) => {
                                        const val = Number(e.target.value);
                                        setTrimStart(Math.min(val, trimEnd - 1));
                                    }}
                                    className="time-slider"
                                />
                                <span className="time-display">{formatTimestamp(trimStart)}</span>
                            </div>
                        </div>

                        <div className="control-group">
                            <label>End Time</label>
                            <div className="time-input-wrapper">
                                <input
                                    type="range"
                                    min={0}
                                    max={selectedSource.duration_seconds || 60}
                                    value={trimEnd}
                                    onChange={(e) => {
                                        const val = Number(e.target.value);
                                        setTrimEnd(Math.max(val, trimStart + 1));
                                    }}
                                    className="time-slider"
                                />
                                <span className="time-display">{formatTimestamp(trimEnd)}</span>
                            </div>
                        </div>

                        <div className="clip-info">
                            <span className="clip-duration">
                                📏 Clip Duration: <strong>{formatDuration(trimEnd - trimStart)}</strong>
                            </span>
                        </div>
                    </div>

                    {/* Audio toggle */}
                    <div className="audio-control">
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                checked={stripAudio}
                                onChange={(e) => setStripAudio(e.target.checked)}
                            />
                            <span className="toggle-slider" />
                            <span className="toggle-label">
                                {stripAudio ? '🔇 Original Audio Muted' : '🔊 Keep Original Audio'}
                            </span>
                        </label>
                    </div>

                    {/* Relevant transcript segments for the trim range */}
                    {transcript && transcript.segments?.length > 0 && (
                        <div className="editor-transcript-preview">
                            <h4>📝 Transcript in selection</h4>
                            <div className="transcript-preview-scroll">
                                {transcript.segments
                                    .filter(s => s.start >= trimStart && s.end <= trimEnd)
                                    .slice(0, 20)
                                    .map((seg, i) => (
                                        <span key={i} className="ts-preview-text">{seg.text} </span>
                                    ))}
                                {transcript.segments.filter(s => s.start >= trimStart && s.end <= trimEnd).length === 0 && (
                                    <span className="ts-preview-empty">No transcript segments in this range</span>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="wizard-nav">
                        <button className="nav-btn back" onClick={() => goToStep(STEPS.VIDEO_OVERVIEW)}>
                            ← Back
                        </button>
                        <button className="nav-btn next" onClick={() => goToStep(STEPS.MUSIC_CAPTIONS)}>
                            Next: Music & Captions →
                        </button>
                    </div>
                </div>
            )}

            {/* === STEP 4: MUSIC & CAPTIONS === */}
            {currentStep === STEPS.MUSIC_CAPTIONS && selectedSource && (
                <div className="wizard-panel step-music">
                    <div className="wizard-panel-header">
                        <h2>🎵 Music & Captions</h2>
                        <p>Choose background music and caption style</p>
                    </div>

                    {/* Music selection */}
                    <div className="music-section">
                        <h3>🎶 Background Music</h3>
                        <div className="music-grid">
                            <div
                                className={`music-card ${!selectedMusic ? 'selected' : ''}`}
                                onClick={() => setSelectedMusic(null)}
                            >
                                <div className="music-icon">🔇</div>
                                <div className="music-name">No Music</div>
                            </div>
                            {musicLibrary.map((track) => (
                                <div
                                    key={track.filename}
                                    className={`music-card ${selectedMusic === track.filename ? 'selected' : ''}`}
                                    onClick={() => setSelectedMusic(track.filename)}
                                >
                                    <div className="music-icon">🎵</div>
                                    <div className="music-name">{track.label}</div>
                                    <div className="music-file">{track.filename}</div>
                                </div>
                            ))}
                        </div>

                        {selectedMusic && (
                            <div className="volume-control">
                                <label>Volume: {Math.round(musicVolume * 100)}%</label>
                                <input
                                    type="range"
                                    min={0}
                                    max={0.5}
                                    step={0.01}
                                    value={musicVolume}
                                    onChange={(e) => setMusicVolume(Number(e.target.value))}
                                    className="volume-slider"
                                />
                            </div>
                        )}
                    </div>

                    {/* Caption selection */}
                    <div className="caption-section">
                        <h3>💬 Captions</h3>
                        <div className="caption-options">
                            {[
                                { value: 'transcript', label: '📝 From Transcript', desc: 'Auto-generated from video speech' },
                                { value: 'llm', label: '🤖 AI Generated', desc: 'LLM creates captions from summary' },
                                { value: 'none', label: '❌ No Captions', desc: 'Skip caption generation' },
                            ].map(opt => (
                                <label
                                    key={opt.value}
                                    className={`caption-option ${captionSource === opt.value ? 'selected' : ''}`}
                                >
                                    <input
                                        type="radio"
                                        name="captionSource"
                                        value={opt.value}
                                        checked={captionSource === opt.value}
                                        onChange={(e) => setCaptionSource(e.target.value)}
                                    />
                                    <div className="option-content">
                                        <div className="option-label">{opt.label}</div>
                                        <div className="option-desc">{opt.desc}</div>
                                    </div>
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="wizard-nav">
                        <button className="nav-btn back" onClick={() => goToStep(STEPS.EDITOR)}>
                            ← Back
                        </button>
                        <button className="nav-btn next" onClick={() => goToStep(STEPS.GENERATE)}>
                            Next: Review & Generate →
                        </button>
                    </div>
                </div>
            )}

            {/* === STEP 5: REVIEW & GENERATE === */}
            {currentStep === STEPS.GENERATE && selectedSource && (
                <div className="wizard-panel step-generate">
                    <div className="wizard-panel-header">
                        <h2>🚀 Review & Generate</h2>
                        <p>Choose your style, preview the script, then generate</p>
                    </div>

                    {/* Settings summary */}
                    <div className="generate-summary">
                        <div className="summary-row">
                            <span className="summary-label">📹 Source</span>
                            <span className="summary-value">{selectedSource.title}</span>
                        </div>
                        <div className="summary-row">
                            <span className="summary-label">✂️ Trim</span>
                            <span className="summary-value">
                                {formatTimestamp(trimStart)} → {formatTimestamp(trimEnd)} ({formatDuration(trimEnd - trimStart)})
                            </span>
                        </div>
                        <div className="summary-row">
                            <span className="summary-label">🔊 Audio</span>
                            <span className="summary-value">{stripAudio ? 'Original muted' : 'Keep original'}</span>
                        </div>
                        <div className="summary-row">
                            <span className="summary-label">🎵 Music</span>
                            <span className="summary-value">
                                {selectedMusic ? `${selectedMusic} (${Math.round(musicVolume * 100)}%)` : 'None'}
                            </span>
                        </div>
                        <div className="summary-row">
                            <span className="summary-label">💬 Captions</span>
                            <span className="summary-value">
                                {captionSource === 'transcript' ? 'From transcript' : captionSource === 'llm' ? 'AI generated' : 'None'}
                            </span>
                        </div>
                    </div>

                    {/* Style options */}
                    <div className="style-options">
                        <div className="control-group">
                            <label>Commentary Style</label>
                            <select
                                value={commentaryStyle}
                                onChange={(e) => setCommentaryStyle(e.target.value)}
                                className="style-select"
                            >
                                <option value="reaction">🎬 Reaction / Commentary</option>
                                <option value="analysis">🔍 In-depth Analysis</option>
                                <option value="educational">📚 Educational</option>
                            </select>
                        </div>

                        <div className="control-group">
                            <label>Content Type</label>
                            <select
                                value={contentType}
                                onChange={(e) => setContentType(e.target.value)}
                                className="style-select"
                            >
                                <option value="youtube_import">📥 YouTube Import</option>
                                <option value="daily_update">📰 News / Daily Update</option>
                                <option value="big_tech">🏢 Big Tech</option>
                                <option value="book_review">📚 Book Review</option>
                            </select>
                        </div>
                    </div>

                    {/* Two-phase flow: Generate Script → Review → Render */}
                    <div className="generate-action">
                        {generationResult && generationResult.status === 'generating' ? (
                            /* Phase 3: Video rendering started */
                            <div className="generation-result">
                                <div className="result-icon">✅</div>
                                <div className="result-text">{generationResult.message}</div>
                                <div className="result-details">
                                    {generationResult.script_id && <span>Script #{generationResult.script_id}</span>}
                                    {generationResult.clip_duration && <span> • {formatDuration(generationResult.clip_duration)}</span>}
                                </div>
                            </div>
                        ) : scriptPreview ? (
                            /* Phase 2: Script preview — review & approve */
                            <div className="script-preview-panel">
                                <div className="script-preview-header">
                                    <h3>📜 Generated Script</h3>
                                    {scriptPreview.catchy_title && (
                                        <div className="script-title">"{scriptPreview.catchy_title}"</div>
                                    )}
                                </div>

                                {scriptPreview.scenes && scriptPreview.scenes.length > 0 ? (
                                    <div className="script-scenes">
                                        {scriptPreview.scenes.map((scene, idx) => (
                                            <div key={idx} className="script-scene-card">
                                                <div className="scene-header">
                                                    <span className="scene-number">Scene {scene.scene_number || idx + 1}</span>
                                                    {scene.duration && (
                                                        <span className="scene-duration">~{scene.duration}s</span>
                                                    )}
                                                </div>
                                                <div className="scene-text">{scene.text}</div>
                                                {scene.visual_direction && (
                                                    <div className="scene-visual">📷 {scene.visual_direction}</div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="script-raw-preview">
                                        {scriptPreview.script_preview}
                                    </div>
                                )}

                                <div className="script-preview-actions">
                                    <button
                                        className="nav-btn back"
                                        onClick={() => {
                                            setScriptPreview(null);
                                            setGenerationResult(null);
                                        }}
                                    >
                                        ↩ Regenerate Script
                                    </button>
                                    <button
                                        className="generate-btn"
                                        onClick={handleApproveAndRender}
                                        disabled={isApproving}
                                    >
                                        {isApproving ? (
                                            <><span className="loading-spinner" /> Rendering...</>
                                        ) : (
                                            <>🚀 Approve & Generate Video</>
                                        )}
                                    </button>
                                </div>
                            </div>
                        ) : (
                            /* Phase 1: Generate script */
                            <button
                                className="generate-btn script-btn"
                                onClick={handleGenerateScript}
                                disabled={isGenerating}
                            >
                                {isGenerating ? (
                                    <><span className="loading-spinner" /> Generating Script...</>
                                ) : (
                                    <>📜 Generate Script Preview</>
                                )}
                            </button>
                        )}
                    </div>

                    <div className="wizard-nav">
                        <button className="nav-btn back" onClick={() => goToStep(STEPS.MUSIC_CAPTIONS)}>
                            ← Back
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default YouTubeImport;
