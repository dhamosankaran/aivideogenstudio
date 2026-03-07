import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
    fetchContentArticles,
    rankArticles,
    createDigestArticle,
    generateDigestScript,
    generateDigestVideo,
    getVoiceOptions,
    listDigestArticles,
} from '../services/dailyDigestApi';
import './ViralNews.css';
import './DailyDigest.css';

// ── Constants ─────────────────────────────────────────────────────

const DATE_RANGES = [
    { id: 'today', label: "Today's Feed" },
    { id: 'last_7_days', label: 'Last 7 Days' },
];

const DIGEST_DURATIONS = [
    { id: '60s', label: '60 Seconds', desc: '3 stories · Reels / TikTok pace', badge: null },
    { id: '90s', label: '90 Seconds', desc: '5 stories · Recommended for YouTube Shorts', badge: 'Recommended' },
];

const BACKGROUND_MODES = [
    { id: 'auto', label: '✨ Auto Mix', desc: 'Smart mix: videos → images → gradient fallback', badge: 'Recommended' },
    { id: 'images_only', label: '🖼️ Images Only', desc: null /* dynamic — see getImagesOnlyDesc() */ },
    { id: 'videos_only', label: '🎬 Videos Only', desc: 'Pexels stock videos for all scenes', badge: null },
];

// Returns the correct description for the Images Only mode based on current image source
const getImagesOnlyDesc = (imageSource) =>
    imageSource === 'ai_generated'
        ? 'Per-scene Gemini AI images with Ken Burns effect'
        : 'Per-scene stock images with Ken Burns effect';


const VEO_STYLES = [
    { id: 'auto', label: '✨ Auto', desc: 'Scene 3 → Whiteboard · Others → Illustration', badge: 'Recommended' },
    { id: 'cinematic', label: '🎬 Cinematic', desc: 'Real-world environments, dramatic camera', badge: null },
    { id: 'whiteboard', label: '✏️ Whiteboard', desc: 'Hand drawing on white canvas', badge: null },
    { id: 'illustration', label: '🎨 Illustration', desc: '2D flat diagrams & motion graphics', badge: null },
];

const IMAGE_SOURCES = [
    { id: 'stock', label: 'Stock (Pexels + Google)', desc: 'Free stock photo search' },
    { id: 'ai_generated', label: 'AI Generated (Gemini)', desc: 'Company-context aware images (beta)' },
];

const VIDEO_SOURCES = [
    { id: 'stock', label: 'Stock Videos (Pexels)', desc: 'Free stock video library' },
    { id: 'veo', label: 'Gemini Veo (Beta)', desc: 'AI-generated cinematic clips (~1min/scene)' },
];

const MAX_SELECT = 7;
const MIN_SELECT = 3;

// ── Scene tag helper ──────────────────────────────────────────────

function sceneTag(scene, totalScenes) {
    if (scene.scene_number === 1) return 'hook';
    if (scene.scene_number === totalScenes) return 'cta';
    if (scene.story_index && scene.story_index > 0) return `story ${scene.story_index}`;
    return 'insight';
}

function sceneCardClass(tag) {
    if (tag === 'hook') return 'vn-scene-card--hook';
    if (tag === 'cta') return 'vn-scene-card--cta';
    if (tag.startsWith('story')) return 'vn-scene-card--story';
    return '';
}

// ── Step indicator ────────────────────────────────────────────────

function StepIndicator({ step }) {
    const steps = ['Select', 'Rank', 'Script', 'Audio', 'Video'];
    return (
        <div className="vn-step-indicator">
            {steps.map((label, i) => (
                <React.Fragment key={label}>
                    <div className={`vn-step ${i + 1 < step ? 'done' : i + 1 === step ? 'active' : ''}`}>
                        <div className="vn-step-dot">{i + 1 < step ? '✓' : i + 1}</div>
                        <span className="vn-step-label">{label}</span>
                    </div>
                    {i < steps.length - 1 && (
                        <div className={`vn-step-line ${i + 1 < step ? 'done' : ''}`} />
                    )}
                </React.Fragment>
            ))}
        </div>
    );
}

// ── Source label helper ───────────────────────────────────────────

function getSourceLabel(article) {
    const raw = (article.source || '').trim();
    if (raw && raw.toUpperCase() !== 'UNKNOWN') return raw;
    try {
        const hostname = new URL(article.url || '').hostname;
        return hostname.replace(/^www\./, '') || null;
    } catch {
        return null;
    }
}

// ── Freshness badge helper ────────────────────────────────────────

function getFreshnessBadge(publishedAt) {
    if (!publishedAt) return null;
    const hours = (Date.now() - new Date(publishedAt).getTime()) / 3_600_000;
    if (hours < 24) return '<24h';
    if (hours < 48) return '<48h';
    return null;
}

// ── Selection progress bar ────────────────────────────────────────

function SelectionProgress({ selected, max, min }) {
    const state = selected === 0 ? 'empty' : selected < min ? 'below' : 'valid';
    const pct = Math.min((selected / max) * 100, 100);
    return (
        <div className="vn-sel-progress">
            <div className="vn-sel-progress-header">
                <span className={`vn-sel-label vn-sel-label--${state}`}>
                    {selected === 0
                        ? `Select ${min}–${max} articles for today's digest`
                        : selected < min
                            ? `${selected} selected — need ${min - selected} more`
                            : `${selected} / ${max} selected`}
                </span>
                <span className="vn-sel-segments">
                    {Array.from({ length: max }, (_, i) => (
                        <span
                            key={i}
                            className={`vn-sel-seg ${i < selected ? (state === 'below' ? 'amber' : 'green') : ''}`}
                        />
                    ))}
                </span>
            </div>
            <div className="vn-sel-bar">
                <div className={`vn-sel-fill vn-sel-fill--${state}`} style={{ width: `${pct}%` }} />
            </div>
        </div>
    );
}

// ── Article card for selection ────────────────────────────────────

function ArticleCard({ article, selected, onToggle }) {
    const isSelected = selected.has(article.id);
    const limitReached = !isSelected && selected.size >= MAX_SELECT;
    const selectionOrder = isSelected ? [...selected].indexOf(article.id) + 1 : null;

    const sourceLabel = getSourceLabel(article);
    const desc = (article.description || '').trim();
    const hasDesc = desc.length >= 15;
    const freshBadge = getFreshnessBadge(article.published_at);

    return (
        <div
            className={`vn-article-card ${isSelected ? 'selected' : ''} ${limitReached ? 'disabled' : ''}`}
            onClick={() => !limitReached && onToggle(article.id)}
        >
            {isSelected && (
                <div className="vn-article-check" title={`Selection #${selectionOrder}`}>
                    {selectionOrder}
                </div>
            )}
            <div className="vn-article-meta">
                {sourceLabel
                    ? <span className="vn-article-source">{sourceLabel}</span>
                    : <span className="vn-article-source vn-article-source--hidden" />
                }
                <span className="vn-article-date">
                    {article.published_at
                        ? new Date(article.published_at).toLocaleDateString()
                        : ''}
                </span>
            </div>
            <h4 className="vn-article-title">{article.title}</h4>
            {hasDesc
                ? <p className="vn-article-desc">{desc.slice(0, 140)}{desc.length > 140 ? '…' : ''}</p>
                : <p className="vn-article-desc vn-article-desc--empty">No preview available</p>
            }
            <div className="vn-article-footer">
                {freshBadge && <span className="vn-badge vn-badge-fresh">{freshBadge}</span>}
                {isSelected && <span className="vn-badge vn-badge-selected">#{selectionOrder}</span>}
            </div>
        </div>
    );
}

// ── Ranked article row ────────────────────────────────────────────

function RankedRow({ item, index, total, isCut, onMoveUp, onMoveDown }) {
    return (
        <div className={`vn-ranked-row ${isCut ? 'vn-ranked-row--cut' : ''}`}>
            <div className="vn-rank-badge">#{item.rank}</div>
            <div className="vn-ranked-body">
                <div className="vn-ranked-title">{item.title}</div>
                <div className="vn-ranked-meta">
                    <span className="vn-tag">{item.company}</span>
                    <span className="vn-ranked-reason">{item.rank_reason}</span>
                </div>
                <div className="vn-ranked-facts">
                    <strong>Key fact:</strong> {item.key_fact}
                    {item.impact && <> · <strong>Impact:</strong> {item.impact}</>}
                </div>
                <div className="vn-ranked-score">
                    Impact score: <strong>{(item.impact_score || 0).toFixed(1)}/10</strong>
                </div>
            </div>
            <div className="vn-ranked-controls">
                <button disabled={index === 0} onClick={() => onMoveUp(index)} title="Move up">↑</button>
                <button disabled={index === total - 1} onClick={() => onMoveDown(index)} title="Move down">↓</button>
            </div>
        </div>
    );
}

// ── Main component ────────────────────────────────────────────────

export default function DailyDigest() {
    const [searchParams] = useSearchParams();
    const [step, setStep] = useState(1);
    const [autoRanking, setAutoRanking] = useState(false);

    // Step 1: article selection
    const [articles, setArticles] = useState([]);
    const [selectedIds, setSelectedIds] = useState(new Set());
    const [dateRange, setDateRange] = useState('today');
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoadingArticles, setIsLoadingArticles] = useState(false);
    const [articleError, setArticleError] = useState(null);

    // Past digests sidebar
    const [pastDigests, setPastDigests] = useState([]);

    // Step 2: ranking
    const [rankedArticles, setRankedArticles] = useState([]);
    const [digestTitle, setDigestTitle] = useState('');
    const [isRanking, setIsRanking] = useState(false);
    const [rankError, setRankError] = useState(null);

    // Step 3: script
    const [digestArticleId, setDigestArticleId] = useState(null);
    const [scriptData, setScriptData] = useState(null);
    const [videoDuration, setVideoDuration] = useState('90s');
    const [scriptAccepted, setScriptAccepted] = useState(false);
    const [isGeneratingScript, setIsGeneratingScript] = useState(false);
    const [scriptError, setScriptError] = useState(null);

    // Step 4: TTS + video options
    const [voiceOptions, setVoiceOptions] = useState(null);
    const [selectedProvider, setSelectedProvider] = useState('openai');
    const [selectedVoice, setSelectedVoice] = useState('onyx');
    const [backgroundMode, setBackgroundMode] = useState('auto');
    const [imageSource, setImageSource] = useState('ai_generated');
    const [videoSource, setVideoSource] = useState('stock');
    const [veoStyle, setVeoStyle] = useState('auto');

    // Step 5: video
    const [videoResult, setVideoResult] = useState(null);
    const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
    const [generationStep, setGenerationStep] = useState('');
    const [videoError, setVideoError] = useState(null);

    // ── Load articles ──────────────────────────────────────────────

    const loadArticles = useCallback(async () => {
        setIsLoadingArticles(true);
        setArticleError(null);
        try {
            const data = await fetchContentArticles({
                dateRange,
                search: searchQuery || null,
                pageSize: 50,
            });
            setArticles(data.items || []);
        } catch (e) {
            setArticleError(e.message);
        } finally {
            setIsLoadingArticles(false);
        }
    }, [dateRange, searchQuery]);

    useEffect(() => { loadArticles(); }, [loadArticles]);

    useEffect(() => {
        listDigestArticles(5).then(setPastDigests).catch(() => { });
    }, []);

    // Auto-rank articles pre-selected from Content Library (via ?article_ids=1,2,3)
    useEffect(() => {
        const idsParam = searchParams.get('article_ids');
        if (!idsParam) return;
        const ids = idsParam.split(',').map(Number).filter(Boolean);
        if (ids.length < 2) return;

        setSelectedIds(new Set(ids));
        setAutoRanking(true);
        rankArticles(ids)
            .then(ranked => {
                const withRank = ranked.map((item, i) => ({ ...item, rank: i + 1 }));
                setRankedArticles(withRank);
                const today = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                setDigestTitle(`${withRank.length} AI Stories — ${today}`);
                setStep(2);
            })
            .catch(e => setRankError(e.message))
            .finally(() => setAutoRanking(false));
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // ── Load voice options ─────────────────────────────────────────

    useEffect(() => {
        getVoiceOptions('daily_update').then(opts => {
            setVoiceOptions(opts);
            const provider = opts?.default_provider || 'openai';
            setSelectedProvider(provider);
            const defVoice = opts?.providers?.find(p => p.id === provider)?.default_voice;
            if (defVoice) setSelectedVoice(defVoice);
        }).catch(() => { });
    }, []);

    // ── Sync voice when provider changes ──────────────────────────

    useEffect(() => {
        const defVoice = voiceOptions?.providers?.find(p => p.id === selectedProvider)?.default_voice;
        if (defVoice) setSelectedVoice(defVoice);
    }, [selectedProvider, voiceOptions]);

    // ── Article selection toggle ───────────────────────────────────

    const toggleArticle = useCallback((id) => {
        setSelectedIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else if (next.size < MAX_SELECT) next.add(id);
            return next;
        });
    }, []);

    // ── Step 1 → 2: rank ─────────────────────────────────────────

    const handleRank = async () => {
        if (selectedIds.size < 2) return;
        setIsRanking(true);
        setRankError(null);
        try {
            const ranked = await rankArticles([...selectedIds]);
            // Set rank order in items
            const withRank = ranked.map((item, i) => ({ ...item, rank: i + 1 }));
            setRankedArticles(withRank);

            // Auto-suggest title
            const today = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const count = withRank.length;
            setDigestTitle(`${count} AI Stories — ${today}`);

            setStep(2);
        } catch (e) {
            setRankError(e.message);
        } finally {
            setIsRanking(false);
        }
    };

    // ── Step 2 reordering ─────────────────────────────────────────

    const moveRankedItem = (index, direction) => {
        const swapIndex = index + direction;
        if (swapIndex < 0 || swapIndex >= rankedArticles.length) return;
        const next = [...rankedArticles];
        [next[index], next[swapIndex]] = [next[swapIndex], next[index]];
        setRankedArticles(next.map((item, i) => ({ ...item, rank: i + 1 })));
    };

    // ── Step 2 → 3: create digest + generate script ───────────────

    const handleCreateAndScript = async () => {
        if (!digestTitle.trim()) return;
        setIsGeneratingScript(true);
        setScriptError(null);
        try {
            // Create digest article
            const rankedIds = rankedArticles.map(r => r.article_id);
            const digestResp = await createDigestArticle(rankedIds, digestTitle, rankedArticles);
            setDigestArticleId(digestResp.article_id);

            // Generate script
            const durationToUse = selectedIds.size <= 3 ? '60s' : videoDuration;
            const script = await generateDigestScript(digestResp.article_id, durationToUse);
            setScriptData(script);
            setScriptAccepted(false);
            setStep(3);
        } catch (e) {
            setScriptError(e.message);
        } finally {
            setIsGeneratingScript(false);
        }
    };

    // ── Step 3 → 4: regenerate script ────────────────────────────

    const handleRegenerateScript = async () => {
        if (!digestArticleId) return;
        setIsGeneratingScript(true);
        setScriptError(null);
        setScriptAccepted(false);
        try {
            const script = await generateDigestScript(digestArticleId, videoDuration);
            setScriptData(script);
        } catch (e) {
            setScriptError(e.message);
        } finally {
            setIsGeneratingScript(false);
        }
    };

    // ── Step 4 → 5: generate video ────────────────────────────────

    const handleGenerateVideo = async () => {
        if (!digestArticleId || !scriptAccepted) return;
        setIsGeneratingVideo(true);
        setVideoError(null);
        setGenerationStep('Generating TTS audio…');

        try {
            setGenerationStep('Composing video scenes…');
            const result = await generateDigestVideo(digestArticleId, {
                scriptId: scriptData?.script_id,
                ttsProvider: selectedProvider,
                voice: selectedVoice,
                backgroundMode,
                imageSource,
                videoSource,
                videoDuration,
                veoStyle,
            });
            setVideoResult(result);
            setGenerationStep('');
            setStep(5);
        } catch (e) {
            setVideoError(e.message);
            setGenerationStep('');
        } finally {
            setIsGeneratingVideo(false);
        }
    };

    // ── Reset ─────────────────────────────────────────────────────

    const handleReset = () => {
        setStep(1);
        setSelectedIds(new Set());
        setRankedArticles([]);
        setDigestTitle('');
        setDigestArticleId(null);
        setScriptData(null);
        setScriptAccepted(false);
        setVideoResult(null);
        setVideoError(null);
        setScriptError(null);
        setRankError(null);
        listDigestArticles(5).then(setPastDigests).catch(() => { });
    };

    // ── Render ────────────────────────────────────────────────────

    return (
        <div className="vn-layout">
            {/* Left panel */}
            <div className="vn-left">
                <div className="vn-header">
                    <h2 className="vn-title">📡 Daily AI Digest</h2>
                    {step === 1 && (
                        <p className="vn-subtitle">
                            Pick today's top AI stories → LLM ranks them → Generate a roundup Short
                        </p>
                    )}
                </div>
                <StepIndicator step={step} />

                {/* ── STEP 1: Select articles ─────────────────── */}
                {step === 1 && (
                    <div className="vn-section">
                        <div className="vn-controls-row">
                            <div className="vn-filter-row">
                                {DATE_RANGES.map(d => (
                                    <button
                                        key={d.id}
                                        className={`vn-category-btn ${dateRange === d.id ? 'active' : ''}`}
                                        onClick={() => setDateRange(d.id)}
                                    >
                                        {d.label}
                                    </button>
                                ))}
                            </div>
                            <input
                                className="vn-search"
                                type="text"
                                placeholder="Search articles…"
                                value={searchQuery}
                                onChange={e => setSearchQuery(e.target.value)}
                            />
                        </div>

                        <SelectionProgress selected={selectedIds.size} max={MAX_SELECT} min={MIN_SELECT} />

                        {articleError && <div className="vn-error">{articleError}</div>}

                        {isLoadingArticles ? (
                            <div className="vn-loading"><div className="vn-spinner" /> Loading articles…</div>
                        ) : (
                            <div className="vn-article-grid">
                                {articles.length === 0
                                    ? <div className="vn-empty">No articles found. Fetch from RSS first.</div>
                                    : articles.map(article => (
                                        <ArticleCard
                                            key={article.id}
                                            article={article}
                                            selected={selectedIds}
                                            onToggle={toggleArticle}
                                        />
                                    ))
                                }
                            </div>
                        )}

                        {rankError && <div className="vn-error">{rankError}</div>}

                        {autoRanking && (
                            <div className="vn-loading">
                                <div className="vn-spinner" />
                                Ranking {selectedIds.size} articles from Content Library…
                            </div>
                        )}

                        <div className="vn-step-actions">
                            <button
                                className="vn-btn-primary"
                                onClick={handleRank}
                                disabled={selectedIds.size < 2 || isRanking || autoRanking}
                            >
                                {isRanking
                                    ? <><span className="vn-spinner" /> Ranking…</>
                                    : `✨ Rank & Prioritize (${selectedIds.size} selected)`}
                            </button>
                        </div>
                    </div>
                )}

                {/* ── STEP 2: Review ranking ──────────────────── */}
                {step === 2 && (
                    <div className="vn-section">
                        <div className="vn-ranked-list">
                            {(() => {
                                const cutoff = videoDuration === '60s' ? 3 : 5;
                                return rankedArticles.map((item, i) => (
                                    <React.Fragment key={item.article_id}>
                                        {i === cutoff && rankedArticles.length > cutoff && (
                                            <div className="vn-rank-cutoff">
                                                <span className="vn-rank-cutoff-label">↑ Included · ↓ May be cut</span>
                                            </div>
                                        )}
                                        <RankedRow
                                            item={item}
                                            index={i}
                                            total={rankedArticles.length}
                                            isCut={i >= cutoff}
                                            onMoveUp={() => moveRankedItem(i, -1)}
                                            onMoveDown={() => moveRankedItem(i, 1)}
                                        />
                                    </React.Fragment>
                                ));
                            })()}
                        </div>

                        <div className="vn-vo-section">
                            <label className="vn-vo-label">Digest Title</label>
                            <input
                                className="vn-search"
                                type="text"
                                value={digestTitle}
                                onChange={e => setDigestTitle(e.target.value)}
                                placeholder="e.g. 5 AI Stories — Mar 3"
                            />

                            <label className="vn-vo-label" style={{ marginTop: 16 }}>Duration</label>
                            <div className="vn-tts-grid vn-duration-grid">
                                {DIGEST_DURATIONS.filter(d =>
                                    d.id === '60s'
                                        ? rankedArticles.length >= 3
                                        : rankedArticles.length >= 5
                                ).map(d => (
                                    <label key={d.id} className={`vn-tts-card ${videoDuration === d.id ? 'selected' : ''}`}>
                                        <input
                                            type="radio"
                                            name="duration"
                                            value={d.id}
                                            checked={videoDuration === d.id}
                                            onChange={() => setVideoDuration(d.id)}
                                        />
                                        <div className="vn-tts-text">
                                            <span className="vn-tts-name">{d.label}</span>
                                            <span className="vn-tts-cost">{d.desc}</span>
                                        </div>
                                        {d.badge && <span className="vn-tts-rec">{d.badge}</span>}
                                    </label>
                                ))}
                            </div>
                        </div>

                        {scriptError && <div className="vn-error">{scriptError}</div>}

                        <div className="vn-step-actions">
                            <button className="vn-btn-secondary" onClick={() => setStep(1)}>← Back</button>
                            <button
                                className="vn-btn-primary"
                                onClick={handleCreateAndScript}
                                disabled={!digestTitle.trim() || isGeneratingScript}
                            >
                                {isGeneratingScript
                                    ? <><span className="vn-spinner" /> Generating Script…</>
                                    : '🎬 Generate Script →'}
                            </button>
                        </div>
                    </div>
                )}

                {/* ── STEP 3: Script ──────────────────────────── */}
                {step === 3 && (
                    <div className="vn-section">
                        {/* Script overview banner */}
                        {scriptData && (
                            <div className="vn-script-banner">
                                {scriptData.catchy_title && (
                                    <div className="vn-script-banner-title">"{scriptData.catchy_title}"</div>
                                )}
                                <div className="vn-script-banner-stats">
                                    <span>{scriptData.scenes?.length || '—'} scenes</span>
                                    <span className="vn-script-banner-dot">·</span>
                                    <span>{scriptData.word_count || '—'} words</span>
                                    <span className="vn-script-banner-dot">·</span>
                                    <span>{scriptData.estimated_duration ? `~${scriptData.estimated_duration.toFixed(0)}s` : '—'}</span>
                                </div>
                            </div>
                        )}

                        {scriptData?.scenes && (
                            <div className="vn-scenes">
                                {scriptData.scenes.map(scene => {
                                    const tag = sceneTag(scene, scriptData.scenes.length);
                                    return (
                                        <div key={scene.scene_number} className={`vn-scene-card ${sceneCardClass(tag)}`}>
                                            <div className="vn-scene-header">
                                                <span className="vn-scene-num">Scene {scene.scene_number}</span>
                                                <span className="vn-scene-tag vn-tag">{tag}</span>
                                                {scene.company && (
                                                    <span className="vn-scene-company">{scene.company}</span>
                                                )}
                                            </div>
                                            <p className="vn-scene-text">{scene.text}</p>
                                            {scene.visual_cues && (
                                                <div className="vn-scene-visual">🎥 {scene.visual_cues}</div>
                                            )}
                                            {scene.image_keywords?.length > 0 && (
                                                <div className="vn-scene-keywords">
                                                    🔍 {scene.image_keywords.join(' · ')}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {scriptData && (
                            <div className="vn-script-stats">
                                <span>{scriptData.word_count || '—'} words</span>
                                <span>{scriptData.estimated_duration ? `~${scriptData.estimated_duration.toFixed(0)}s` : '—'}</span>
                                <span>{scriptData.scenes?.length || '—'} scenes</span>
                            </div>
                        )}

                        {scriptError && <div className="vn-error">{scriptError}</div>}

                        {/* Sticky approve bar — always visible at bottom of viewport */}
                        <div className={`vn-sticky-accept ${scriptAccepted ? 'accepted' : ''}`}>
                            <button
                                className={`vn-accept-btn ${scriptAccepted ? 'accepted' : ''}`}
                                type="button"
                                onClick={() => setScriptAccepted(v => !v)}
                            >
                                {scriptAccepted
                                    ? <><span className="vn-accept-check-icon">✓</span> Script Approved</>
                                    : <>Approve Script</>
                                }
                            </button>
                            <button
                                className="vn-btn-secondary"
                                onClick={handleRegenerateScript}
                                disabled={isGeneratingScript}
                            >
                                {isGeneratingScript ? <><span className="vn-spinner" /> Regenerating…</> : '↻ Regenerate'}
                            </button>
                            <button
                                className="vn-btn-primary"
                                disabled={!scriptAccepted}
                                onClick={() => setStep(4)}
                            >
                                Audio &amp; Video →
                            </button>
                        </div>

                        <div className="vn-step-actions">
                            <button className="vn-btn-secondary" onClick={() => setStep(2)}>← Back</button>
                        </div>
                    </div>
                )}

                {/* ── STEP 4: Audio & Video settings ─────────── */}
                {step === 4 && (
                    <div className="vn-section">
                        {/* ── Voice & TTS ── */}
                        <div className="vn-vo-section">
                            <h4 className="vn-subsection-title">🎤 Voice & TTS Settings</h4>

                            <label className="vn-vo-label">TTS Provider</label>
                            <div className="vn-tts-grid">
                                {(voiceOptions?.providers || [
                                    { id: 'openai', name: 'OpenAI', cost_label: '~$0.02/video', default_voice: 'onyx' },
                                    { id: 'google', name: 'Google TTS', cost_label: '~$0.01/video', default_voice: 'en-US-Journey-D' },
                                    { id: 'elevenlabs', name: 'ElevenLabs', cost_label: '~$0.15/video', default_voice: 'Brian' },
                                ]).map(p => (
                                    <label key={p.id} className={`vn-tts-card ${selectedProvider === p.id ? 'selected' : ''}`}>
                                        <input
                                            type="radio"
                                            name="tts"
                                            value={p.id}
                                            checked={selectedProvider === p.id}
                                            onChange={() => setSelectedProvider(p.id)}
                                        />
                                        <div className="vn-tts-text">
                                            <span className="vn-tts-name">{p.name}</span>
                                            <span className="vn-tts-cost">{p.cost_label}</span>
                                        </div>
                                        {(voiceOptions?.default_provider || 'openai') === p.id && (
                                            <span className="vn-tts-rec">✨ Recommended</span>
                                        )}
                                    </label>
                                ))}
                            </div>

                            <label className="vn-vo-label">Voice</label>
                            <div className="vn-voice-wrap">
                                <select
                                    className="vn-select"
                                    value={selectedVoice || ''}
                                    onChange={e => setSelectedVoice(e.target.value)}
                                >
                                    {(voiceOptions?.voices?.[selectedProvider] || [
                                        { id: 'onyx', name: 'Onyx', tone: 'Deep & authoritative' },
                                        { id: 'echo', name: 'Echo', tone: 'Confident & professional' },
                                        { id: 'nova', name: 'Nova', tone: 'Warm & clear' },
                                        { id: 'alloy', name: 'Alloy', tone: 'Neutral & versatile' },
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
                        </div>

                        {/* ── Visual Settings ── */}
                        <div className="vn-vo-section" style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '1.5rem' }}>
                            <h4 className="vn-subsection-title">🎨 Visual Settings</h4>

                            {/* Image Source */}
                            <label className="vn-vo-label">Image Source</label>
                            <div className="vn-tts-grid">
                                {IMAGE_SOURCES.map(s => (
                                    <label key={s.id} className={`vn-tts-card ${imageSource === s.id ? 'selected' : ''}`}>
                                        <input
                                            type="radio"
                                            name="img-src"
                                            value={s.id}
                                            checked={imageSource === s.id}
                                            onChange={() => {
                                                setImageSource(s.id);
                                                // Auto-sync background mode: AI images → images_only, stock → restore auto
                                                if (s.id === 'ai_generated') setBackgroundMode('images_only');
                                                else if (backgroundMode === 'images_only') setBackgroundMode('auto');
                                            }}
                                        />
                                        <div className="vn-tts-text">
                                            <span className="vn-tts-name">{s.label}</span>
                                            <span className="vn-tts-cost">{s.desc}</span>
                                        </div>
                                        {s.id === 'ai_generated' && <span className="vn-tts-rec" style={{ background: 'rgba(99,102,241,0.15)', color: '#818cf8' }}>🧪 Beta</span>}
                                    </label>
                                ))}
                            </div>

                            {/* Video Background */}
                            <label className="vn-vo-label">Video Background</label>
                            <div className="vn-tts-grid">
                                {VIDEO_SOURCES.map(s => (
                                    <label key={s.id} className={`vn-tts-card ${videoSource === s.id ? 'selected' : ''}`}>
                                        <input
                                            type="radio"
                                            name="vid-src"
                                            value={s.id}
                                            checked={videoSource === s.id}
                                            onChange={() => setVideoSource(s.id)}
                                        />
                                        <div className="vn-tts-text">
                                            <span className="vn-tts-name">{s.label}</span>
                                            <span className="vn-tts-cost">{s.desc}</span>
                                        </div>
                                        {s.id === 'veo' && <span className="vn-tts-rec" style={{ background: 'rgba(99,102,241,0.15)', color: '#818cf8' }}>🧪 Beta</span>}
                                    </label>
                                ))}
                            </div>

                            {/* Veo Style — only shown when Veo video source selected */}
                            {videoSource === 'veo' && (
                                <>
                                    <label className="vn-vo-label">Veo Style</label>
                                    <div className="vn-tts-grid">
                                        {VEO_STYLES.map(s => (
                                            <label key={s.id} className={`vn-tts-card ${veoStyle === s.id ? 'selected' : ''}`}>
                                                <input
                                                    type="radio"
                                                    name="veo-style"
                                                    value={s.id}
                                                    checked={veoStyle === s.id}
                                                    onChange={() => setVeoStyle(s.id)}
                                                />
                                                <div className="vn-tts-text">
                                                    <span className="vn-tts-name">{s.label}</span>
                                                    <span className="vn-tts-cost">{s.desc}</span>
                                                </div>
                                                {s.badge && <span className="vn-tts-rec">{s.badge}</span>}
                                            </label>
                                        ))}
                                    </div>
                                </>
                            )}

                            {/* Background Mode */}
                            <label className="vn-vo-label">Background Mode</label>
                            <div className="vn-tts-grid">
                                {BACKGROUND_MODES.map(m => (
                                    <label key={m.id} className={`vn-tts-card ${backgroundMode === m.id ? 'selected' : ''}`}>
                                        <input
                                            type="radio"
                                            name="bg"
                                            value={m.id}
                                            checked={backgroundMode === m.id}
                                            onChange={() => setBackgroundMode(m.id)}
                                        />
                                        <div className="vn-tts-text">
                                            <span className="vn-tts-name">{m.label}</span>
                                            <span className="vn-tts-cost">
                                                {m.id === 'images_only' ? getImagesOnlyDesc(imageSource) : m.desc}
                                            </span>
                                        </div>
                                        {m.badge && <span className="vn-tts-rec">{m.badge}</span>}
                                    </label>
                                ))}
                            </div>

                            {/* Cost estimate */}
                            <div className="vn-cost-row">
                                <span className="vn-cost-label">Estimated cost</span>
                                <span className="vn-cost-val">
                                    {selectedProvider === 'elevenlabs'
                                        ? '~$0.17'
                                        : selectedProvider === 'google'
                                            ? '~$0.02'
                                            : '~$0.04'}
                                    {imageSource === 'ai_generated' ? ' + Gemini images' : ''}
                                    {videoSource === 'veo' ? ' + Veo' : ''}
                                </span>
                            </div>
                        </div>

                        {videoError && <div className="vn-error">{videoError}</div>}

                        <div className="vn-step-actions">
                            <button className="vn-btn-secondary" onClick={() => setStep(3)}>← Back</button>
                            <button
                                className="vn-btn-generate-video"
                                onClick={handleGenerateVideo}
                                disabled={isGeneratingVideo}
                            >
                                {isGeneratingVideo ? (
                                    <><span className="vn-spinner" />{generationStep || 'Processing…'}</>
                                ) : (
                                    <>🚀 Generate Digest Video ({selectedProvider} / {selectedVoice}{imageSource === 'ai_generated' ? ' / AI Images' : ''}{videoSource === 'veo' ? ' / Veo' : ''})</>
                                )}
                            </button>
                        </div>
                    </div>
                )}

                {/* ── STEP 5: Done ────────────────────────────── */}
                {step === 5 && videoResult && (
                    <div className="vn-section">
                        <div className="vn-success-card">
                            <div className="vn-success-icon">🎬</div>
                            <h3 className="vn-success-title">Daily Digest Rendering!</h3>
                            <p className="vn-success-sub">
                                Your {videoDuration} digest with {rankedArticles.length} stories is being composed.
                                Check the <strong>Video Validation</strong> page.
                            </p>
                            <div className="vn-result-meta">
                                <span>Video ID: {videoResult.video_id}</span>
                                <span>Script ID: {videoResult.script_id}</span>
                                <span>TTS: {videoResult.tts_provider} · {videoResult.voice}</span>
                            </div>
                        </div>

                        <div className="vn-step-actions">
                            <button className="vn-btn-primary" onClick={handleReset}>
                                + Create Another Digest
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Right panel — context-sensitive per step */}
            <div className="vn-right">
                {(step === 1 || step === 5) && (
                    <>
                        <div className="vn-panel-header">
                            <h3 className="vn-panel-title">Recent Digests</h3>
                        </div>
                        {pastDigests.length === 0 ? (
                            <div className="vn-panel-empty">No digests yet — create your first one!</div>
                        ) : (
                            <div className="vn-saved-list">
                                {pastDigests.map(d => (
                                    <div key={d.article_id} className="vn-saved-item">
                                        <div className="vn-saved-title">{d.title}</div>
                                        <div className="vn-saved-meta">
                                            {d.story_count} stories ·{' '}
                                            {d.created_at ? new Date(d.created_at).toLocaleDateString() : ''}
                                            {d.has_script && (
                                                <span className="vn-badge vn-badge-selected" style={{ marginLeft: 8 }}>
                                                    Script ✓
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </>
                )}

                {step === 2 && (
                    <>
                        <div className="vn-panel-header">
                            <h3 className="vn-panel-title">Stories Preview</h3>
                        </div>
                        <div className="vn-panel-preview">
                            {digestTitle && (
                                <div className="vn-panel-digest-title">{digestTitle}</div>
                            )}
                            <div className="vn-panel-stat-row">
                                <span className="vn-panel-stat-label">Stories ranked</span>
                                <span className="vn-panel-stat-val">{rankedArticles.length}</span>
                            </div>
                            <div className="vn-panel-stat-row">
                                <span className="vn-panel-stat-label">Will be included</span>
                                <span className="vn-panel-stat-val vn-panel-stat-val--green">
                                    {Math.min(videoDuration === '60s' ? 3 : 5, rankedArticles.length)}
                                </span>
                            </div>
                            {rankedArticles.length > (videoDuration === '60s' ? 3 : 5) && (
                                <div className="vn-panel-stat-row">
                                    <span className="vn-panel-stat-label">May be cut</span>
                                    <span className="vn-panel-stat-val vn-panel-stat-val--muted">
                                        {rankedArticles.length - (videoDuration === '60s' ? 3 : 5)}
                                    </span>
                                </div>
                            )}
                            <div className="vn-panel-hint">
                                Use ↑↓ arrows to reorder. Top stories run first in the video.
                            </div>
                        </div>
                    </>
                )}

                {step === 3 && (
                    <>
                        <div className="vn-panel-header">
                            <h3 className="vn-panel-title">Script Summary</h3>
                        </div>
                        {scriptData ? (
                            <div className="vn-panel-preview">
                                <div className="vn-panel-stat-row">
                                    <span className="vn-panel-stat-label">Words</span>
                                    <span className="vn-panel-stat-val">{scriptData.word_count || '—'}</span>
                                </div>
                                <div className="vn-panel-stat-row">
                                    <span className="vn-panel-stat-label">Scenes</span>
                                    <span className="vn-panel-stat-val">{scriptData.scenes?.length || '—'}</span>
                                </div>
                                <div className="vn-panel-stat-row">
                                    <span className="vn-panel-stat-label">Duration</span>
                                    <span className="vn-panel-stat-val">
                                        {scriptData.estimated_duration ? `~${scriptData.estimated_duration.toFixed(0)}s` : '—'}
                                    </span>
                                </div>
                                {scriptData.catchy_title && (
                                    <div className="vn-panel-hint vn-panel-hint--title">
                                        "{scriptData.catchy_title}"
                                    </div>
                                )}
                                {scriptAccepted && (
                                    <div className="vn-panel-accepted">✓ Script approved</div>
                                )}
                            </div>
                        ) : (
                            <div className="vn-panel-empty">Generating script…</div>
                        )}
                    </>
                )}

                {step === 4 && (
                    <>
                        <div className="vn-panel-header">
                            <h3 className="vn-panel-title">Generation Preview</h3>
                        </div>
                        <div className="vn-panel-preview">
                            <div className="vn-panel-stat-row">
                                <span className="vn-panel-stat-label">Voice</span>
                                <span className="vn-panel-stat-val">{selectedProvider} / {selectedVoice}</span>
                            </div>
                            <div className="vn-panel-stat-row">
                                <span className="vn-panel-stat-label">Images</span>
                                <span className="vn-panel-stat-val">
                                    {imageSource === 'ai_generated' ? 'AI (Gemini)' : 'Stock'}
                                </span>
                            </div>
                            <div className="vn-panel-stat-row">
                                <span className="vn-panel-stat-label">Video BG</span>
                                <span className="vn-panel-stat-val">
                                    {videoSource === 'veo' ? 'Veo (AI)' : 'Stock'}
                                </span>
                            </div>
                            <div className="vn-panel-stat-row">
                                <span className="vn-panel-stat-label">Background</span>
                                <span className="vn-panel-stat-val">{backgroundMode}</span>
                            </div>
                            <div className="vn-panel-stat-row">
                                <span className="vn-panel-stat-label">Stories</span>
                                <span className="vn-panel-stat-val">{rankedArticles.length}</span>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
