/**
 * YouTubeImport.jsx — v2 Enhanced 4-Step Wizard
 *
 * Step 1: Smart Import   — Paste URL, one-click download + analyze, shows metadata
 * Step 2: Trim & Preview — YT player + trim sliders + transcript + smart trim suggestions
 * Step 3: Script Studio  — Inline editing + output mode + voice + captions + aspect ratio + music
 * Step 4: Generate       — Summary + preview + one-click render
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  analyzeYouTubeVideo,
  getYouTubeSources,
  getYouTubeSource,
  getVideoSummary,
  getTranscript,
  getMusicLibrary,
  downloadVideo,
  getVideoInfo,
  generateScript,
  approveAndRender,
  getVoices,
  generatePreview,
} from '../services/youtubeApi';
import './YouTubeImport.css';

const STEPS = [
  { id: 1, label: 'Import', icon: '📥' },
  { id: 2, label: 'Trim & Preview', icon: '✂️' },
  { id: 3, label: 'Script Studio', icon: '🎬' },
  { id: 4, label: 'Generate', icon: '🚀' },
];

const OUTPUT_MODES = [
  { id: 'tts', label: '🎙️ TTS Voiceover', desc: 'AI narrates your script over the video' },
  { id: 'text_overlay', label: '📝 Text Overlay', desc: 'Burn script text as animated overlays' },
  { id: 'captions', label: '💬 Captions', desc: 'Subtitle-style captions at bottom' },
  { id: 'tts_captions', label: '🎙️+💬 TTS + Captions', desc: 'Voiceover with matching captions' },
];

const ASPECT_RATIOS = [
  { id: '16:9', label: '🖥️ 16:9', desc: 'Landscape (YouTube)' },
  { id: '9:16', label: '📱 9:16', desc: 'Shorts / Reels' },
  { id: '1:1', label: '⬛ 1:1', desc: 'Instagram Square' },
];

const CAPTION_FONTS = [
  { id: 'bold', label: 'Bold' },
  { id: 'light', label: 'Light' },
  { id: 'cinematic', label: 'Cinematic' },
];

const CAPTION_COLORS = [
  { id: 'white', label: 'White', hex: '#ffffff' },
  { id: 'yellow', label: 'Yellow', hex: '#fde047' },
  { id: 'cyan', label: 'Cyan', hex: '#22d3ee' },
];

const CAPTION_POSITIONS = [
  { id: 'top', label: 'Top' },
  { id: 'center', label: 'Center' },
  { id: 'bottom', label: 'Bottom' },
];

const CAPTION_BG_STYLES = [
  { id: 'none', label: 'None' },
  { id: 'dark_box', label: 'Dark Box' },
  { id: 'blurred', label: 'Blurred' },
];

function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function YouTubeImport() {
  // ── Wizard state ──
  const [step, setStep] = useState(1);

  // ── Step 1: Import ──
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [sources, setSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);

  // ── Step 2: Trim ──
  const [transcript, setTranscript] = useState(null);
  const [summary, setSummary] = useState(null);
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(60);
  const [stripAudio, setStripAudio] = useState(false);
  const playerRef = useRef(null);
  const playerInstanceRef = useRef(null);

  // ── Step 3: Script Studio ──
  const [scriptData, setScriptData] = useState(null);
  const [scriptLoading, setScriptLoading] = useState(false);
  const [editedScenes, setEditedScenes] = useState([]);
  const [outputMode, setOutputMode] = useState('tts');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [commentaryStyle, setCommentaryStyle] = useState('reaction');
  const [contentType, setContentType] = useState('youtube_import');

  // Voice selection
  const [voiceData, setVoiceData] = useState(null);
  const [ttsProvider, setTtsProvider] = useState('openai');
  const [voiceId, setVoiceId] = useState('');

  // Caption styling
  const [captionFont, setCaptionFont] = useState('bold');
  const [captionColor, setCaptionColor] = useState('white');
  const [captionPosition, setCaptionPosition] = useState('bottom');
  const [captionBgStyle, setCaptionBgStyle] = useState('dark_box');

  // Music
  const [musicLibrary, setMusicLibrary] = useState([]);
  const [musicTrack, setMusicTrack] = useState('');
  const [musicVolume, setMusicVolume] = useState(0.12);

  // ── Step 4: Generate ──
  const [generating, setGenerating] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState('');

  // ── Load sources on mount ──
  useEffect(() => {
    loadSources();
  }, []);

  // ── Load voices on Step 3 ──
  useEffect(() => {
    if (step === 3 && !voiceData) {
      loadVoices();
      loadMusicLibrary();
    }
  }, [step]);

  const loadSources = async () => {
    try {
      const data = await getYouTubeSources();
      setSources(data);
    } catch {
      /* silent */
    }
  };

  const loadVoices = async () => {
    try {
      const data = await getVoices();
      setVoiceData(data);
      if (data.default_provider) setTtsProvider(data.default_provider);
      if (data.providers?.length) {
        const defaultProv = data.providers.find(p => p.id === data.default_provider);
        if (defaultProv?.default_voice) setVoiceId(defaultProv.default_voice);
      }
    } catch {
      /* Voice loading is non-critical */
    }
  };

  const loadMusicLibrary = async () => {
    try {
      const data = await getMusicLibrary();
      setMusicLibrary(data.tracks || []);
      if (data.default_track) setMusicTrack(data.default_track);
    } catch {
      /* non-critical */
    }
  };

  // ═══════════════════════════════════════════════════════════
  // STEP 1: Smart Import
  // ═══════════════════════════════════════════════════════════
  const handleImport = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // 1) Quick metadata preview
      const info = await getVideoInfo(url.trim());
      setVideoInfo(info);

      // 2) Analyze + download in one click
      const result = await analyzeYouTubeVideo(url.trim());
      setSuccess(`✓ Imported: ${result.title || info?.title || 'Video'}`);

      // 3) Reload sources & select this one
      const updatedSources = await getYouTubeSources();
      setSources(updatedSources);

      const imported = updatedSources.find(s => s.youtube_url === url.trim() || s.id === result.source_id);
      if (imported) {
        await selectSource(imported);
      }
    } catch (err) {
      setError(err.message || 'Import failed');
    } finally {
      setLoading(false);
    }
  };

  const selectSource = async (source) => {
    setSelectedSource(source);
    setVideoInfo({
      title: source.title,
      channel_name: source.channel_name,
      duration: source.duration_seconds,
      thumbnail_url: source.thumbnail_url,
      description: source.description,
    });
    setTrimEnd(source.duration_seconds || 60);

    // Auto-load transcript and summary
    try {
      const detail = await getYouTubeSource(source.id);
      setSelectedSource(detail);

      const [transcriptData, summaryData] = await Promise.allSettled([
        getTranscript(source.id),
        getVideoSummary(source.id),
      ]);

      if (transcriptData.status === 'fulfilled') setTranscript(transcriptData.value);
      if (summaryData.status === 'fulfilled') setSummary(summaryData.value);
    } catch {
      /* non-critical */
    }
  };

  // ═══════════════════════════════════════════════════════════
  // STEP 2: YouTube Player
  // ═══════════════════════════════════════════════════════════
  const initYouTubePlayer = useCallback(() => {
    if (!selectedSource?.youtube_video_id || !playerRef.current) return;
    if (playerInstanceRef.current) return;

    if (!window.YT) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(tag);
      window.onYouTubeIframeAPIReady = () => createPlayer();
    } else {
      createPlayer();
    }

    function createPlayer() {
      playerInstanceRef.current = new window.YT.Player(playerRef.current, {
        videoId: selectedSource.youtube_video_id,
        playerVars: {
          autoplay: 0, controls: 1, modestbranding: 1, rel: 0,
          start: Math.floor(trimStart),
        },
      });
    }
  }, [selectedSource?.youtube_video_id, trimStart]);

  useEffect(() => {
    if (step === 2) initYouTubePlayer();
  }, [step, initYouTubePlayer]);

  const handleTrimFromInsight = (insight) => {
    setTrimStart(insight.start_time);
    setTrimEnd(insight.end_time || (insight.start_time + 60));
    if (playerInstanceRef.current?.seekTo) {
      playerInstanceRef.current.seekTo(insight.start_time, true);
    }
  };

  // ═══════════════════════════════════════════════════════════
  // STEP 3: Script Generation & Editing
  // ═══════════════════════════════════════════════════════════
  const handleGenerateScript = async () => {
    if (!selectedSource) return;
    setScriptLoading(true);

    try {
      const result = await generateScript(selectedSource.id, {
        trimStart,
        trimEnd,
        commentaryStyle,
        contentType,
        autoApprove: false,
      });

      setScriptData(result);
      setEditedScenes(result.scenes ? [...result.scenes] : []);
    } catch (err) {
      setError(err.message || 'Script generation failed');
    } finally {
      setScriptLoading(false);
    }
  };

  useEffect(() => {
    if (step === 3 && selectedSource && !scriptData && !scriptLoading) {
      handleGenerateScript();
    }
  }, [step]);

  const updateSceneText = (index, newText) => {
    setEditedScenes(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], text: newText };
      return updated;
    });
  };

  // ═══════════════════════════════════════════════════════════
  // STEP 4: Generate
  // ═══════════════════════════════════════════════════════════
  const handlePreview = async () => {
    if (!selectedSource) return;
    setPreviewLoading(true);
    try {
      const result = await generatePreview(selectedSource.id, {
        trimStart, trimEnd, stripAudio, aspectRatio, outputMode,
      });
      // Preview URL is relative — prepend backend host
      const backendBase = 'http://localhost:8000';
      setPreviewUrl(`${backendBase}${result.preview_url}`);
    } catch (err) {
      setError(err.message || 'Preview failed');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!scriptData?.script_id) return;
    setGenerating(true);
    setError('');

    try {
      await approveAndRender(scriptData.script_id, {
        trimStart, trimEnd, stripAudio,
        musicTrack, musicVolume,
        generateTts: outputMode === 'tts' || outputMode === 'tts_captions',
        ttsProvider,
        voiceId,
        creditsOverlay: true,
        aspectRatio,
        outputMode,
      });
      setSuccess('🚀 Video generation started! Redirecting to validation...');
      setTimeout(() => (window.location.href = '/videos'), 2000);
    } catch (err) {
      setError(err.message || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  // ── Can proceed? ──
  const canProceed = () => {
    switch (step) {
      case 1: return !!selectedSource;
      case 2: return trimEnd > trimStart;
      case 3: return !!scriptData;
      case 4: return true;
      default: return false;
    }
  };

  const handleNextStep = () => {
    if (canProceed() && step < 4) setStep(step + 1);
  };

  const handlePrevStep = () => {
    if (step > 1) setStep(step - 1);
  };

  // ═══════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════
  return (
    <div className="youtube-import">
      {/* ── Wizard Steps Bar ── */}
      <div className="wizard-steps">
        {STEPS.map(s => (
          <div
            key={s.id}
            className={`wizard-step ${step === s.id ? 'active' : ''} ${step > s.id ? 'completed' : ''}`}
            onClick={() => s.id <= step && setStep(s.id)}
          >
            <span className="step-number">{step > s.id ? '✓' : s.icon}</span>
            <span>{s.label}</span>
          </div>
        ))}
      </div>

      {/* ── Messages ── */}
      {error && (
        <div className="yt-error">
          <span>❌ {error}</span>
          <button className="dismiss-btn" onClick={() => setError('')}>×</button>
        </div>
      )}
      {success && (
        <div className="yt-success">
          <span>{success}</span>
          <button className="dismiss-btn" onClick={() => setSuccess('')}>×</button>
        </div>
      )}

      {/* ═══ STEP 1: Smart Import ═══ */}
      {step === 1 && (
        <div className="wizard-panel" id="yt-step-import">
          <div className="wizard-panel-header">
            <span className="yt-header-icon">📥</span>
            <div>
              <h2>Smart Import</h2>
              <p>Paste a YouTube, X/Twitter, or LinkedIn URL to get started</p>
            </div>
          </div>

          {/* URL Input */}
          <div className="yt-input-section">
            <div className="yt-input-wrapper">
              <span className="platform-badge">🔗</span>
              <input
                id="yt-url-input"
                className="yt-url-input"
                type="text"
                placeholder="Paste video URL here..."
                value={url}
                onChange={e => setUrl(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleImport()}
              />
            </div>
            <div className="url-actions">
              <button
                id="yt-import-btn"
                className="yt-analyze-btn primary"
                onClick={handleImport}
                disabled={loading || !url.trim()}
              >
                {loading ? <span className="loading-spinner" /> : '📥'}
                {loading ? 'Importing...' : 'Import & Analyze'}
              </button>
            </div>
          </div>

          {/* Video Info Preview (appears after paste/import) */}
          {videoInfo && videoInfo.title && (
            <div className="yt-video-header" style={{ marginBottom: '1.5rem' }}>
              {videoInfo.thumbnail_url && (
                <img src={videoInfo.thumbnail_url} alt="" className="yt-video-thumb" />
              )}
              <div className="yt-video-info">
                <h2>{videoInfo.title}</h2>
                <div className="yt-video-meta">
                  {videoInfo.channel_name && <span className="channel-name">📺 {videoInfo.channel_name}</span>}
                  {videoInfo.duration && <span>⏱️ {formatTime(videoInfo.duration)}</span>}
                </div>
                {videoInfo.description && (
                  <p style={{
                    marginTop: '0.75rem', fontSize: '0.85rem', lineHeight: 1.6,
                    color: 'var(--text-secondary)', maxHeight: '4.8em', overflow: 'hidden',
                  }}>
                    {videoInfo.description}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Recent Imports */}
          <div className="recent-imports">
            <h3>📋 Recent Imports</h3>
            <div className="yt-source-list">
              {sources.length === 0 ? (
                <div className="yt-empty-state">No imports yet. Paste a URL above to get started.</div>
              ) : (
                sources.slice(0, 8).map(s => (
                  <div
                    key={s.id}
                    className={`yt-source-card ${selectedSource?.id === s.id ? 'active' : ''}`}
                    onClick={() => selectSource(s)}
                  >
                    {s.thumbnail_url && (
                      <img src={s.thumbnail_url} alt="" className="yt-source-thumb" />
                    )}
                    <div className="yt-source-info">
                      <div className="yt-source-title">{s.title || s.youtube_video_id}</div>
                      <div className="yt-source-meta">
                        <span className={`status-badge ${s.analysis_status}`}>{s.analysis_status}</span>
                        {s.insights_count > 0 && (
                          <span className="insight-count">💡 {s.insights_count} insights</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═══ STEP 2: Trim & Preview ═══ */}
      {step === 2 && selectedSource && (
        <div className="wizard-panel" id="yt-step-trim">
          <div className="wizard-panel-header">
            <span className="yt-header-icon">✂️</span>
            <div>
              <h2>Trim & Preview</h2>
              <p>Select the portion of the video you want to use</p>
            </div>
          </div>

          {/* Video Player */}
          <div className="editor-video-preview">
            <div className="video-player-wrapper editor-player">
              <div ref={playerRef} className="video-player-iframe" />
            </div>
            <div className="preview-trim-label">
              Trim: {formatTime(trimStart)} → {formatTime(trimEnd)} ({formatTime(trimEnd - trimStart)})
            </div>
          </div>

          {/* Trim Controls */}
          <div className="editor-controls">
            <div className="control-group">
              <label>Start Time</label>
              <div className="time-input-wrapper">
                <input
                  id="yt-trim-start"
                  type="range"
                  className="time-slider"
                  min={0}
                  max={selectedSource.duration_seconds || 300}
                  step={1}
                  value={trimStart}
                  onChange={e => {
                    const v = parseFloat(e.target.value);
                    setTrimStart(Math.min(v, trimEnd - 5));
                  }}
                />
                <span className="time-display">{formatTime(trimStart)}</span>
              </div>
            </div>
            <div className="control-group">
              <label>End Time</label>
              <div className="time-input-wrapper">
                <input
                  id="yt-trim-end"
                  type="range"
                  className="time-slider"
                  min={0}
                  max={selectedSource.duration_seconds || 300}
                  step={1}
                  value={trimEnd}
                  onChange={e => {
                    const v = parseFloat(e.target.value);
                    setTrimEnd(Math.max(v, trimStart + 5));
                  }}
                />
                <span className="time-display">{formatTime(trimEnd)}</span>
              </div>
            </div>
            <div className="clip-info">
              <label>Audio</label>
              <label id="yt-strip-audio-toggle" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={stripAudio}
                  onChange={e => setStripAudio(e.target.checked)}
                />
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Mute original audio
                </span>
              </label>
            </div>
          </div>

          {/* Two-column: Transcript + Smart Trim Suggestions */}
          <div className="overview-columns">
            {/* Transcript */}
            <div className="overview-panel">
              <h3>📝 Transcript</h3>
              {!transcript ? (
                <div className="panel-loading">
                  <span className="loading-spinner" /> Loading transcript...
                </div>
              ) : transcript.segments?.length > 0 ? (
                <div className="transcript-scroll">
                  {transcript.segments.map((seg, i) => {
                    const inRange = seg.start >= trimStart && seg.end <= trimEnd;
                    return (
                      <div
                        key={i}
                        className="transcript-segment"
                        style={inRange ? { background: 'var(--color-primary-soft)' } : {}}
                        onClick={() => {
                          setTrimStart(seg.start);
                          if (playerInstanceRef.current?.seekTo) {
                            playerInstanceRef.current.seekTo(seg.start, true);
                          }
                        }}
                      >
                        <span className="ts-time">{formatTime(seg.start)}</span>
                        <span className="ts-text">{seg.text}</span>
                      </div>
                    );
                  })}
                  {transcript.transcript_source && (
                    <div className="transcript-source-tag">
                      Source: {transcript.transcript_source}
                    </div>
                  )}
                </div>
              ) : (
                <div className="panel-empty">No transcript available. AI will analyze the video visually.</div>
              )}
            </div>

            {/* Smart Trim Suggestions (from insights) */}
            <div className="overview-panel">
              <h3>💡 Smart Trim Suggestions</h3>
              {selectedSource.insights?.length > 0 ? (
                <div className="insights-grid" style={{ gridTemplateColumns: '1fr' }}>
                  {selectedSource.insights.map((insight, i) => (
                    <div
                      key={i}
                      className="insight-mini-card"
                      onClick={() => handleTrimFromInsight(insight)}
                    >
                      <div className="insight-mini-time">
                        ⏱ {formatTime(insight.start_time)}–{formatTime(insight.end_time)}
                        {insight.viral_score && (
                          <span style={{ marginLeft: '0.5rem', color: 'var(--color-warning)' }}>
                            🔥 {insight.viral_score}/10
                          </span>
                        )}
                      </div>
                      <div className="insight-mini-summary">{insight.summary}</div>
                    </div>
                  ))}
                </div>
              ) : summary?.video_summary ? (
                <div className="summary-text-block">{summary.video_summary}</div>
              ) : (
                <div className="panel-empty">
                  Insights will appear after analysis completes.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═══ STEP 3: Script Studio ═══ */}
      {step === 3 && selectedSource && (
        <div className="wizard-panel" id="yt-step-script">
          <div className="wizard-panel-header">
            <span className="yt-header-icon">🎬</span>
            <div>
              <h2>Script Studio</h2>
              <p>Review, edit, and customize your video output</p>
            </div>
          </div>

          {/* Script Scenes — Inline Editing */}
          <div className="overview-panel" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              📜 Script
              <button
                className="yt-analyze-btn secondary"
                style={{ fontSize: '0.75rem', padding: '0.4rem 0.8rem' }}
                onClick={handleGenerateScript}
                disabled={scriptLoading}
              >
                {scriptLoading ? <span className="loading-spinner" /> : '🔄'} Regenerate
              </button>
            </h3>

            {scriptLoading ? (
              <div className="yt-analyzing-state">
                <div className="analyzing-animation">
                  <div className="brain-icon">🧠</div>
                  <div className="analyzing-text">Generating script...</div>
                  <div className="analyzing-subtext">Using title, description, transcript & AI analysis</div>
                </div>
              </div>
            ) : scriptData?.catchy_title ? (
              <div>
                <input
                  id="yt-script-title"
                  type="text"
                  value={scriptData.catchy_title}
                  onChange={e => setScriptData(prev => ({ ...prev, catchy_title: e.target.value }))}
                  style={{
                    width: '100%', padding: '0.8rem 1rem', fontSize: '1.1rem', fontWeight: 700,
                    background: 'var(--surface-page)', border: '1px solid var(--border-card)',
                    borderRadius: '10px', color: 'var(--text-heading)', marginBottom: '1rem',
                  }}
                />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {editedScenes.map((scene, i) => (
                    <div key={i} style={{
                      display: 'flex', gap: '0.75rem', padding: '0.6rem',
                      background: 'var(--surface-page)', border: '1px solid var(--border-card)',
                      borderRadius: '8px',
                    }}>
                      <span style={{
                        minWidth: '28px', height: '28px', borderRadius: '50%',
                        background: 'var(--gradient-indigo)', display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                        fontSize: '0.75rem', fontWeight: 700, color: '#fff', flexShrink: 0,
                      }}>{i + 1}</span>
                      <textarea
                        id={`yt-scene-${i}`}
                        value={scene.text || ''}
                        onChange={e => updateSceneText(i, e.target.value)}
                        rows={2}
                        style={{
                          flex: 1, background: 'transparent', border: 'none',
                          color: 'var(--text-secondary)', fontSize: '0.85rem',
                          lineHeight: 1.5, resize: 'vertical', outline: 'none',
                          fontFamily: 'inherit',
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="panel-empty">Click "Regenerate" to create a script.</div>
            )}
          </div>

          {/* Output Mode + Aspect Ratio */}
          <div className="overview-columns">
            {/* Output Mode Picker */}
            <div className="overview-panel">
              <h3>🎛️ Output Mode</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {OUTPUT_MODES.map(mode => (
                  <div
                    key={mode.id}
                    id={`yt-mode-${mode.id}`}
                    className={`insight-mini-card ${outputMode === mode.id ? 'active' : ''}`}
                    onClick={() => setOutputMode(mode.id)}
                    style={outputMode === mode.id ? {
                      borderColor: 'var(--color-primary)', background: 'var(--color-primary-soft)',
                    } : {}}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                      {mode.label}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                      {mode.desc}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Aspect Ratio */}
            <div className="overview-panel">
              <h3>📐 Aspect Ratio</h3>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                {ASPECT_RATIOS.map(ar => (
                  <div
                    key={ar.id}
                    id={`yt-ar-${ar.id.replace(':', '')}`}
                    className="insight-mini-card"
                    onClick={() => setAspectRatio(ar.id)}
                    style={{
                      flex: 1, textAlign: 'center', cursor: 'pointer',
                      ...(aspectRatio === ar.id ? {
                        borderColor: 'var(--color-primary)', background: 'var(--color-primary-soft)',
                      } : {}),
                    }}
                  >
                    <div style={{ fontSize: '1.5rem', marginBottom: '0.3rem' }}>{ar.label.split(' ')[0]}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{ar.desc}</div>
                  </div>
                ))}
              </div>

              {/* Commentary Style */}
              <h3 style={{ marginTop: '1rem' }}>🎨 Commentary Style</h3>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {['reaction', 'analysis', 'educational'].map(style => (
                  <button
                    key={style}
                    className={`yt-analyze-btn ${commentaryStyle === style ? 'primary' : 'secondary'}`}
                    style={{ fontSize: '0.75rem', padding: '0.4rem 0.8rem', flex: 1 }}
                    onClick={() => setCommentaryStyle(style)}
                  >
                    {style.charAt(0).toUpperCase() + style.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Voice Selector (only when TTS mode) */}
          {(outputMode === 'tts' || outputMode === 'tts_captions') && voiceData && (
            <div className="overview-panel" style={{ marginTop: '1rem' }}>
              <h3>🎙️ Voice Selection</h3>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                {/* Provider Tabs */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', minWidth: '120px' }}>
                  {voiceData.providers?.map(prov => (
                    <button
                      key={prov.id}
                      className={`yt-analyze-btn ${ttsProvider === prov.id ? 'primary' : 'secondary'}`}
                      style={{ fontSize: '0.75rem', padding: '0.5rem 0.8rem', textAlign: 'left' }}
                      onClick={() => {
                        setTtsProvider(prov.id);
                        setVoiceId(prov.default_voice || '');
                      }}
                    >
                      {prov.name}
                      <span style={{ display: 'block', fontSize: '0.65rem', opacity: 0.7 }}>
                        {prov.cost_label}
                      </span>
                    </button>
                  ))}
                </div>

                {/* Voice Dropdown */}
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.5rem' }}>
                    {voiceData.voices?.[ttsProvider]?.map(voice => (
                      <div
                        key={voice.id}
                        className="insight-mini-card"
                        onClick={() => setVoiceId(voice.id)}
                        style={voiceId === voice.id ? {
                          borderColor: 'var(--color-primary)', background: 'var(--color-primary-soft)',
                        } : { cursor: 'pointer' }}
                      >
                        <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                          {voice.name}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{voice.tone}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Caption Styling (only when caption mode) */}
          {(outputMode === 'captions' || outputMode === 'tts_captions') && (
            <div className="overview-panel" style={{ marginTop: '1rem' }}>
              <h3>💬 Caption Styling</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem', display: 'block' }}>Font</label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                    {CAPTION_FONTS.map(f => (
                      <button key={f.id}
                        className={`yt-analyze-btn ${captionFont === f.id ? 'primary' : 'secondary'}`}
                        style={{ fontSize: '0.7rem', padding: '0.3rem 0.5rem' }}
                        onClick={() => setCaptionFont(f.id)}
                      >{f.label}</button>
                    ))}
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem', display: 'block' }}>Color</label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                    {CAPTION_COLORS.map(c => (
                      <button key={c.id}
                        className={`yt-analyze-btn ${captionColor === c.id ? 'primary' : 'secondary'}`}
                        style={{ fontSize: '0.7rem', padding: '0.3rem 0.5rem' }}
                        onClick={() => setCaptionColor(c.id)}
                      >
                        <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: c.hex, marginRight: 4 }} />
                        {c.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem', display: 'block' }}>Position</label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                    {CAPTION_POSITIONS.map(p => (
                      <button key={p.id}
                        className={`yt-analyze-btn ${captionPosition === p.id ? 'primary' : 'secondary'}`}
                        style={{ fontSize: '0.7rem', padding: '0.3rem 0.5rem' }}
                        onClick={() => setCaptionPosition(p.id)}
                      >{p.label}</button>
                    ))}
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem', display: 'block' }}>Background</label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                    {CAPTION_BG_STYLES.map(bg => (
                      <button key={bg.id}
                        className={`yt-analyze-btn ${captionBgStyle === bg.id ? 'primary' : 'secondary'}`}
                        style={{ fontSize: '0.7rem', padding: '0.3rem 0.5rem' }}
                        onClick={() => setCaptionBgStyle(bg.id)}
                      >{bg.label}</button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Background Music */}
          <div className="overview-panel" style={{ marginTop: '1rem' }}>
            <h3>🎵 Background Music</h3>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <select
                id="yt-music-select"
                value={musicTrack}
                onChange={e => setMusicTrack(e.target.value)}
                style={{
                  flex: 1, padding: '0.6rem 0.8rem', background: 'var(--surface-page)',
                  border: '1px solid var(--border-card)', borderRadius: '8px',
                  color: 'var(--text-primary)', fontSize: '0.85rem',
                }}
              >
                <option value="">None</option>
                {musicLibrary.map(track => (
                  <option key={track.filename} value={track.filename}>
                    {track.label} ({track.content_type})
                  </option>
                ))}
              </select>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '180px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Vol</span>
                <input
                  type="range"
                  min={0} max={1} step={0.01}
                  value={musicVolume}
                  onChange={e => setMusicVolume(parseFloat(e.target.value))}
                  className="time-slider"
                  style={{ flex: 1 }}
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', minWidth: '30px' }}>
                  {Math.round(musicVolume * 100)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══ STEP 4: Generate ═══ */}
      {step === 4 && selectedSource && (
        <div className="wizard-panel" id="yt-step-generate">
          <div className="wizard-panel-header">
            <span className="yt-header-icon">🚀</span>
            <div>
              <h2>Generate Video</h2>
              <p>Review your settings and generate</p>
            </div>
          </div>

          {/* Settings Summary */}
          <div className="overview-columns">
            <div className="overview-panel">
              <h3>📋 Settings Summary</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Source</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                    {selectedSource.title?.slice(0, 40) || 'Video'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Trim</span>
                  <span style={{ color: 'var(--color-primary-light)', fontFamily: 'var(--font-mono)' }}>
                    {formatTime(trimStart)} → {formatTime(trimEnd)}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Output Mode</span>
                  <span style={{ color: 'var(--text-primary)' }}>
                    {OUTPUT_MODES.find(m => m.id === outputMode)?.label}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Aspect Ratio</span>
                  <span style={{ color: 'var(--text-primary)' }}>{aspectRatio}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Audio</span>
                  <span style={{ color: 'var(--text-primary)' }}>
                    {stripAudio ? 'Muted' : 'Original kept'}
                  </span>
                </div>
                {(outputMode === 'tts' || outputMode === 'tts_captions') && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Voice</span>
                    <span style={{ color: 'var(--text-primary)' }}>
                      {ttsProvider} / {voiceId}
                    </span>
                  </div>
                )}
                {musicTrack && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Music</span>
                    <span style={{ color: 'var(--text-primary)' }}>
                      {musicTrack} ({Math.round(musicVolume * 100)}%)
                    </span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Script</span>
                  <span style={{ color: 'var(--text-primary)' }}>
                    {editedScenes.length} scenes • {commentaryStyle}
                  </span>
                </div>
              </div>
            </div>

            {/* Preview Panel */}
            <div className="overview-panel">
              <h3>🎬 Preview</h3>
              {previewUrl ? (
                <video
                  src={previewUrl}
                  controls
                  style={{ width: '100%', borderRadius: '8px', marginBottom: '0.5rem' }}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
                  <button
                    id="yt-preview-btn"
                    className="yt-analyze-btn primary"
                    onClick={handlePreview}
                    disabled={previewLoading}
                  >
                    {previewLoading ? <span className="loading-spinner" /> : '🎬'}
                    {previewLoading ? 'Generating preview...' : 'Generate 5s Preview'}
                  </button>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                    Quick preview with overlays applied
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Generate Button */}
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
            <button
              id="yt-generate-btn"
              className="yt-analyze-btn primary"
              onClick={handleGenerate}
              disabled={generating || !scriptData}
              style={{ padding: '1rem 3rem', fontSize: '1.1rem', borderRadius: '14px' }}
            >
              {generating ? <span className="loading-spinner" /> : '🚀'}
              {generating ? ' Generating video...' : ' Generate Video'}
            </button>
            {generating && (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                This may take a few minutes. You'll be redirected to Video Validation when ready.
              </p>
            )}
          </div>
        </div>
      )}

      {/* ── Wizard Navigation ── */}
      <div className="wizard-nav">
        <button
          className="nav-btn back"
          onClick={handlePrevStep}
          disabled={step === 1}
          style={step === 1 ? { visibility: 'hidden' } : {}}
        >
          ← Back
        </button>
        {step < 4 ? (
          <button
            id="yt-next-btn"
            className="nav-btn next"
            onClick={handleNextStep}
            disabled={!canProceed()}
          >
            Next →
          </button>
        ) : null}
      </div>
    </div>
  );
}
