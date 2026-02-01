import { useState, useEffect } from 'react';
import { fetchSources, fetchContentTypes } from '../services/contentApi';
import './FilterBar.css';

export default function FilterBar({ filters, onChange, onSelectAll, allSelected }) {
    const [sources, setSources] = useState([]);
    const [contentTypes, setContentTypes] = useState([]);

    const loadFilterOptions = async () => {
        try {
            const [sourcesData, typesData] = await Promise.all([
                fetchSources(),
                fetchContentTypes()
            ]);
            setSources(sourcesData);
            setContentTypes(typesData);
        } catch (err) {
            console.error('Failed to load filter options:', err);
        }
    };

    useEffect(() => {
        loadFilterOptions();
    }, []);

    const handleChange = (key, value) => {
        onChange({ [key]: value });
    };

    const handleClearFilters = () => {
        onChange({
            source: '',
            date_range: 'all',
            content_type: '',
            status: '',
            search: ''
        });
    };

    const hasActiveFilters = filters.source || filters.content_type || filters.status || filters.search;

    return (
        <div className="filter-bar">
            <div className="filter-row">
                <div className="filter-group">
                    <label htmlFor="search">Search</label>
                    <input
                        id="search"
                        type="text"
                        placeholder="Search articles..."
                        value={filters.search}
                        onChange={(e) => handleChange('search', e.target.value)}
                        className="search-input"
                    />
                </div>

                <div className="filter-group">
                    <label htmlFor="source">Source</label>
                    <select
                        id="source"
                        value={filters.source}
                        onChange={(e) => handleChange('source', e.target.value)}
                        className="filter-select"
                    >
                        <option value="">All Sources</option>
                        {sources.map(source => (
                            <option key={source} value={source}>{source}</option>
                        ))}
                    </select>
                </div>

                <div className="filter-group">
                    <label htmlFor="date_range">Date Range</label>
                    <select
                        id="date_range"
                        value={filters.date_range}
                        onChange={(e) => handleChange('date_range', e.target.value)}
                        className="filter-select"
                    >
                        <option value="yesterday">Yesterday</option>
                        <option value="today">Today</option>
                        <option value="last_7_days">Last 7 Days</option>
                        <option value="last_30_days">Last 30 Days</option>
                        <option value="last_90_days">Last 90 Days</option>
                        <option value="all">All Time</option>
                    </select>
                </div>

                <div className="filter-group">
                    <label htmlFor="content_type">Content Type</label>
                    <select
                        id="content_type"
                        value={filters.content_type}
                        onChange={(e) => handleChange('content_type', e.target.value)}
                        className="filter-select"
                    >
                        <option value="">All Types</option>
                        {contentTypes.map(type => (
                            <option key={type} value={type}>
                                {type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="filter-group">
                    <label htmlFor="status">Status</label>
                    <select
                        id="status"
                        value={filters.status}
                        onChange={(e) => handleChange('status', e.target.value)}
                        className="filter-select"
                    >
                        <option value="">All Status</option>
                        <option value="unprocessed">New</option>
                        <option value="has_script">Script Ready</option>
                        <option value="has_video">Video Created</option>
                    </select>
                </div>

                <div className="filter-actions">
                    <button
                        onClick={onSelectAll}
                        className="btn-secondary"
                        title={allSelected ? "Deselect all" : "Select all"}
                    >
                        {allSelected ? '☑' : '☐'} All
                    </button>

                    {hasActiveFilters && (
                        <button
                            onClick={handleClearFilters}
                            className="btn-clear"
                        >
                            Clear Filters
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
