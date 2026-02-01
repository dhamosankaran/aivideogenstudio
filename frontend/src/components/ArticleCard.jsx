import './ArticleCard.css';

export default function ArticleCard({ article, selected, onSelect }) {
    const getStatusClass = (status) => {
        switch (status) {
            case 'unprocessed': return 'status-new';
            case 'script_generated': return 'status-ready';
            case 'video_created': return 'status-done';
            default: return 'status-gray';
        }
    };

    const getStatusLabel = (status) => {
        switch (status) {
            case 'unprocessed': return 'New';
            case 'script_generated': return 'Script Ready';
            case 'video_created': return 'Video Created';
            default: return status;
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
    };

    const formatContentType = (type) => {
        if (!type) return null;
        return type.split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    };

    return (
        <div
            className={`article-card ${selected ? 'selected' : ''}`}
            onClick={() => onSelect(article.id)}
        >
            <div className="card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span className="source-badge">{article.source}</span>
                    <span className="date">{formatDate(article.published_at)}</span>
                </div>

                <span className={`status-badge-absolute ${getStatusClass(article.status)}`}>
                    {getStatusLabel(article.status)}
                </span>
            </div>

            <h3 className="article-title">{article.title}</h3>

            <p className="article-description">
                {article.description || article.why_interesting || 'No description available'}
            </p>

            {article.key_points && article.key_points.length > 0 && (
                <div className="key-points">
                    <strong>Key Points:</strong>
                    <ul>
                        {article.key_points.slice(0, 2).map((point, idx) => (
                            <li key={idx}>{point}</li>
                        ))}
                    </ul>
                </div>
            )}

            <div className="card-footer">
                <div className="footer-tags">
                    {article.relevance_score && (
                        <span className="score">
                            {article.relevance_score.toFixed(1)}/10
                        </span>
                    )}

                    {article.suggested_content_type && (
                        <span className="content-type-badge">
                            {formatContentType(article.suggested_content_type)}
                        </span>
                    )}
                </div>

                <button
                    className="btn-select"
                    onClick={(e) => {
                        e.stopPropagation();
                        onSelect(article.id);
                    }}
                >
                    {selected ? 'Selected ✓' : 'Select'}
                </button>
            </div>
        </div>
    );
}
