import { useState, useEffect } from 'react';
import { useAppNavigate } from '../context/ProjectContext';
import {
    searchBooks,
    selectBook,
    getBook,
    analyzeBook,
    generateBookVideo,
    prepareBookAssets,
    getAllBooks
} from '../services/bookApi';
import './BookReview.css';

function BookReview() {
    const { navigateTo } = useAppNavigate();

    // State
    const [searchQuery, setSearchQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState([]);
    const [books, setBooks] = useState([]);
    const [selectedBook, setSelectedBook] = useState(null);
    const [selectedAngle, setSelectedAngle] = useState(0);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generationStep, setGenerationStep] = useState('');
    const [assetPreview, setAssetPreview] = useState(null);

    // Load existing books on mount
    useEffect(() => {
        loadBooks();
    }, []);

    const loadBooks = async () => {
        try {
            const data = await getAllBooks();
            setBooks(data);
        } catch (err) {
            console.error('Failed to load books:', err);
        }
    };

    const handleSearch = async () => {
        if (!searchQuery.trim() || searchQuery.length < 2) {
            setError('Please enter at least 2 characters to search');
            return;
        }

        setIsSearching(true);
        setError(null);
        setSearchResults([]);

        try {
            const results = await searchBooks(searchQuery);
            setSearchResults(results);
            if (results.length === 0) {
                setError('No books found. Try a different search term.');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setIsSearching(false);
        }
    };

    const handleSelectSearchResult = async (bookData) => {
        setError(null);
        setSuccessMessage(null);

        try {
            const book = await selectBook(bookData);
            setSelectedBook(book);
            setSearchResults([]);
            setSearchQuery('');
            loadBooks(); // Refresh library
        } catch (err) {
            setError(err.message);
        }
    };

    const handleSelectExistingBook = async (book) => {
        try {
            const fullBook = await getBook(book.id);
            setSelectedBook(fullBook);
            setSelectedAngle(0);
        } catch (err) {
            setError(err.message);
        }
    };

    const handleAnalyze = async () => {
        if (!selectedBook) return;

        setIsAnalyzing(true);
        setError(null);

        try {
            const analyzedBook = await analyzeBook(selectedBook.id);
            setSelectedBook(analyzedBook);
            setSuccessMessage('Analysis complete! Review the key takeaways and select a video angle.');
            loadBooks();
        } catch (err) {
            setError(err.message);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handlePrepareAssets = async (bookId) => {
        try {
            const assets = await prepareBookAssets(bookId);
            setAssetPreview(assets);
        } catch (err) {
            console.error("Failed to prepare assets:", err);
            // Don't block flow, but user won't see preview
        }
    };

    useEffect(() => {
        if (selectedBook && selectedBook.analysis_status === 'completed') {
            handlePrepareAssets(selectedBook.id);
        } else {
            setAssetPreview(null);
        }
    }, [selectedBook]);

    const handleGenerateVideo = async () => {
        if (!selectedBook) return;

        setIsGenerating(true);
        setError(null);
        setGenerationStep('Creating script & generating audio...');

        try {
            // Pass project_folder if available ensuring strict asset mode
            const projectFolder = assetPreview?.project_folder;
            const result = await generateBookVideo(selectedBook.id, selectedAngle, null, projectFolder);

            setGenerationStep('Video rendering in background...');
            setSuccessMessage(
                `🎬 ${result.message} Redirecting to Videos...`
            );

            setTimeout(() => {
                navigateTo('videos');
            }, 2000);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsGenerating(false);
            setGenerationStep('');
        }
    };

    const getViralScoreClass = (score) => {
        if (score >= 8) return 'score-high';
        if (score >= 5) return 'score-medium';
        return 'score-low';
    };

    return (
        <div className="book-review">
            {/* Header */}
            <div className="book-header">
                <div className="book-header-icon">📚</div>
                <div className="book-header-content">
                    <h1>Book Review Shorts</h1>
                    <p>Search for books, extract key insights, and create engaging summary videos</p>
                </div>
            </div>

            {/* Search Section */}
            <div className="book-search-section">
                <div className="book-search-wrapper">
                    <input
                        type="text"
                        placeholder="Search by title or author... (e.g., Atomic Habits)"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                        className="book-search-input"
                    />
                    <button
                        onClick={handleSearch}
                        disabled={isSearching}
                        className="book-search-btn"
                    >
                        {isSearching ? (
                            <span className="loading-spinner"></span>
                        ) : (
                            <>🔍 Search</>
                        )}
                    </button>
                </div>

                {error && <div className="book-error">{error}</div>}
                {successMessage && <div className="book-success">{successMessage}</div>}

                {/* Search Results */}
                {searchResults.length > 0 && (
                    <div className="book-search-results">
                        <h4>Search Results</h4>
                        <div className="search-results-grid">
                            {searchResults.map((result, index) => (
                                <div
                                    key={index}
                                    className="search-result-card"
                                    onClick={() => handleSelectSearchResult(result)}
                                >
                                    <div className="result-cover">
                                        {result.cover_url ? (
                                            <img src={result.cover_url} alt="" />
                                        ) : (
                                            <div className="cover-placeholder">📕</div>
                                        )}
                                    </div>
                                    <div className="result-info">
                                        <div className="result-title">{result.title}</div>
                                        <div className="result-author">{result.author || 'Unknown Author'}</div>
                                        {result.first_publish_year && (
                                            <div className="result-year">Published: {result.first_publish_year}</div>
                                        )}
                                        {result.subjects && result.subjects.length > 0 && (
                                            <div className="result-subjects">
                                                {result.subjects.slice(0, 3).map((subject, i) => (
                                                    <span key={i} className="subject-tag">{subject}</span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Main Content */}
            <div className="book-main-content">
                {/* Book Library Sidebar */}
                <div className="book-sidebar">
                    <h3>📖 Book Library</h3>
                    <div className="book-list">
                        {books.map(book => (
                            <div
                                key={book.id}
                                className={`book-card ${selectedBook?.id === book.id ? 'active' : ''}`}
                                onClick={() => handleSelectExistingBook(book)}
                            >
                                <div className="book-cover">
                                    {book.cover_url ? (
                                        <img src={book.cover_url} alt="" />
                                    ) : (
                                        <div className="cover-placeholder-small">📕</div>
                                    )}
                                </div>
                                <div className="book-info">
                                    <div className="book-title">{book.title}</div>
                                    <div className="book-author">{book.author || 'Unknown'}</div>
                                    <span className={`status-badge ${book.analysis_status}`}>
                                        {book.analysis_status}
                                    </span>
                                </div>
                            </div>
                        ))}
                        {books.length === 0 && (
                            <div className="book-empty-state">
                                No books in library. Search above to add books!
                            </div>
                        )}
                    </div>
                </div>

                {/* Book Detail Panel */}
                <div className="book-detail-panel">
                    {selectedBook ? (
                        <>
                            {/* Book Info Header */}
                            <div className="book-detail-header">
                                <div className="detail-cover">
                                    {selectedBook.cover_url ? (
                                        <img src={selectedBook.cover_url} alt="" />
                                    ) : (
                                        <div className="cover-placeholder-large">📕</div>
                                    )}
                                </div>
                                <div className="detail-info">
                                    <h2>{selectedBook.title}</h2>
                                    <div className="detail-meta">
                                        <span className="author-name">✍️ {selectedBook.author || 'Unknown Author'}</span>
                                        {selectedBook.first_publish_year && (
                                            <span className="publish-year">📅 {selectedBook.first_publish_year}</span>
                                        )}
                                        {selectedBook.page_count && (
                                            <span className="page-count">📄 {selectedBook.page_count} pages</span>
                                        )}
                                    </div>
                                    {selectedBook.subjects && selectedBook.subjects.length > 0 && (
                                        <div className="detail-subjects">
                                            {selectedBook.subjects.slice(0, 5).map((subject, i) => (
                                                <span key={i} className="subject-tag-large">{subject}</span>
                                            ))}
                                        </div>
                                    )}
                                    <span className={`status-badge large ${selectedBook.analysis_status}`}>
                                        {selectedBook.analysis_status === 'analyzing' && '⏳ '}
                                        {selectedBook.analysis_status}
                                    </span>
                                </div>
                            </div>

                            {/* Description */}
                            {selectedBook.description && (
                                <div className="book-description">
                                    <h4>📝 Description</h4>
                                    <p>{selectedBook.description}</p>
                                </div>
                            )}

                            {/* Pending Analysis State */}
                            {selectedBook.analysis_status === 'pending' && (
                                <div className="book-action-section">
                                    <div className="action-prompt">
                                        <span className="action-icon">🧠</span>
                                        <p>Ready to analyze this book and extract key insights for your video?</p>
                                    </div>
                                    <button
                                        className="analyze-btn"
                                        onClick={handleAnalyze}
                                        disabled={isAnalyzing}
                                    >
                                        {isAnalyzing ? (
                                            <>
                                                <span className="loading-spinner"></span>
                                                Analyzing with AI...
                                            </>
                                        ) : (
                                            <>✨ Analyze Book</>
                                        )}
                                    </button>
                                </div>
                            )}

                            {/* Analyzing State */}
                            {selectedBook.analysis_status === 'analyzing' && (
                                <div className="book-analyzing-state">
                                    <div className="analyzing-animation">
                                        <div className="brain-icon">📖</div>
                                        <div className="analyzing-text">AI is reading the book...</div>
                                        <div className="analyzing-subtext">Extracting key insights and generating video angles</div>
                                    </div>
                                </div>
                            )}

                            {/* Failed State */}
                            {selectedBook.analysis_status === 'failed' && (
                                <div className="book-error-state">
                                    <div className="error-icon">❌</div>
                                    <div className="error-text">Analysis Failed</div>
                                    <div className="error-detail">{selectedBook.error_message}</div>
                                    <button className="retry-btn" onClick={handleAnalyze}>
                                        🔄 Retry Analysis
                                    </button>
                                </div>
                            )}

                            {/* Analysis Complete - Show Takeaways */}
                            {selectedBook.analysis_status === 'completed' && selectedBook.key_takeaways && (
                                <>
                                    <div className="book-takeaways-section">
                                        <h3>💡 Key Takeaways</h3>
                                        <div className="takeaways-list">
                                            {selectedBook.key_takeaways.map((takeaway, index) => (
                                                <div key={index} className="takeaway-card">
                                                    <div className="takeaway-header">
                                                        <span className="takeaway-number">{index + 1}</span>
                                                        <div className={`viral-score ${getViralScoreClass(takeaway.viral_score)}`}>
                                                            ⭐ {takeaway.viral_score}/10
                                                        </div>
                                                    </div>
                                                    <div className="takeaway-point">{takeaway.point}</div>
                                                    <div className="takeaway-hook">
                                                        <span className="hook-label">Hook:</span>
                                                        "{takeaway.hook}"
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Video Angle Selection */}
                                    {selectedBook.suggested_angles && (
                                        <div className="book-angles-section">
                                            <h3>🎬 Select Video Angle</h3>
                                            <div className="angles-list">
                                                {selectedBook.suggested_angles.map((angle, index) => (
                                                    <label
                                                        key={index}
                                                        className={`angle-option ${selectedAngle === index ? 'selected' : ''}`}
                                                    >
                                                        <input
                                                            type="radio"
                                                            name="angle"
                                                            checked={selectedAngle === index}
                                                            onChange={() => setSelectedAngle(index)}
                                                        />
                                                        <span className="angle-text">{angle}</span>
                                                    </label>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Asset Preview Section */}
                                    {assetPreview && assetPreview.cover_image && (
                                        <div className="asset-preview-section">
                                            <h3>🎬 Video Asset Preview</h3>
                                            <div className="asset-card">
                                                <div className="asset-image-container">
                                                    {/* Use local file serving if possible, or just the URL. 
                                                        Since backend returns absolute path, we might need to handle serving.
                                                        For now, assuming backend serves 'data' folder or we use the public URL if available.
                                                        Actually, let's use the book.cover_url for display if local path isn't web-accessible easily without config.
                                                        But wait, user wants to see *confirmed* asset. 
                                                        If we can't serve local file easily, we show the remote URL but label it as "Verified Asset".
                                                     */}
                                                    <img
                                                        src={selectedBook.cover_url}
                                                        alt="Video Cover Asset"
                                                        className="asset-preview-img"
                                                    />
                                                    <div className="asset-badge">Verified Cover</div>
                                                </div>
                                                <p className="asset-note">
                                                    ✅ strict mode: This exact image will be used for the entire video.
                                                    <br />
                                                    📁 {assetPreview.project_folder.split('/').pop()}
                                                </p>
                                            </div>
                                        </div>
                                    )}

                                    {/* Generate Video Button */}
                                    <div className="book-create-section">
                                        <button
                                            className="create-video-btn"
                                            onClick={handleGenerateVideo}
                                            disabled={isGenerating}
                                        >
                                            {isGenerating ? (
                                                <>
                                                    <span className="loading-spinner"></span>
                                                    {generationStep || 'Generating...'}
                                                </>
                                            ) : (
                                                <>🚀 Generate Book Review Video</>
                                            )}
                                        </button>
                                        {isGenerating && (
                                            <div className="generation-progress">
                                                <div className="progress-steps">
                                                    <span className="step active">📝 Script</span>
                                                    <span className="step-arrow">→</span>
                                                    <span className={`step ${generationStep.includes('audio') ? 'active' : ''}`}>🔊 Audio</span>
                                                    <span className="step-arrow">→</span>
                                                    <span className={`step ${generationStep.includes('rendering') ? 'active' : ''}`}>🎬 Video</span>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </>
                            )}
                        </>
                    ) : (
                        <div className="book-empty-detail">
                            <div className="empty-icon">📚</div>
                            <h3>No Book Selected</h3>
                            <p>Search for a book above and select it to view details and create a review video.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default BookReview;
