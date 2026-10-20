import React from 'react';
import { AlertCircle, X } from 'lucide-react';

/**
 * Reusable inline error card.
 * Props:
 *  - title:     short heading (e.g. "Sign in failed")
 *  - message:   explanation text
 *  - onDismiss: optional; when provided, shows a close button
 *  - children:  optional extra content (e.g. a helpful link)
 */
const ErrorCard = ({ title = 'Something went wrong', message, onDismiss, children }) => {
  return (
    <div className="error-card" role="alert">
      <AlertCircle className="error-card-icon" size={22} aria-hidden="true" />
      <div className="error-card-body">
        <p className="error-card-title">{title}</p>
        {message && <p className="error-card-message">{message}</p>}
        {children}
      </div>
      {onDismiss && (
        <button
          type="button"
          className="error-card-close"
          onClick={onDismiss}
          aria-label="Dismiss error"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};

export default ErrorCard;