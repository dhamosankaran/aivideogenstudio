import { useState } from 'react';
import './BulkActions.css';

export default function BulkActions({ count, onGenerate, onDelete, onCreateDigest, generating }) {
    const [contentType, setContentType] = useState('daily_update');

    const handleGenerate = () => {
        onGenerate(contentType);
    };

    return (
        <div className="bulk-actions">
            <div className="bulk-actions-content">
                <div className="selection-info">
                    <span className="count">{count}</span>
                    <span className="label">article{count !== 1 ? 's' : ''} selected</span>
                </div>

                <div className="actions">
                    <div className="content-type-selector">
                        <label htmlFor="content-type">Content Type:</label>
                        <select
                            id="content-type"
                            value={contentType}
                            onChange={(e) => setContentType(e.target.value)}
                            disabled={generating}
                            className="content-type-select"
                        >
                            <option value="daily_update">Daily Update</option>
                            <option value="big_tech">Big Tech News</option>
                            <option value="leader_quote">Leader Quote</option>
                            <option value="arxiv_paper">arXiv Paper</option>
                        </select>
                    </div>

                    <button
                        onClick={handleGenerate}
                        disabled={generating}
                        className="btn-generate"
                    >
                        {generating ? (
                            <>
                                <span className="spinner-small"></span>
                                Generating Scripts...
                            </>
                        ) : (
                            <>
                                Generate Scripts ({count})
                            </>
                        )}
                    </button>

                    <button
                        onClick={onCreateDigest}
                        disabled={generating || count < 2}
                        className="btn-digest"
                        style={{ marginLeft: '8px', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: 'white', border: 'none', padding: '0 16px', borderRadius: '6px', cursor: count < 2 ? 'not-allowed' : 'pointer', height: '100%', opacity: count < 2 ? 0.5 : 1, fontWeight: 500 }}
                        title={count < 2 ? 'Select at least 2 articles to create a digest' : `Create a single combined digest video from ${count} articles`}
                    >
                        📡 Create Digest ({count})
                    </button>

                    <button
                        onClick={onDelete}
                        disabled={generating}
                        className="btn-delete"
                        style={{ marginLeft: '8px', backgroundColor: '#ef4444', color: 'white', border: 'none', padding: '0 16px', borderRadius: '6px', cursor: 'pointer', height: '100%' }}
                    >
                        Delete
                    </button>
                </div>
            </div>
        </div>
    );
}
