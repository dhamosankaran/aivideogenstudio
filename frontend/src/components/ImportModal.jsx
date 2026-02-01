import { useState, useEffect } from 'react';
import { searchNews, importArticles } from '../services/newsApi';
import './ImportModal.css';

export default function ImportModal({ isOpen, onClose, onImportComplete }) {
    const [query, setQuery] = useState('');
    const [dateRange, setDateRange] = useState('7');
    const [searching, setSearching] = useState(false);
    const [importing, setImporting] = useState(false);
    const [results, setResults] = useState(null);
    const [selected, setSelected] = useState([]);
    const [error, setError] = useState(null);

    // Reset state when modal opens
    useEffect(() => {
        if (isOpen) {
            setQuery('');
            setResults(null);
            setSelected([]);
            setError(null);
        }
    }, [isOpen]);

    if (!isOpen) return null;

    const handleSearch = async () => {
        if (!query.trim()) {
            setError('Please enter a search query');
            return;
        }

        setSearching(true);
        setError(null);
        setResults(null);
        setSelected([]);

        try {
            const fromDate = new Date();
            fromDate.setDate(fromDate.getDate() - parseInt(dateRange));

            const data = await searchNews(query, {
                from_date: fromDate.toISOString().split('T')[0],
                page_size: 10,
                sort_by: 'relevancy'
            });

            setResults(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setSearching(false);
        }
    };

    const handleSelect = (index) => {
        setSelected(prev => {
            if (prev.includes(index)) {
                return prev.filter(i => i !== index);
            } else {
                return [...prev, index];
            }
        });
    };

    const handleSelectAll = () => {
        if (selected.length === results.articles.length) {
            setSelected([]);
        } else {
            setSelected(results.articles.map((_, i) => i));
        }
    };

    const handleImport = async () => {
        if (selected.length === 0) {
            alert('Please select at least one article');
            return;
        }

        setImporting(true);

        try {
            const articlesToImport = selected.map(i => results.articles[i]);
            const result = await importArticles(articlesToImport);

            alert(`Imported ${result.imported} articles!\n${result.duplicates} duplicates skipped.`);

            // Notify parent to refresh and close
            if (onImportComplete) {
                onImportComplete();
            }
            onClose();
        } catch (err) {
            alert(`Failed to import: ${err.message}`);
        } finally {
            setImporting(false);
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-container">
                <div className="modal-header">
                    <h2>🔍 Import from NewsAPI</h2>
                    <button onClick={onClose} className="btn-close">×</button>
                </div>

                <div className="modal-body">
                    <div className="search-controls">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                            placeholder='Try "AI", "Tesla", "Tech"...'
                            className="search-input"
                            autoFocus
                        />

                        <select
                            value={dateRange}
                            onChange={(e) => setDateRange(e.target.value)}
                            className="date-select"
                        >
                            <option value="1">Last 24h</option>
                            <option value="3">Last 3d</option>
                            <option value="7">Last 7d</option>
                            <option value="30">Last 30d</option>
                        </select>

                        <button
                            onClick={handleSearch}
                            disabled={searching}
                            className="btn-search"
                        >
                            {searching ? '...' : 'Search'}
                        </button>
                    </div>

                    {error && (
                        <div className="error-message">
                            <strong>Error:</strong> {error}
                        </div>
                    )}

                    {results && (
                        <div className="search-results">
                            <div className="results-actions-bar">
                                <span>Found {results.total_results} articles</span>
                                <div className="actions-right">
                                    <button onClick={handleSelectAll} className="btn-text">
                                        {selected.length === results.articles.length ? 'None' : 'All'}
                                    </button>
                                </div>
                            </div>

                            <div className="articles-list-compact">
                                {results.articles.map((article, index) => (
                                    <div
                                        key={index}
                                        className={`article-item ${selected.includes(index) ? 'selected' : ''}`}
                                        onClick={() => handleSelect(index)}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={selected.includes(index)}
                                            onChange={() => { }}
                                        />
                                        <div className="article-info">
                                            <h4>{article.title}</h4>
                                            <span className="meta">{article.source.name} • {new Date(article.publishedAt).toLocaleDateString()}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                <div className="modal-footer">
                    <button onClick={onClose} className="btn-cancel">Cancel</button>
                    <button
                        onClick={handleImport}
                        disabled={importing || selected.length === 0}
                        className="btn-import-primary"
                    >
                        {importing ? 'Importing...' : `Import ${selected.length} Articles`}
                    </button>
                </div>
            </div>
        </div>
    );
}
