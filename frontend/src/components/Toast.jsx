import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import './Toast.css';

const ToastContext = createContext(null);

let toastId = 0;

export function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([]);

    const addToast = useCallback((message, type = 'info', duration = 5000) => {
        const id = ++toastId;
        setToasts(prev => [...prev, { id, message, type, duration }]);
        if (duration > 0) {
            setTimeout(() => {
                setToasts(prev => prev.filter(t => t.id !== id));
            }, duration);
        }
        return id;
    }, []);

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const toast = useCallback({
        success: (msg, dur) => addToast(msg, 'success', dur),
        error: (msg, dur) => addToast(msg, 'error', dur ?? 8000),
        warning: (msg, dur) => addToast(msg, 'warning', dur),
        info: (msg, dur) => addToast(msg, 'info', dur),
    }, [addToast]);

    // Reassign methods directly
    const toastApi = Object.assign(
        (msg, type, dur) => addToast(msg, type, dur),
        {
            success: (msg, dur) => addToast(msg, 'success', dur),
            error: (msg, dur) => addToast(msg, 'error', dur ?? 8000),
            warning: (msg, dur) => addToast(msg, 'warning', dur),
            info: (msg, dur) => addToast(msg, 'info', dur),
        }
    );

    return (
        <ToastContext.Provider value={toastApi}>
            {children}
            <div className="toast-container" role="status" aria-live="polite">
                {toasts.map(t => (
                    <ToastItem key={t.id} toast={t} onClose={() => removeToast(t.id)} />
                ))}
            </div>
        </ToastContext.Provider>
    );
}

export function useToast() {
    const ctx = useContext(ToastContext);
    if (!ctx) throw new Error('useToast must be used within ToastProvider');
    return ctx;
}

const ICONS = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
};

function ToastItem({ toast, onClose }) {
    const [exiting, setExiting] = useState(false);
    const Icon = ICONS[toast.type] || Info;

    const handleClose = () => {
        setExiting(true);
        setTimeout(onClose, 200);
    };

    return (
        <div className={`toast toast-${toast.type} ${exiting ? 'toast-exit' : ''}`}>
            <Icon className="toast-icon" size={18} />
            <span className="toast-message">{toast.message}</span>
            <button className="toast-close" onClick={handleClose} aria-label="Close">
                <X size={14} />
            </button>
        </div>
    );
}
