import { useState, useEffect } from 'react';
import { importManualContent } from '../services/contentApi';
import './ManualImportModal.css';

/**
 * ManualImportModal - Paste external content for video generation
 * 
 * Allows users to paste content from Perplexity, LinkedIn, articles, etc.
 * and import it into the Content Library for video generation.
 */
export default function ManualImportModal({ isOpen, onClose, onImportComplete }) {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [sourceUrl, setSourceUrl] = useState('');
    const [contentType, setContentType] = useState('daily_update');
    const [importing, setImporting] = useState(false);
    const [error, setError] = useState(null);

    // Reset state when modal opens
    useEffect(() => {
        if (isOpen) {
            setTitle('');
            setContent('');
            setSourceUrl('');
            setContentType('daily_update');
            setError(null);
        }
    }, [isOpen]);

    if (!isOpen) return null;

    // Calculate word count and estimated duration
    const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;
    const estimatedDuration = Math.round(wordCount / 2.5); // ~150 words/min = 2.5 words/sec

    // Format duration as mm:ss
    const formatDuration = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Validation
    const titleValid = title.trim().length >= 10;
    const contentValid = content.trim().length >= 100;
    const canSubmit = titleValid && contentValid && !importing;

    const handleImport = async () => {
        if (!canSubmit) return;

        setImporting(true);
        setError(null);

        try {
            const result = await importManualContent({
                title: title.trim(),
                content: content.trim(),
                sourceUrl: sourceUrl.trim() || null,
                contentType
            });

            // Show success message
            const analysisMsg = result.analyzed
                ? '✅ Content imported and analyzed!'
                : '✅ Content imported! (Analysis pending)';

            alert(`${analysisMsg}\n\n📊 Word Count: ${result.word_count}\n⏱️ Est. Duration: ${formatDuration(Math.round(result.estimated_duration))}s`);

            // Notify parent to refresh and close
            if (onImportComplete) {
                onImportComplete();
            }
            onClose();
        } catch (err) {
            setError(err.message);
        } finally {
            setImporting(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="manual-import-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>✍️ Paste External Content</h2>
                    <button onClick={onClose} className="btn-close">×</button>
                </div>

                <div className="modal-body">
                    <p className="modal-description">
                        Paste content from Perplexity, LinkedIn, articles, or any external source
                        to generate video scripts.
                    </p>

                    {error && (
                        <div className="error-message">
                            <strong>Error:</strong> {error}
                        </div>
                    )}

                    <div className="form-group">
                        <label htmlFor="title">
                            Title <span className="required">*</span>
                            {title && !titleValid && (
                                <span className="validation-hint">(min 10 characters)</span>
                            )}
                        </label>
                        <input
                            id="title"
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="Enter a descriptive title for this content..."
                            className={`form-input ${title && !titleValid ? 'invalid' : ''}`}
                            maxLength={200}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="content">
                            Content <span className="required">*</span>
                            {content && !contentValid && (
                                <span className="validation-hint">(min 100 characters)</span>
                            )}
                        </label>
                        <textarea
                            id="content"
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            placeholder="Paste the full article or content here..."
                            className={`form-textarea ${content && !contentValid ? 'invalid' : ''}`}
                            rows={10}
                            maxLength={15000}
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group flex-1">
                            <label htmlFor="sourceUrl">Source URL (optional)</label>
                            <input
                                id="sourceUrl"
                                type="url"
                                value={sourceUrl}
                                onChange={(e) => setSourceUrl(e.target.value)}
                                placeholder="https://..."
                                className="form-input"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="contentType">Content Type</label>
                            <select
                                id="contentType"
                                value={contentType}
                                onChange={(e) => setContentType(e.target.value)}
                                className="form-select"
                            >
                                <option value="daily_update">Daily Update</option>
                                <option value="big_tech">Big Tech News</option>
                                <option value="leader_quote">Leader Quote</option>
                                <option value="arxiv_paper">Research Paper</option>
                            </select>
                        </div>
                    </div>

                    {/* Stats bar */}
                    <div className="stats-bar">
                        <span className="stat">
                            📝 <strong>{wordCount.toLocaleString()}</strong> words
                        </span>
                        <span className="stat">
                            ⏱️ Est. Video: <strong>{formatDuration(estimatedDuration)}</strong>
                        </span>
                        {content.length > 0 && (
                            <span className="stat chars">
                                {content.length.toLocaleString()} / 15,000 chars
                            </span>
                        )}
                    </div>
                </div>

                <div className="modal-footer">
                    <button onClick={onClose} className="btn-cancel">Cancel</button>
                    <button
                        onClick={handleImport}
                        disabled={!canSubmit}
                        className="btn-import-primary"
                    >
                        {importing ? (
                            <>
                                <span className="spinner"></span>
                                Importing & Analyzing...
                            </>
                        ) : (
                            '📥 Import Content'
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
