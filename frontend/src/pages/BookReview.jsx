import { useState, useEffect } from 'react';
import { useAppNavigate } from '../context/ProjectContext';
import {
    searchBooks,
    selectBook,
    getBook,
    analyzeBook,
    generateBookVideo,
    generateBookScript,
    prepareBookAssets,
    getAllBooks,
    getVoiceOptions
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
    const [duplicateInfo, setDuplicateInfo] = useState(null);  // Set when re-selecting an existing book
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generationStep, setGenerationStep] = useState('');
    const [assetPreview, setAssetPreview] = useState(null);

    // Script preview state
    const [isGeneratingScript, setIsGeneratingScript] = useState(false);
    const [scriptPreview, setScriptPreview] = useState(null);
    const [scriptAccepted, setScriptAccepted] = useState(false);

    // TTS state
    const [voiceOptions, setVoiceOptions] = useState(null);
    const [selectedProvider, setSelectedProvider] = useState('openai');
    const [selectedVoice, setSelectedVoice] = useState(null);

    // Background mode state
    const [backgroundMode, setBackgroundMode] = useState('auto');
    // Image source state
    const [imageSource, setImageSource] = useState('stock');
    // Video source state
    const [videoSource, setVideoSource] = useState('stock');
    // Veo style state (only relevant when videoSource === 'veo')
    const [veoStyle, setVeoStyle] = useState('auto');
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
        setDuplicateInfo(null);

        try {
            const book = await selectBook(bookData);
            setSelectedBook(book);
            setSearchResults([]);
            setSearchQuery('');
            loadBooks(); // Refresh library

            if (book.already_existed) {
                setDuplicateInfo(
                    `📚 "${book.title}" is already in your library${book.analysis_status === 'completed' ? ' and has been analyzed' : ''
                    }. Loaded its existing details below.`
                );
            } else {
                setSuccessMessage(`✅ "${book.title}" added to your library.`);
            }
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
            // Load voice options when book is analyzed
            loadVoiceOptions();
        } else {
            setAssetPreview(null);
        }
        // Reset script state when book changes
        setScriptPreview(null);
        setScriptAccepted(false);
    }, [selectedBook]);

    const loadVoiceOptions = async () => {
        try {
            const options = await getVoiceOptions('book_review');
            setVoiceOptions(options);
            // Set defaults from voice config
            setSelectedProvider(options.default_provider || 'openai');
            const defaultProvider = options.providers.find(p => p.id === options.default_provider);
            if (defaultProvider) {
                setSelectedVoice(defaultProvider.default_voice);
            }
        } catch (err) {
            console.error('Failed to load voice options:', err);
        }
    };

    // When provider changes, update voice to provider's default
    useEffect(() => {
        if (voiceOptions) {
            const provider = voiceOptions.providers.find(p => p.id === selectedProvider);
            if (provider) {
                setSelectedVoice(provider.default_voice);
            }
        }
    }, [selectedProvider]);

    const handleGenerateScript = async () => {
        if (!selectedBook) return;

        setIsGeneratingScript(true);
        setError(null);
        setScriptPreview(null);
        setScriptAccepted(false);

        try {
            const result = await generateBookScript(selectedBook.id, selectedAngle);
            setScriptPreview(result);
            setSuccessMessage('Script generated! Review below and approve before generating video.');
        } catch (err) {
            setError(err.message);
        } finally {
            setIsGeneratingScript(false);
        }
    };

    const handleGenerateVideo = async () => {
        if (!selectedBook) return;

        setIsGenerating(true);
        setError(null);
        setGenerationStep('Generating audio with ' + selectedProvider + '...');

        try {
            const projectFolder = assetPreview?.project_folder;
            const result = await generateBookVideo(
                selectedBook.id,
                selectedAngle,
                null,
                projectFolder,
                scriptPreview?.script_id || null,
                selectedProvider,
                selectedVoice,
                backgroundMode,
                imageSource,
                videoSource,
                veoStyle
            );

            setGenerationStep('Video rendering in background...');
            setSuccessMessage(
                `🎬 ${result.message} (TTS: ${result.tts_provider} / ${result.voice}) Redirecting...`
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
                {duplicateInfo && (
                    <div className="book-duplicate-info">{duplicateInfo}</div>
                )}

                {/* Search Results */}
                {searchResults.length > 0 && (
                    <div className="book-search-results">
                        <h4>Search Results</h4>
                        <div className="search-results-grid">
                            {searchResults.map((result, index) => {
                                const isInLibrary = books.some(
                                    b => b.open_library_key === result.open_library_key
                                );
                                return (
                                    <div
                                        key={index}
                                        className={`search-result-card ${isInLibrary ? 'in-library' : ''}`}
                                        onClick={() => handleSelectSearchResult(result)}
                                    >
                                        {isInLibrary && (
                                            <div className="in-library-badge">📚 In Library</div>
                                        )}
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
                                );
                            })}
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

                                    {/* Step 1: Generate Script Button */}
                                    {!scriptPreview && (
                                        <div className="book-create-section">
                                            <button
                                                className="generate-script-btn"
                                                onClick={handleGenerateScript}
                                                disabled={isGeneratingScript}
                                            >
                                                {isGeneratingScript ? (
                                                    <>
                                                        <span className="loading-spinner"></span>
                                                        Generating script...
                                                    </>
                                                ) : (
                                                    <>📝 Generate Script for Review</>
                                                )}
                                            </button>
                                        </div>
                                    )}

                                    {/* Step 2: Script Preview Panel */}
                                    {scriptPreview && (
                                        <div className="script-preview-section">
                                            <div className="script-preview-header">
                                                <h3>📝 Script Preview</h3>
                                                <div className="script-meta-badges">
                                                    <span className="meta-badge">
                                                        📊 {scriptPreview.word_count} words
                                                    </span>
                                                    <span className="meta-badge">
                                                        ⏱️ ~{Math.round(scriptPreview.estimated_duration)}s
                                                    </span>
                                                    <span className={`meta-badge ${scriptPreview.is_valid ? 'valid' : 'invalid'}`}>
                                                        {scriptPreview.is_valid ? '✅ Valid' : '⚠️ Issues'}
                                                    </span>
                                                </div>
                                            </div>

                                            {scriptPreview.catchy_title && (
                                                <div className="script-title-preview">
                                                    <span className="title-label">Title:</span>
                                                    <span className="title-text">{scriptPreview.catchy_title}</span>
                                                </div>
                                            )}

                                            <div className="script-scenes-list">
                                                {scriptPreview.scenes && scriptPreview.scenes.map((scene, index) => (
                                                    <div key={index} className="script-scene-card">
                                                        <div className="scene-header">
                                                            <span className="scene-number">Scene {scene.scene_number}</span>
                                                            {scene.visual_cues && (
                                                                <span className="scene-visual">🎨 {scene.visual_cues}</span>
                                                            )}
                                                        </div>
                                                        <p className="scene-text">{scene.text}</p>
                                                        {scene.image_keywords && scene.image_keywords.length > 0 && (
                                                            <div className="scene-keywords">
                                                                {scene.image_keywords.map((kw, i) => (
                                                                    <span key={i} className="keyword-tag">{kw}</span>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>

                                            {/* Validation errors */}
                                            {scriptPreview.validation_errors && scriptPreview.validation_errors.length > 0 && (
                                                <div className="script-validation-warnings">
                                                    {scriptPreview.validation_errors.map((err, i) => (
                                                        <div key={i} className="validation-warning">⚠️ {err}</div>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Script Actions */}
                                            <div className="script-actions">
                                                <button
                                                    className={`script-accept-btn ${scriptAccepted ? 'accepted' : ''}`}
                                                    onClick={() => setScriptAccepted(true)}
                                                    disabled={scriptAccepted}
                                                >
                                                    {scriptAccepted ? '✅ Script Accepted' : '✅ Accept Script'}
                                                </button>
                                                <button
                                                    className="script-regenerate-btn"
                                                    onClick={handleGenerateScript}
                                                    disabled={isGeneratingScript}
                                                >
                                                    {isGeneratingScript ? (
                                                        <>
                                                            <span className="loading-spinner"></span>
                                                            Regenerating...
                                                        </>
                                                    ) : (
                                                        <>🔄 Regenerate</>
                                                    )}
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {/* Step 3: TTS Provider & Voice Selection */}
                                    {scriptAccepted && voiceOptions && (
                                        <div className="tts-selector-section">
                                            <h3>🎤 Voice & TTS Settings</h3>

                                            <div className="tts-provider-grid">
                                                {voiceOptions.providers.map(provider => (
                                                    <label
                                                        key={provider.id}
                                                        className={`tts-provider-card ${selectedProvider === provider.id ? 'selected' : ''}`}
                                                    >
                                                        <input
                                                            type="radio"
                                                            name="tts-provider"
                                                            value={provider.id}
                                                            checked={selectedProvider === provider.id}
                                                            onChange={() => setSelectedProvider(provider.id)}
                                                        />
                                                        <div className="provider-info">
                                                            <span className="provider-name">{provider.name}</span>
                                                            <span className="provider-cost">{provider.cost_label}</span>
                                                        </div>
                                                        {provider.id === voiceOptions.default_provider && (
                                                            <span className="recommended-badge">✨ Recommended</span>
                                                        )}
                                                    </label>
                                                ))}
                                            </div>

                                            <div className="voice-selector-wrapper">
                                                <label className="voice-label">Voice:</label>
                                                <select
                                                    className="voice-select"
                                                    value={selectedVoice || ''}
                                                    onChange={(e) => setSelectedVoice(e.target.value)}
                                                >
                                                    {voiceOptions.voices[selectedProvider] &&
                                                        voiceOptions.voices[selectedProvider].map(voice => (
                                                            <option key={voice.id} value={voice.id}>
                                                                {voice.name} — {voice.tone}
                                                            </option>
                                                        ))
                                                    }
                                                </select>
                                                {voiceOptions.voices[selectedProvider] && (
                                                    <div className="voice-tone-hint">
                                                        {voiceOptions.voices[selectedProvider].find(v => v.id === selectedVoice)?.tone || ''}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* Step 4: Visual Settings — Image Source, Video Source, Background Mode */}
                                    {scriptAccepted && (
                                        <div className="tts-selector-section" style={{ borderTop: '1px solid rgba(212, 175, 55, 0.2)', paddingTop: '1.5rem' }}>
                                            <h3>🎨 Visual Settings</h3>

                                            {/* Image Source */}
                                            <p style={{ fontSize: '0.85rem', color: '#a0855a', marginBottom: '0.5rem', marginTop: '1rem' }}>
                                                Image Source
                                            </p>
                                            <div className="tts-provider-grid">
                                                {[
                                                    { id: 'stock', label: '🖼️ Stock Photos', desc: 'Pexels + Google image search', badge: null },
                                                    { id: 'ai_generated', label: '✨ Gemini AI', desc: 'AI-generated cinematic images', badge: 'Beta' }
                                                ].map(src => (
                                                    <label
                                                        key={src.id}
                                                        className={`tts-provider-card ${imageSource === src.id ? 'selected' : ''}`}
                                                    >
                                                        <input
                                                            type="radio"
                                                            name="img-source"
                                                            value={src.id}
                                                            checked={imageSource === src.id}
                                                            onChange={() => setImageSource(src.id)}
                                                        />
                                                        <div className="provider-info">
                                                            <span className="provider-name">{src.label}</span>
                                                            <span className="provider-cost" style={{ fontSize: '0.72rem' }}>{src.desc}</span>
                                                        </div>
                                                        {src.badge && (
                                                            <span className="recommended-badge" style={{ background: 'rgba(99,102,241,0.15)', color: '#818cf8' }}>🧪 {src.badge}</span>
                                                        )}
                                                    </label>
                                                ))}
                                            </div>

                                            {/* Video Background Source */}
                                            <p style={{ fontSize: '0.85rem', color: '#a0855a', marginBottom: '0.5rem', marginTop: '1.2rem' }}>
                                                Video Background
                                            </p>
                                            <div className="tts-provider-grid">
                                                {[
                                                    { id: 'stock', label: '🎬 Stock Videos', desc: 'Pexels stock video library', badge: null },
                                                    { id: 'veo', label: '✨ Gemini Veo', desc: 'AI-generated 8s cinematic clips (~1min/scene)', badge: 'Beta' }
                                                ].map(src => (
                                                    <label
                                                        key={src.id}
                                                        className={`tts-provider-card ${videoSource === src.id ? 'selected' : ''}`}
                                                    >
                                                        <input
                                                            type="radio"
                                                            name="vid-source"
                                                            value={src.id}
                                                            checked={videoSource === src.id}
                                                            onChange={() => setVideoSource(src.id)}
                                                        />
                                                        <div className="provider-info">
                                                            <span className="provider-name">{src.label}</span>
                                                            <span className="provider-cost" style={{ fontSize: '0.72rem' }}>{src.desc}</span>
                                                        </div>
                                                        {src.badge && (
                                                            <span className="recommended-badge" style={{ background: 'rgba(99,102,241,0.15)', color: '#818cf8' }}>🧪 {src.badge}</span>
                                                        )}
                                                    </label>
                                                ))}
                                            </div>

                                            {/* Veo Style — only shown when Gemini Veo is selected */}
                                            {videoSource === 'veo' && (
                                                <>
                                                    <p style={{ fontSize: '0.85rem', color: '#a0855a', marginBottom: '0.5rem', marginTop: '1.2rem' }}>
                                                        Veo Style
                                                    </p>
                                                    <div className="tts-provider-grid">
                                                        {[
                                                            { id: 'auto', label: '✨ Auto', desc: 'Scene 3 → Whiteboard · Scenes 4 & 6 → Illustration', badge: 'Recommended' },
                                                            { id: 'cinematic', label: '🎬 Cinematic', desc: 'Real-world environments, dramatic camera moves', badge: null },
                                                            { id: 'whiteboard', label: '✏️ Whiteboard', desc: 'Hand drawing on white canvas, all scenes', badge: null },
                                                            { id: 'illustration', label: '🖼️ Illustration', desc: '2D flat diagrams & motion graphics, all scenes', badge: null },
                                                        ].map(style => (
                                                            <label
                                                                key={style.id}
                                                                className={`tts-provider-card ${veoStyle === style.id ? 'selected' : ''}`}
                                                            >
                                                                <input
                                                                    type="radio"
                                                                    name="veo-style"
                                                                    value={style.id}
                                                                    checked={veoStyle === style.id}
                                                                    onChange={() => setVeoStyle(style.id)}
                                                                />
                                                                <div className="provider-info">
                                                                    <span className="provider-name">{style.label}</span>
                                                                    <span className="provider-cost" style={{ fontSize: '0.72rem' }}>{style.desc}</span>
                                                                </div>
                                                                {style.badge && (
                                                                    <span className="recommended-badge">✨ {style.badge}</span>
                                                                )}
                                                            </label>
                                                        ))}
                                                    </div>
                                                </>
                                            )}

                                            {/* Background Mode */}
                                            <p style={{ fontSize: '0.85rem', color: '#a0855a', marginBottom: '0.5rem', marginTop: '1.2rem' }}>
                                                Background Mode
                                            </p>
                                            <div className="tts-provider-grid">
                                                {[
                                                    { id: 'images_only', label: '🖼️ Images Only', desc: 'Book cover + images with Ken Burns effect', badge: 'Classic' },
                                                    { id: 'videos_only', label: '🎬 Videos Only', desc: 'Video backgrounds for all scenes (except cover)', badge: null },
                                                    { id: 'auto', label: '✨ Auto Mix', desc: 'Smart mix: cover → videos → images → gradient', badge: 'Recommended' }
                                                ].map(mode => (
                                                    <label
                                                        key={mode.id}
                                                        className={`tts-provider-card ${backgroundMode === mode.id ? 'selected' : ''}`}
                                                    >
                                                        <input
                                                            type="radio"
                                                            name="bg-mode"
                                                            value={mode.id}
                                                            checked={backgroundMode === mode.id}
                                                            onChange={() => setBackgroundMode(mode.id)}
                                                        />
                                                        <div className="provider-info">
                                                            <span className="provider-name">{mode.label}</span>
                                                            <span className="provider-cost" style={{ fontSize: '0.72rem' }}>{mode.desc}</span>
                                                        </div>
                                                        {mode.badge && (
                                                            <span className="recommended-badge">✨ {mode.badge}</span>
                                                        )}
                                                    </label>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Step 5: Generate Video Button */}
                                    {scriptAccepted && (
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
                                                    <>🚀 Generate Video ({selectedProvider} / {selectedVoice}{imageSource === 'ai_generated' ? ' / AI Images' : ''}{videoSource === 'veo' ? ' / Veo' : ''})</>
                                                )}
                                            </button>
                                            {isGenerating && (
                                                <div className="generation-progress">
                                                    <div className="progress-steps">
                                                        <span className="step active">🔊 Audio</span>
                                                        <span className="step-arrow">→</span>
                                                        <span className={`step ${generationStep.includes('rendering') ? 'active' : ''}`}>🎬 Video</span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
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
