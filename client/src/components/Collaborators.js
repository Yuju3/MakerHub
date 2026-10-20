import React, { useEffect, useId, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Users, Crown, X, Search } from 'lucide-react';

const MAX_VISIBLE = 3;       // chips shown inline before collapsing into "+N more"
const SEARCH_THRESHOLD = 8;  // show a search box in the full list above this many people

// Owner first, then everyone else in their original order (no duplicates).
const orderMembers = (project) => {
  const members = Array.isArray(project?.members) ? [...new Set(project.members)] : [];
  const owner = project?.ownerId;
  return owner && members.includes(owner)
    ? [owner, ...members.filter((m) => m !== owner)]
    : members;
};

const Chip = ({ id, isOwner, isYou }) => (
  <span className="collab-chip" title={id}>
    {isOwner && <Crown size={12} aria-label="Owner" />}
    <span className="collab-chip-name">{id}</span>
    {isYou && <span className="collab-chip-you">(you)</span>}
  </span>
);

/**
 * Shows who is on a project.
 * Up to MAX_VISIBLE people are shown inline; if there are more, a "+N more" button
 * opens a scrollable dialog with everyone.
 * Props:
 *  - project:       { name, ownerId, members: [userId, ...] }
 *  - currentUserId: optional, marks the signed-in user with "(you)"
 */
const Collaborators = ({ project, currentUserId }) => {
  const members = useMemo(() => orderMembers(project), [project]);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const triggerRef = useRef(null);
  const closeRef = useRef(null);
  const titleId = useId();

  // Dialog behavior: Escape closes, page scroll is locked, focus moves in and then back out.
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setOpen(false);
        setQuery('');
      }
    };
    document.addEventListener('keydown', onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeRef.current?.focus();
    const trigger = triggerRef.current;
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = previousOverflow;
      trigger?.focus();
    };
  }, [open]);

  const closeDialog = () => {
    setOpen(false);
    setQuery('');
  };

  const visible = members.slice(0, MAX_VISIBLE);
  const hiddenCount = members.length - visible.length;
  const filtered = members.filter((m) => m.toLowerCase().includes(query.trim().toLowerCase()));

  return (
    <div className="collab">
      <div className="collab-label">
        <Users size={14} aria-hidden="true" />
        <span>Collaborators ({members.length})</span>
      </div>

      {members.length === 0 ? (
        <p className="collab-empty">No collaborators yet</p>
      ) : (
        <div className="collab-chips">
          {visible.map((id) => (
            <Chip key={id} id={id} isOwner={id === project?.ownerId} isYou={id === currentUserId} />
          ))}
          {hiddenCount > 0 && (
            <button
              type="button"
              ref={triggerRef}
              className="collab-more"
              onClick={(e) => {
                e.stopPropagation(); // don't also open the project when the card is clicked
                setOpen(true);
              }}
            >
              +{hiddenCount} more &middot; View all
            </button>
          )}
        </div>
      )}

      {open &&
        createPortal(
          <div className="modal-overlay" onClick={(e) => { e.stopPropagation(); closeDialog(); }}>
            <div
              className="modal-dialog"
              role="dialog"
              aria-modal="true"
              aria-labelledby={titleId}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <div style={{ minWidth: 0 }}>
                  <h3 id={titleId} style={{ margin: 0 }}>Collaborators ({members.length})</h3>
                  <p className="modal-subtitle">{project?.name}</p>
                </div>
                <button
                  type="button"
                  ref={closeRef}
                  className="error-card-close"
                  onClick={closeDialog}
                  aria-label="Close collaborators list"
                >
                  <X size={18} />
                </button>
              </div>

              {members.length > SEARCH_THRESHOLD && (
                <div className="collab-search">
                  <Search size={16} aria-hidden="true" />
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Search collaborators"
                    aria-label="Search collaborators"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                </div>
              )}

              <ul className="collab-list">
                {filtered.map((id) => (
                  <li key={id} className="collab-row">
                    <span className="collab-chip-name" title={id}>{id}</span>
                    {id === project?.ownerId && <span className="collab-badge">Owner</span>}
                    {id === currentUserId && <span className="collab-badge collab-badge-you">You</span>}
                  </li>
                ))}
                {filtered.length === 0 && <li className="collab-empty">No matches</li>}
              </ul>
            </div>
          </div>,
          document.body
        )}
    </div>
  );
};

export default Collaborators;