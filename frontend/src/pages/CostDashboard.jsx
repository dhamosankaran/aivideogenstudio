import { useState, useEffect } from 'react';
import { fetchCostEstimate, fetchDailySpend } from '../services/costApi';

// ── Inline styles (no extra CSS file) ────────────────────────────────────────

const S = {
    page: {
        padding: '24px',
        maxWidth: '1100px',
        margin: '0 auto',
        fontFamily: 'inherit',
        color: '#e2e8f0',
    },
    header: {
        marginBottom: '24px',
    },
    h1: {
        fontSize: '22px',
        fontWeight: '700',
        color: '#f1f5f9',
        margin: '0 0 4px 0',
    },
    subtitle: {
        fontSize: '13px',
        color: '#94a3b8',
        margin: 0,
    },
    // Alert banner
    alert: {
        background: 'linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)',
        border: '1px solid #ef4444',
        borderRadius: '10px',
        padding: '16px 20px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
    },
    alertIcon: { fontSize: '22px', flexShrink: 0, marginTop: '1px' },
    alertContent: { flex: 1 },
    alertTitle: { fontSize: '15px', fontWeight: '700', color: '#fca5a5', margin: '0 0 6px 0' },
    alertBody: { fontSize: '13px', color: '#fecaca', margin: 0, lineHeight: '1.6' },
    alertBadge: {
        background: '#dc2626',
        color: '#fff',
        borderRadius: '6px',
        padding: '2px 8px',
        fontSize: '12px',
        fontWeight: '600',
    },
    // Stat cards
    statsRow: {
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px',
        marginBottom: '28px',
    },
    card: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '10px',
        padding: '18px 20px',
    },
    cardDanger: {
        background: '#1e293b',
        border: '1px solid #ef4444',
        borderRadius: '10px',
        padding: '18px 20px',
    },
    cardGood: {
        background: '#1e293b',
        border: '1px solid #22c55e',
        borderRadius: '10px',
        padding: '18px 20px',
    },
    cardLabel: { fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 8px 0', fontWeight: '600' },
    cardValue: { fontSize: '28px', fontWeight: '800', color: '#f1f5f9', margin: '0 0 4px 0' },
    cardValueDanger: { fontSize: '28px', fontWeight: '800', color: '#f87171', margin: '0 0 4px 0' },
    cardValueGood: { fontSize: '28px', fontWeight: '800', color: '#4ade80', margin: '0 0 4px 0' },
    cardMeta: { fontSize: '12px', color: '#64748b', margin: 0 },
    // Section
    section: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '10px',
        padding: '20px 24px',
        marginBottom: '20px',
    },
    sectionTitle: { fontSize: '15px', fontWeight: '700', color: '#f1f5f9', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' },
    // Calculator
    calcGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px',
        marginBottom: '20px',
    },
    label: { display: 'block', fontSize: '11px', fontWeight: '600', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' },
    select: {
        width: '100%',
        background: '#0f172a',
        border: '1px solid #334155',
        borderRadius: '6px',
        color: '#e2e8f0',
        padding: '8px 10px',
        fontSize: '13px',
        cursor: 'pointer',
        outline: 'none',
    },
    calcResult: {
        background: '#0f172a',
        borderRadius: '8px',
        padding: '16px 20px',
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr) auto',
        gap: '16px',
        alignItems: 'center',
        border: '1px solid #1e293b',
    },
    calcItem: {},
    calcItemLabel: { fontSize: '11px', color: '#64748b', margin: '0 0 4px 0', fontWeight: '600' },
    calcItemValue: { fontSize: '20px', fontWeight: '700', color: '#e2e8f0', margin: 0 },
    calcTotal: {
        background: '#1d4ed8',
        borderRadius: '8px',
        padding: '12px 20px',
        textAlign: 'center',
    },
    calcTotalLabel: { fontSize: '11px', color: '#93c5fd', margin: '0 0 4px 0', fontWeight: '600' },
    calcTotalValue: { fontSize: '24px', fontWeight: '800', color: '#fff', margin: 0 },
    savingsBadge: {
        display: 'inline-block',
        marginTop: '12px',
        background: '#14532d',
        border: '1px solid #22c55e',
        borderRadius: '6px',
        padding: '6px 14px',
        fontSize: '13px',
        color: '#4ade80',
        fontWeight: '600',
    },
    // Table
    table: {
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: '13px',
    },
    th: {
        textAlign: 'left',
        padding: '8px 12px',
        color: '#64748b',
        fontWeight: '600',
        fontSize: '11px',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        borderBottom: '1px solid #334155',
    },
    thRight: {
        textAlign: 'right',
        padding: '8px 12px',
        color: '#64748b',
        fontWeight: '600',
        fontSize: '11px',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        borderBottom: '1px solid #334155',
    },
    td: { padding: '10px 12px', borderBottom: '1px solid #1e293b', color: '#e2e8f0' },
    tdRight: { padding: '10px 12px', borderBottom: '1px solid #1e293b', color: '#e2e8f0', textAlign: 'right' },
    tdMuted: { padding: '10px 12px', borderBottom: '1px solid #1e293b', color: '#64748b' },
    tdDanger: { padding: '10px 12px', borderBottom: '1px solid #1e293b', color: '#f87171', fontWeight: '700', textAlign: 'right' },
    tdGood: { padding: '10px 12px', borderBottom: '1px solid #1e293b', color: '#4ade80', fontWeight: '700', textAlign: 'right' },
    rowHighlight: { background: '#1a0000' },
    totalRow: { background: '#0f172a', fontWeight: '700' },
    empty: { textAlign: 'center', padding: '32px', color: '#475569' },
    loading: { textAlign: 'center', padding: '60px', color: '#64748b' },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(val) {
    return `$${Number(val).toFixed(2)}`;
}

function fmtSmall(val) {
    return `$${Number(val).toFixed(4)}`;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function CostDashboard() {
    // Calculator state
    const [calcConfig, setCalcConfig] = useState({
        content_type: 'book_review',
        video_source: 'veo',
        image_source: 'ai_generated',
        tts_provider: 'openai',
    });
    const [estimate, setEstimate] = useState(null);
    const [calcLoading, setCalcLoading] = useState(false);

    // History state
    const [history, setHistory] = useState(null);
    const [histDays, setHistDays] = useState(30);
    const [histLoading, setHistLoading] = useState(true);

    // Load estimate whenever config changes
    useEffect(() => {
        setCalcLoading(true);
        fetchCostEstimate(calcConfig)
            .then(setEstimate)
            .catch(console.error)
            .finally(() => setCalcLoading(false));
    }, [calcConfig]);

    // Load history
    useEffect(() => {
        setHistLoading(true);
        fetchDailySpend(histDays)
            .then(setHistory)
            .catch(console.error)
            .finally(() => setHistLoading(false));
    }, [histDays]);

    const handleCalcChange = (field) => (e) => {
        setCalcConfig(prev => ({ ...prev, [field]: e.target.value }));
    };

    // Derive stats from history
    const march1Data = history?.days?.find(d => d.date === '2026-03-01');
    const monthTotal = history?.total_estimated ?? 0;

    const perVideoVeo = estimate?.total_per_video ?? 9.96;
    const perVideoStock = estimate?.without_veo_total ?? 0.36;
    const savings = estimate?.veo_savings_per_video ?? 9.60;

    return (
        <div style={S.page}>
            {/* Header */}
            <div style={S.header}>
                <h1 style={S.h1}>Cost Tracker</h1>
                <p style={S.subtitle}>Gemini API spend estimation — prices as of March 2026 (estimates, not actual Google billing)</p>
            </div>

            {/* Alert Banner */}
            <div style={S.alert}>
                <span style={S.alertIcon}>🔴</span>
                <div style={S.alertContent}>
                    <p style={S.alertTitle}>
                        March 1 Bill: ~$34 &nbsp;
                        <span style={S.alertBadge}>Veo was 96% of cost</span>
                    </p>
                    <p style={S.alertBody}>
                        <strong>Root cause:</strong> Each book review triggers 3 Veo 3.1 clips × 8s × $0.40/sec = <strong>$9.60 in Veo per video</strong>.<br />
                        3 completed videos ($28.80 Veo) + test scripts ($3.20) + Gemini images ($2.01) + TTS ($0.12) ≈ <strong>$34</strong>.<br />
                        Videos 24–26 failed with <code style={{ background: '#450a0a', padding: '1px 5px', borderRadius: '3px', fontSize: '12px' }}>allow_adult for personGeneration not supported</code> before Veo ran — those clips were not billed.
                    </p>
                </div>
            </div>

            {/* Stat Cards */}
            <div style={S.statsRow}>
                <div style={S.cardDanger}>
                    <p style={S.cardLabel}>March 1 Spend</p>
                    <p style={S.cardValueDanger}>{march1Data ? fmt(march1Data.estimated_cost) : '~$34'}</p>
                    <p style={S.cardMeta}>{march1Data ? `${march1Data.videos_attempted} videos attempted` : '6 videos attempted'}</p>
                </div>
                <div style={S.card}>
                    <p style={S.cardLabel}>Per Video (w/ Veo)</p>
                    <p style={S.cardValue}>{fmt(perVideoVeo)}</p>
                    <p style={S.cardMeta}>3 Veo clips + 5 images + TTS</p>
                </div>
                <div style={S.cardGood}>
                    <p style={S.cardLabel}>Per Video (stock only)</p>
                    <p style={S.cardValueGood}>{fmt(perVideoStock)}</p>
                    <p style={S.cardMeta}>Gemini images + TTS, no Veo</p>
                </div>
                <div style={S.card}>
                    <p style={S.cardLabel}>Veo Savings / Video</p>
                    <p style={S.cardValue}>{fmt(savings)}</p>
                    <p style={S.cardMeta}>Switch to stock video to save this</p>
                </div>
            </div>

            {/* Cost Calculator */}
            <div style={S.section}>
                <h2 style={S.sectionTitle}>
                    <span>🧮</span> Cost Calculator
                </h2>
                <div style={S.calcGrid}>
                    <div>
                        <label style={S.label}>Content Type</label>
                        <select style={S.select} value={calcConfig.content_type} onChange={handleCalcChange('content_type')}>
                            <option value="book_review">Book Review</option>
                            <option value="viral_news">Viral News</option>
                        </select>
                    </div>
                    <div>
                        <label style={S.label}>Video Source</label>
                        <select style={S.select} value={calcConfig.video_source} onChange={handleCalcChange('video_source')}>
                            <option value="veo">Veo 3.1 AI ($0.40/sec)</option>
                            <option value="stock">Stock (Free)</option>
                        </select>
                    </div>
                    <div>
                        <label style={S.label}>Image Source</label>
                        <select style={S.select} value={calcConfig.image_source} onChange={handleCalcChange('image_source')}>
                            <option value="ai_generated">Gemini AI ($0.067/img)</option>
                            <option value="stock">Stock (Free)</option>
                        </select>
                    </div>
                    <div>
                        <label style={S.label}>TTS Provider</label>
                        <select style={S.select} value={calcConfig.tts_provider} onChange={handleCalcChange('tts_provider')}>
                            <option value="openai">OpenAI ($0.02)</option>
                            <option value="google">Google ($0.01)</option>
                            <option value="elevenlabs">ElevenLabs ($0.15)</option>
                        </select>
                    </div>
                </div>

                {calcLoading ? (
                    <div style={S.loading}>Calculating...</div>
                ) : estimate ? (
                    <>
                        <div style={S.calcResult}>
                            <div style={S.calcItem}>
                                <p style={S.calcItemLabel}>Veo Clips</p>
                                <p style={S.calcItemValue}>
                                    {estimate.veo_clips} × {fmt(estimate.pricing?.veo_per_clip_8s ?? 3.20)}
                                </p>
                            </div>
                            <div style={S.calcItem}>
                                <p style={S.calcItemLabel}>Gemini Images</p>
                                <p style={S.calcItemValue}>
                                    {estimate.gemini_images} × {fmtSmall(estimate.pricing?.gemini_image_1k ?? 0.067)}
                                </p>
                            </div>
                            <div style={S.calcItem}>
                                <p style={S.calcItemLabel}>TTS Audio</p>
                                <p style={S.calcItemValue}>{fmt(estimate.tts_cost)}</p>
                            </div>
                            <div style={S.calcItem}>
                                <p style={S.calcItemLabel}>Veo Cost</p>
                                <p style={{ ...S.calcItemValue, color: estimate.veo_cost > 0 ? '#f87171' : '#4ade80' }}>
                                    {fmt(estimate.veo_cost)}
                                </p>
                            </div>
                            <div style={S.calcTotal}>
                                <p style={S.calcTotalLabel}>Total / Video</p>
                                <p style={S.calcTotalValue}>{fmt(estimate.total_per_video)}</p>
                            </div>
                        </div>

                        {estimate.veo_savings_per_video > 0 && (
                            <div style={S.savingsBadge}>
                                💡 Switch to stock video → save {fmt(estimate.veo_savings_per_video)} per video
                                ({fmt(estimate.veo_savings_per_video * 10)}/month at 10 videos)
                            </div>
                        )}
                    </>
                ) : null}
            </div>

            {/* Pricing Reference */}
            <div style={S.section}>
                <h2 style={S.sectionTitle}><span>💰</span> Pricing Reference (March 2026)</h2>
                <table style={S.table}>
                    <thead>
                        <tr>
                            <th style={S.th}>Service</th>
                            <th style={S.th}>Model</th>
                            <th style={S.thRight}>Unit Price</th>
                            <th style={S.thRight}>Per Video</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style={S.td}>Veo Video Generation</td>
                            <td style={S.tdMuted}>veo-3.1-generate-preview</td>
                            <td style={S.tdRight}>$0.40 / second</td>
                            <td style={{ ...S.tdRight, color: '#f87171', fontWeight: '700' }}>$9.60 (3 clips × 8s)</td>
                        </tr>
                        <tr>
                            <td style={S.td}>Gemini Image (1K)</td>
                            <td style={S.tdMuted}>gemini-3.1-flash-image-preview</td>
                            <td style={S.tdRight}>$0.0672 / image</td>
                            <td style={S.tdRight}>$0.34 (5 images)</td>
                        </tr>
                        <tr>
                            <td style={S.td}>TTS — OpenAI</td>
                            <td style={S.tdMuted}>tts-1</td>
                            <td style={S.tdRight}>~$0.02 / video</td>
                            <td style={S.tdRight}>$0.02</td>
                        </tr>
                        <tr>
                            <td style={S.td}>TTS — Google</td>
                            <td style={S.tdMuted}>Journey / Neural2</td>
                            <td style={S.tdRight}>~$0.01 / video</td>
                            <td style={S.tdRight}>$0.01</td>
                        </tr>
                        <tr>
                            <td style={S.td}>TTS — ElevenLabs</td>
                            <td style={S.tdMuted}>Various</td>
                            <td style={S.tdRight}>~$0.15 / video</td>
                            <td style={S.tdRight}>$0.15</td>
                        </tr>
                        <tr>
                            <td style={S.td}>Stock Images / Video</td>
                            <td style={S.tdMuted}>Pexels / Unsplash</td>
                            <td style={S.tdRight}>Free</td>
                            <td style={S.tdRight}>$0.00</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            {/* Daily Spend History */}
            <div style={S.section}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h2 style={{ ...S.sectionTitle, margin: 0 }}><span>📅</span> Daily Spend History</h2>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <label style={{ ...S.label, margin: 0 }}>Last</label>
                        <select style={{ ...S.select, width: 'auto' }} value={histDays} onChange={e => setHistDays(Number(e.target.value))}>
                            <option value={7}>7 days</option>
                            <option value={30}>30 days</option>
                            <option value={90}>90 days</option>
                        </select>
                    </div>
                </div>

                {histLoading ? (
                    <div style={S.loading}>Loading history...</div>
                ) : (
                    <>
                        <table style={S.table}>
                            <thead>
                                <tr>
                                    <th style={S.th}>Date</th>
                                    <th style={S.th}>Videos</th>
                                    <th style={S.th}>Note</th>
                                    <th style={S.thRight}>Veo Cost</th>
                                    <th style={S.thRight}>Images</th>
                                    <th style={S.thRight}>TTS</th>
                                    <th style={S.thRight}>Estimated Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {!history?.days?.length ? (
                                    <tr>
                                        <td colSpan={7} style={S.empty}>No video generation history found</td>
                                    </tr>
                                ) : (
                                    <>
                                        {history.days.map(day => {
                                            const isMarch1 = day.date === '2026-03-01';
                                            const rowStyle = isMarch1 ? { ...S.td, background: '#1a0000' } : S.td;
                                            const tdR = isMarch1 ? { ...S.tdRight, background: '#1a0000' } : S.tdRight;
                                            const totalStyle = isMarch1
                                                ? { ...S.tdDanger, background: '#1a0000' }
                                                : S.tdRight;
                                            return (
                                                <tr key={day.date}>
                                                    <td style={rowStyle}>
                                                        {day.date}
                                                        {isMarch1 && (
                                                            <span style={{ marginLeft: '8px', background: '#dc2626', color: '#fff', borderRadius: '4px', padding: '1px 6px', fontSize: '10px', fontWeight: '700' }}>
                                                                ← BILLED
                                                            </span>
                                                        )}
                                                    </td>
                                                    <td style={rowStyle}>{day.videos_attempted}</td>
                                                    <td style={{ ...rowStyle, color: '#94a3b8', fontSize: '12px' }}>{day.note}</td>
                                                    <td style={{ ...tdR, color: day.veo_cost > 0 ? '#f87171' : '#64748b' }}>{fmt(day.veo_cost)}</td>
                                                    <td style={tdR}>{fmt(day.image_cost)}</td>
                                                    <td style={tdR}>{fmt(day.tts_cost)}</td>
                                                    <td style={totalStyle}>{fmt(day.estimated_cost)}</td>
                                                </tr>
                                            );
                                        })}
                                        <tr style={{ background: '#0f172a' }}>
                                            <td colSpan={6} style={{ ...S.td, fontWeight: '700', background: '#0f172a' }}>
                                                Total (last {histDays} days)
                                            </td>
                                            <td style={{ ...S.tdDanger, background: '#0f172a', fontSize: '16px' }}>
                                                {fmt(monthTotal)}
                                            </td>
                                        </tr>
                                    </>
                                )}
                            </tbody>
                        </table>

                        <p style={{ fontSize: '11px', color: '#475569', marginTop: '12px', marginBottom: 0 }}>
                            * Estimates only. Book reviews assumed to use Veo (matching March 1 observed spend). Actual Google billing may differ.
                        </p>
                    </>
                )}
            </div>
        </div>
    );
}
