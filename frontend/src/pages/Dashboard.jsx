import { useState, useEffect } from 'react';
import { videoApi } from '../services/api';
import './Dashboard.css';

function Dashboard() {
    const [videos, setVideos] = useState([]);
    const [stats, setStats] = useState({ total: 0, by_status: {} });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = async () => {
        try {
            const [videosRes, statsRes] = await Promise.all([
                videoApi.list(),
                videoApi.stats()
            ]);
            setVideos(videosRes.data.videos);
            setStats(statsRes.data);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // Auto-refresh every 5 seconds
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleDownload = async (id, scriptId) => {
        try {
            const response = await videoApi.download(id);
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `video_${scriptId}.mp4`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            alert(`Download failed: ${err.message}`);
        }
    };

    const getStatusBadge = (status) => {
        const badges = {
            pending: { class: 'badge-gray', text: 'Pending' },
            rendering: { class: 'badge-blue pulse', text: 'Rendering...' },
            completed: { class: 'badge-green', text: 'Completed' },
            failed: { class: 'badge-red', text: 'Failed' }
        };
        const badge = badges[status] || badges.pending;
        return <span className={`badge ${badge.class}`}>{badge.text}</span>;
    };

    if (loading) return <div className="loading">Loading videos...</div>;
    if (error) return <div className="error">Error: {error}</div>;

    return (
        <div className="dashboard">
            <header className="dashboard-header">
                <h1>AIVideoGen Dashboard</h1>
                <div className="stats">
                    <div className="stat">
                        <span className="stat-label">Total Videos</span>
                        <span className="stat-value">{stats.total}</span>
                    </div>
                    <div className="stat">
                        <span className="stat-label">Completed</span>
                        <span className="stat-value">{stats.by_status.completed || 0}</span>
                    </div>
                    <div className="stat">
                        <span className="stat-label">Rendering</span>
                        <span className="stat-value">{stats.by_status.rendering || 0}</span>
                    </div>
                </div>
            </header>

            <div className="video-table-container">
                <table className="video-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Script ID</th>
                            <th>Status</th>
                            <th>Duration</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {videos.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="no-data">No videos generated yet</td>
                            </tr>
                        ) : (
                            videos.map(video => (
                                <tr key={video.id}>
                                    <td>{video.id}</td>
                                    <td>{video.script_id}</td>
                                    <td>{getStatusBadge(video.status)}</td>
                                    <td>{video.duration ? `${video.duration.toFixed(1)}s` : '-'}</td>
                                    <td>{new Date(video.created_at).toLocaleString()}</td>
                                    <td>
                                        {video.status === 'completed' && (
                                            <button
                                                className="btn-download"
                                                onClick={() => handleDownload(video.id, video.script_id)}
                                            >
                                                Download
                                            </button>
                                        )}
                                        {video.status === 'failed' && video.error_message && (
                                            <span className="error-hint" title={video.error_message}>
                                                ⚠️
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default Dashboard;
