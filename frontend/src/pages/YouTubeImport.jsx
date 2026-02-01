import { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import {
    analyzeYouTubeVideo,
    getYouTubeSources,
    getYouTubeSource,
    createShortFromInsight,
    getVideoSummary,
    generateModeA,
    generateModeB
} from '../services/youtubeApi';
import './YouTubeImport.css';

function YouTubeImport() {
    const { navigateTo } = useProject();

    // State
    const [youtubeUrl, setYoutubeUrl] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [sources, setSources] = useState([]);
    const [selectedSource, setSelectedSource] = useState(null);
    const [selectedInsights, setSelectedInsights] = useState(new Set());
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);
    const [pollingId, setPollingId] = useState(null);

    // New state for enhanced features
    const [showSummaryModal, setShowSummaryModal] = useState(false);
    const [videoSummary, setVideoSummary] = useState(null);
    const [isLoadingSummary, setIsLoadingSummary] = useState(false);
    const [generatingInsight, setGeneratingInsight] = useState(null); // {index, mode}
    const [generationProgress, setGenerationProgress] = useState({});

    // Load existing sources on mount
    useEffect(() => {
        loadSources();
    }, []);

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            if (pollingId) clearInterval(pollingId);
        };
    }, [pollingId]);

    const loadSources = async () => {
        try {
            const data = await getYouTubeSources(20);
            setSources(data);
        } catch (err) {
            console.error('Failed to load sources:', err);
        }
    };

    const handleAnalyze = async () => {
        if (!youtubeUrl.trim()) {
            setError('Please enter a YouTube URL');
            return;
        }

        setIsAnalyzing(true);
        setError(null);
        setSuccessMessage(null);

        try {
            const source = await analyzeYouTubeVideo(youtubeUrl);
            setSelectedSource(source);
            setYoutubeUrl('');

            // Start polling for analysis completion
            startPolling(source.id);

        } catch (err) {
            setError(err.message);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const startPolling = (sourceId) => {
        // Clear any existing polling
        if (pollingId) clearInterval(pollingId);

        const id = setInterval(async () => {
            try {
                const source = await getYouTubeSource(sourceId);
                setSelectedSource(source);

                // Stop polling when analysis is complete
                if (source.analysis_status === 'completed' || source.analysis_status === 'failed') {
                    clearInterval(id);
                    setPollingId(null);
                    loadSources(); // Refresh the source list
                }
            } catch (err) {
                console.error('Polling error:', err);
                clearInterval(id);
                setPollingId(null);
            }
        }, 2000);

        setPollingId(id);
    };

    const handleSelectSource = async (source) => {
        try {
            const fullSource = await getYouTubeSource(source.id);
            setSelectedSource(fullSource);
            setSelectedInsights(new Set());

            // Resume polling if still analyzing
            if (fullSource.analysis_status === 'analyzing') {
                startPolling(fullSource.id);
            }
        } catch (err) {
            setError(err.message);
        }
    };

    const handleToggleInsight = (index) => {
        const newSelected = new Set(selectedInsights);
        if (newSelected.has(index)) {
            newSelected.delete(index);
        } else {
            newSelected.add(index);
        }
        setSelectedInsights(newSelected);
    };

    const handleCreateShort = async (insightIndex, mode) => {
        if (!selectedSource) return;

        try {
            const result = await createShortFromInsight(selectedSource.id, insightIndex, mode);
            setSuccessMessage(`Created ${mode === 'A' ? 'Clip + Commentary' : 'Original'} article! Redirecting...`);

            // Navigate to content library after short delay
            setTimeout(() => {
                navigateTo('content');
            }, 1500);

        } catch (err) {
            setError(err.message);
        }
    };

    // New handlers for Mode A and Mode B
    const handleViewSummary = async () => {
        if (!selectedSource) return;

        setIsLoadingSummary(true);
        setShowSummaryModal(true);

        try {
            const data = await getVideoSummary(selectedSource.id);
            setVideoSummary(data);
        } catch (err) {
            setError(err.message);
            setShowSummaryModal(false);
        } finally {
            setIsLoadingSummary(false);
        }
    };

    const handleModeA = async (insightIndex) => {
        if (!selectedSource) return;

        setGeneratingInsight({ index: insightIndex, mode: 'A' });
        setGenerationProgress({ [insightIndex]: 'downloading' });

        try {
            setGenerationProgress({ [insightIndex]: 'generating script' });
            const result = await generateModeA(selectedSource.id, insightIndex, {
                commentaryStyle: 'reaction',
                autoApprove: true
            });

            setGenerationProgress({ [insightIndex]: 'rendering video' });
            setSuccessMessage('Mode A video started! Redirecting to validation...');

            setTimeout(() => {
                navigateTo('validation');
            }, 1500);

        } catch (err) {
            setError(err.message);
        } finally {
            setGeneratingInsight(null);
            setGenerationProgress({});
        }
    };

    const handleModeB = async (insightIndex) => {
        if (!selectedSource) return;

        setGeneratingInsight({ index: insightIndex, mode: 'B' });

        try {
            const result = await generateModeB(selectedSource.id, insightIndex, {
                contentType: 'daily_update'
            });

            setSuccessMessage('Script created! Redirecting to Script Review...');

            setTimeout(() => {
                navigateTo('scripts');
            }, 1500);

        } catch (err) {
            setError(err.message);
        } finally {
            setGeneratingInsight(null);
        }
    };

    const handleCreateBulkShorts = async (mode) => {
        if (!selectedSource || selectedInsights.size === 0) return;

        try {
            for (const index of selectedInsights) {
                await createShortFromInsight(selectedSource.id, index, mode);
            }
            setSuccessMessage(`Created ${selectedInsights.size} articles! Redirecting...`);

            setTimeout(() => {
                navigateTo('content');
            }, 1500);

        } catch (err) {
            setError(err.message);
        }
    };

    const formatDuration = (seconds) => {
        if (!seconds) return '--:--';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const getViralScoreClass = (score) => {
        if (score >= 8) return 'score-high';
        if (score >= 5) return 'score-medium';
        return 'score-low';
    };

    const getEngagementIcon = (type) => {
        const icons = {
            educational: '📚',
            controversial: '🔥',
            emotional: '💫',
            surprising: '😲',
            practical: '⚡'
        };
        return icons[type] || '💡';
    };

    return (
        <div className="youtube-import">
            {/* Header */}
            <div className="yt-header">
                <div className="yt-header-icon">🎬</div>
                <div className="yt-header-content">
                    <h1>YouTube Transcript Analyzer</h1>
                    <p>Extract insights from any YouTube video and create viral Shorts</p>
                </div>
            </div>

            {/* URL Input */}
            <div className="yt-input-section">
                <div className="yt-input-wrapper">
                    <input
                        type="text"
                        placeholder="Paste YouTube URL here..."
                        value={youtubeUrl}
                        onChange={(e) => setYoutubeUrl(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                        className="yt-url-input"
                    />
                    <button
                        onClick={handleAnalyze}
                        disabled={isAnalyzing}
                        className="yt-analyze-btn"
                    >
                        {isAnalyzing ? (
                            <span className="loading-spinner"></span>
                        ) : (
                            <>🔍 Analyze</>
                        )}
                    </button>
                </div>

                {error && <div className="yt-error">{error}</div>}
                {successMessage && <div className="yt-success">{successMessage}</div>}
            </div>

            {/* Main Content */}
            <div className="yt-main-content">
                {/* Previously Analyzed Videos */}
                <div className="yt-sidebar">
                    <h3>📹 Recent Analyses</h3>
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
                                No videos analyzed yet. Paste a URL above to get started!
                            </div>
                        )}
                    </div>
                </div>

                {/* Insights Panel */}
                <div className="yt-insights-panel">
                    {selectedSource ? (
                        <>
                            {/* Video Info Header */}
                            <div className="yt-video-header">
                                <img
                                    src={selectedSource.thumbnail_url}
                                    alt=""
                                    className="yt-video-thumb"
                                />
                                <div className="yt-video-info">
                                    <h2>{selectedSource.title || 'Analyzing Video...'}</h2>
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
                                    {selectedSource.analysis_status === 'completed' && (
                                        <button
                                            className="view-summary-btn"
                                            onClick={handleViewSummary}
                                            disabled={isLoadingSummary}
                                        >
                                            {isLoadingSummary ? '⏳ Loading...' : '📋 View Full Summary'}
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Loading State */}
                            {selectedSource.analysis_status === 'analyzing' && (
                                <div className="yt-analyzing-state">
                                    <div className="analyzing-animation">
                                        <div className="brain-icon">🧠</div>
                                        <div className="analyzing-text">AI is finding key insights...</div>
                                        <div className="analyzing-subtext">This usually takes 15-30 seconds</div>
                                    </div>
                                </div>
                            )}

                            {/* Error State */}
                            {selectedSource.analysis_status === 'failed' && (
                                <div className="yt-error-state">
                                    <div className="error-icon">❌</div>
                                    <div className="error-text">Analysis Failed</div>
                                    <div className="error-detail">{selectedSource.error_message}</div>
                                </div>
                            )}

                            {/* Insights List */}
                            {selectedSource.analysis_status === 'completed' && selectedSource.insights && (
                                <>
                                    <div className="yt-insights-header">
                                        <h3>🎯 Key Insights Found: {selectedSource.insights.length}</h3>
                                        <p>Select insights and choose how to create Shorts</p>
                                    </div>

                                    <div className="yt-insights-list">
                                        {selectedSource.insights.map((insight, index) => (
                                            <div
                                                key={index}
                                                className={`yt-insight-card ${selectedInsights.has(index) ? 'selected' : ''}`}
                                            >
                                                <div className="insight-header">
                                                    <label className="insight-checkbox">
                                                        <input
                                                            type="checkbox"
                                                            checked={selectedInsights.has(index)}
                                                            onChange={() => handleToggleInsight(index)}
                                                        />
                                                        <span className="checkmark"></span>
                                                    </label>

                                                    <div className="insight-time">
                                                        [{insight.formatted_time} - {insight.formatted_end_time}]
                                                    </div>

                                                    <div className={`viral-score ${getViralScoreClass(insight.viral_score)}`}>
                                                        ⭐ {insight.viral_score}/10
                                                    </div>

                                                    <span className="engagement-type">
                                                        {getEngagementIcon(insight.engagement_type)} {insight.engagement_type}
                                                    </span>
                                                </div>

                                                <div className="insight-content">
                                                    <div className="insight-summary">{insight.summary}</div>
                                                    <div className="insight-hook">
                                                        <span className="hook-label">Hook:</span>
                                                        "{insight.hook}"
                                                    </div>

                                                    {insight.key_points && insight.key_points.length > 0 && (
                                                        <div className="insight-points">
                                                            {insight.key_points.slice(0, 2).map((point, i) => (
                                                                <span key={i} className="key-point">• {point}</span>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>

                                                <div className="insight-actions">
                                                    {generatingInsight?.index === index ? (
                                                        <div className="generation-progress">
                                                            <span className="progress-spinner"></span>
                                                            <span className="progress-text">
                                                                {generationProgress[index] || 'Processing...'}
                                                            </span>
                                                        </div>
                                                    ) : (
                                                        <>
                                                            <button
                                                                className="mode-btn mode-a"
                                                                onClick={() => handleModeA(index)}
                                                                disabled={generatingInsight !== null}
                                                                title="Extract clip, add commentary, auto-generate video"
                                                            >
                                                                🎬 React to Clip
                                                            </button>
                                                            <button
                                                                className="mode-btn mode-b"
                                                                onClick={() => handleModeB(index)}
                                                                disabled={generatingInsight !== null}
                                                                title="Create original content, go to Script Review"
                                                            >
                                                                ✍️ Write Original
                                                            </button>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Bulk Actions */}
                                    {selectedInsights.size > 0 && (
                                        <div className="yt-bulk-actions">
                                            <div className="selected-count">
                                                Selected: {selectedInsights.size} insights
                                            </div>
                                            <div className="bulk-buttons">
                                                <button
                                                    className="bulk-btn mode-b"
                                                    onClick={() => handleCreateBulkShorts('B')}
                                                >
                                                    Generate All Selected (Mode B) 🚀
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                        </>
                    ) : (
                        <div className="yt-empty-insights">
                            <div className="empty-icon">📊</div>
                            <h3>No Video Selected</h3>
                            <p>Paste a YouTube URL above to analyze, or select a previously analyzed video from the sidebar.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Summary Modal */}
            {showSummaryModal && (
                <div className="summary-modal-overlay" onClick={() => setShowSummaryModal(false)}>
                    <div className="summary-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>📋 Video Summary</h2>
                            <button className="modal-close" onClick={() => setShowSummaryModal(false)}>×</button>
                        </div>
                        <div className="modal-content">
                            {isLoadingSummary ? (
                                <div className="modal-loading">
                                    <span className="loading-spinner"></span>
                                    <p>Generating summary...</p>
                                </div>
                            ) : videoSummary ? (
                                <>
                                    <div className="summary-source">
                                        <strong>{videoSummary.title}</strong>
                                        {videoSummary.channel_name && (
                                            <span className="summary-channel">by {videoSummary.channel_name}</span>
                                        )}
                                    </div>
                                    <div className="summary-text" dangerouslySetInnerHTML={{
                                        __html: videoSummary.video_summary.replace(/\n/g, '<br>')
                                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                            .replace(/- (.*?)(?=<br>|$)/g, '• $1')
                                    }} />
                                </>
                            ) : (
                                <p>No summary available</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default YouTubeImport;
