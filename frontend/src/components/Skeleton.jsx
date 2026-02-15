import './Skeleton.css';

/**
 * Skeleton — shimmer loading placeholder
 * 
 * @param {'text'|'title'|'avatar'|'card'|'button'} variant
 * @param {number} width  — CSS width (px or %)
 * @param {number} height — CSS height (px)
 * @param {number} count  — how many to render
 * @param {string} className — extra className
 */
export default function Skeleton({
    variant = 'text',
    width,
    height,
    count = 1,
    className = '',
}) {
    const items = Array.from({ length: count }, (_, i) => i);

    return (
        <>
            {items.map((i) => (
                <div
                    key={i}
                    className={`skeleton skeleton-${variant} ${className}`}
                    style={{
                        width: width || undefined,
                        height: height || undefined,
                    }}
                    aria-hidden="true"
                />
            ))}
        </>
    );
}

/**
 * SkeletonCard — Full card placeholder for grids
 */
export function SkeletonCard() {
    return (
        <div className="skeleton-card" aria-hidden="true">
            <div className="skeleton skeleton-title" style={{ width: '80%' }} />
            <div className="skeleton skeleton-text" />
            <div className="skeleton skeleton-text" style={{ width: '60%' }} />
            <div className="skeleton-card-footer">
                <div className="skeleton skeleton-button" style={{ width: 80 }} />
                <div className="skeleton skeleton-button" style={{ width: 60 }} />
            </div>
        </div>
    );
}

/**
 * ContentLibrarySkeleton — Full page loading skeleton for Content Library
 */
export function ContentLibrarySkeleton() {
    return (
        <div className="skeleton-page" aria-label="Loading content...">
            {/* Header skeleton */}
            <div className="skeleton-header-block">
                <div className="skeleton skeleton-title" style={{ width: '220px' }} />
                <div className="skeleton skeleton-text" style={{ width: '360px' }} />
            </div>

            {/* Filter bar skeleton */}
            <div className="skeleton-filter-bar">
                <div className="skeleton skeleton-input" />
                <div className="skeleton skeleton-select" />
                <div className="skeleton skeleton-select" />
            </div>

            {/* Cards grid skeleton */}
            <div className="skeleton-grid">
                {Array.from({ length: 6 }, (_, i) => (
                    <SkeletonCard key={i} />
                ))}
            </div>
        </div>
    );
}
