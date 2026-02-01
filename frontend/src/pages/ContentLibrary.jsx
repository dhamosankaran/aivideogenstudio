import { useState, useEffect } from 'react';
import ArticleCard from '../components/ArticleCard';
import FilterBar from '../components/FilterBar';
import BulkActions from '../components/BulkActions';
import ImportModal from '../components/ImportModal';
import { fetchArticles, generateScripts, deleteArticles } from '../services/contentApi';
import { syncFeeds } from '../services/feedApi';
import './ContentLibrary.css';

export default function ContentLibrary() {
    const [articles, setArticles] = useState([]);
    const [selected, setSelected] = useState([]);
    const [loading, setLoading] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [error, setError] = useState(null);
    const [generating, setGenerating] = useState(false);
    const [showImportModal, setShowImportModal] = useState(false);

    // Pagination state
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(0);
    const [total, setTotal] = useState(0);

    // Filter state
    const [filters, setFilters] = useState({
        source: '',
        date_range: 'all',
        content_type: '',
        status: '',
        search: '',
        page: 1,
        page_size: 20
    });

    // Load articles when filters change
    useEffect(() => {
        loadArticles();
    }, [filters]);

    const loadArticles = async () => {
        setLoading(true);
        setError(null);

        try {
            const data = await fetchArticles(filters);
            setArticles(data.items);
            setCurrentPage(data.page);
            setTotalPages(data.total_pages);
            setTotal(data.total);
        } catch (err) {
            setError(err.message);
            console.error('Failed to load articles:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleFilterChange = (newFilters) => {
        setFilters(prev => ({
            ...prev,
            ...newFilters,
            page: 1 // Reset to first page when filters change
        }));
        setSelected([]); // Clear selection when filters change
    };

    const handlePageChange = (newPage) => {
        setFilters(prev => ({ ...prev, page: newPage }));
        setSelected([]); // Clear selection when page changes
    };

    const handleSelect = (articleId) => {
        setSelected(prev => {
            if (prev.includes(articleId)) {
                return prev.filter(id => id !== articleId);
            } else {
                return [...prev, articleId];
            }
        });
    };

    const handleSelectAll = () => {
        if (selected.length === articles.length) {
            setSelected([]);
        } else {
            setSelected(articles.map(a => a.id));
        }
    };

    const handleGenerateScripts = async (contentType) => {
        if (selected.length === 0) {
            alert('Please select at least one article');
            return;
        }

        setGenerating(true);

        try {
            const result = await generateScripts(selected, contentType);

            // Show detailed results
            let message = '';

            if (result.scripts_created > 0) {
                message += `✅ Successfully generated ${result.scripts_created} script(s)!\n`;
                if (result.analyzed_count > 0) {
                    message += `📊 Auto-analyzed ${result.analyzed_count} article(s)\n`;
                }
            }

            if (result.errors && result.errors.length > 0) {
                message += `\n❌ ${result.errors.length} error(s):\n\n`;
                result.errors.forEach((error, index) => {
                    const errorType = error.error_type === 'analysis_failed' ? '📊 Analysis Failed' :
                        error.error_type === 'validation_error' ? '⚠️ Validation Error' :
                            '❌ Generation Failed';
                    message += `${index + 1}. ${errorType}\n`;
                    message += `   Article: "${error.article_title}"\n`;
                    message += `   Error: ${error.error}\n\n`;
                });
            }

            if (!message) {
                message = 'No scripts were generated. Please try again.';
            }

            alert(message);

            // Reload articles to update status
            await loadArticles();
            setSelected([]);
        } catch (err) {
            alert(`Failed to generate scripts: ${err.message}`);
            console.error('Failed to generate scripts:', err);
        } finally {
            setGenerating(false);
        }
    };

    const handleSyncFeeds = async () => {
        setSyncing(true);
        setError(null);

        try {
            const result = await syncFeeds();
            alert(`RSS sync started! Job ID: ${result.job_id}\nNew articles will appear shortly.`);

            // Wait a bit then reload articles
            setTimeout(async () => {
                await loadArticles();
            }, 3000);
        } catch (err) {
            setError(`Failed to sync feeds: ${err.message}`);
            console.error('Failed to sync feeds:', err);
        } finally {
            setSyncing(false);
        }
    };

    return (
        <div className="content-library">
            <div className="content-library-header">
                <div className="header-content">
                    <div className="header-text">
                        <h1>Content Library</h1>
                        <p className="subtitle">Browse and select articles from your RSS feeds to generate videos</p>
                    </div>
                    <div className="header-buttons">
                        <button
                            onClick={handleSyncFeeds}
                            disabled={syncing || loading}
                            className="btn-sync"
                        >
                            {syncing ? '📡 Fetching...' : '📡 Fetch from RSS'}
                        </button>
                        <button
                            onClick={loadArticles}
                            disabled={loading || syncing}
                            className="btn-refresh"
                        >
                            {loading ? '⟳ Refreshing...' : '⟳ Refresh View'}
                        </button>
                        <button
                            onClick={() => setShowImportModal(true)}
                            className="btn-import-trigger"
                            style={{ marginLeft: '12px', backgroundColor: '#2563eb', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer' }}
                        >
                            🔍 Import from NewsAPI
                        </button>
                    </div>
                </div>
            </div>

            <FilterBar
                filters={filters}
                onChange={handleFilterChange}
                onSelectAll={handleSelectAll}
                allSelected={selected.length === articles.length && articles.length > 0}
            />

            <ImportModal
                isOpen={showImportModal}
                onClose={() => setShowImportModal(false)}
                onImportComplete={loadArticles}
            />

            {error && (
                <div className="error-message">
                    <strong>Error:</strong> {error}
                </div>
            )}

            {loading ? (
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading articles...</p>
                </div>
            ) : articles.length === 0 ? (
                <div className="empty-state">
                    <h3>No articles found</h3>
                    <p>Try adjusting your filters or check back later for new content.</p>
                </div>
            ) : (
                <>
                    <div className="articles-header">
                        <p className="results-count">
                            Showing {articles.length} of {total} articles
                            {selected.length > 0 && ` • ${selected.length} selected`}
                        </p>
                    </div>

                    <div className="articles-grid">
                        {articles.map(article => (
                            <ArticleCard
                                key={article.id}
                                article={article}
                                selected={selected.includes(article.id)}
                                onSelect={handleSelect}
                            />
                        ))}
                    </div>

                    {totalPages > 1 && (
                        <div className="pagination">
                            <button
                                onClick={() => handlePageChange(currentPage - 1)}
                                disabled={currentPage === 1}
                                className="pagination-btn"
                            >
                                Previous
                            </button>

                            <span className="pagination-info">
                                Page {currentPage} of {totalPages}
                            </span>

                            <button
                                onClick={() => handlePageChange(currentPage + 1)}
                                disabled={currentPage === totalPages}
                                className="pagination-btn"
                            >
                                Next
                            </button>
                        </div>
                    )}
                </>
            )}

            {selected.length > 0 && (
                <BulkActions
                    count={selected.length}
                    onGenerate={handleGenerateScripts}
                    onDelete={async () => {
                        if (window.confirm(`Are you sure you want to delete ${selected.length} articles?`)) {
                            setLoading(true);
                            try {
                                const result = await deleteArticles(selected);
                                alert(`Deleted ${result.deleted} articles.`);
                                await loadArticles();
                                setSelected([]);
                            } catch (err) {
                                alert(`Failed to delete: ${err.message}`);
                            } finally {
                                setLoading(false);
                            }
                        }
                    }}
                    generating={generating}
                />
            )}
        </div>
    );
}
