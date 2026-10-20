import React, { useState } from 'react';
import { UserPlus } from 'lucide-react';
import ErrorCard from './ErrorCard';

/**
 * "Join Existing Project" card.
 * Collapsed: a clickable dashed card. Expanded: an inline form that asks for a project ID.
 * Props:
 *  - userId:             the signed-in user's ID
 *  - existingProjectIds: IDs of projects the user already belongs to
 *  - onJoined(project):  called with the project returned by the server on success
 */
const JoinProject = ({ userId, existingProjectIds = [], onJoined }) => {
  const [open, setOpen] = useState(false);
  const [projectId, setProjectId] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const reset = () => {
    setOpen(false);
    setProjectId('');
    setError(null);
  };

  const handleJoin = async (e) => {
    e.preventDefault();
    const id = projectId.trim();
    if (!id) return;

    if (!userId) {
      setError({ title: 'Please sign in again', message: 'We could not tell who you are. Sign in and try again.' });
      return;
    }
    if (existingProjectIds.includes(id)) {
      setError({ title: 'Already a member', message: `You are already part of project "${id}".` });
      return;
    }

    setError(null);
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:5000/join_project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, projectId: id })
      });
      const data = await response.json().catch(() => ({}));
      if (response.status === 404) {
        setError({
          title: 'Project not found',
          message: `No project with ID "${id}" exists. Check the ID with your teammate and try again.`
        });
        return;
      }
      if (!response.ok) {
        setError({ title: 'Could not join project', message: data.error || 'Something went wrong.' });
        return;
      }
      onJoined(data);
      reset();
    } catch (err) {
      setError({
        title: 'Cannot reach the server',
        message: 'Make sure the MakerHub backend is running, then try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  if (!open) {
    return (
      <button type="button" className="card join-card" onClick={() => setOpen(true)}>
        <UserPlus size={32} color="var(--ut-burnt-orange)" aria-hidden="true" />
        <h3>Join Existing Project</h3>
        <p>Enter a project ID to collaborate</p>
      </button>
    );
  }

  return (
    <form className="card join-card-open" onSubmit={handleJoin}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <UserPlus size={24} color="var(--ut-burnt-orange)" aria-hidden="true" />
        <h3 style={{ margin: 0 }}>Join Existing Project</h3>
      </div>

      {error && <ErrorCard title={error.title} message={error.message} onDismiss={() => setError(null)} />}

      <div className="form-group" style={{ marginBottom: '1rem' }}>
        <label className="form-label" htmlFor="joinProjectId">Project ID</label>
        <input
          id="joinProjectId"
          className="form-control"
          placeholder="e.g. ECE364D-01"
          value={projectId}
          onChange={(e) => { setProjectId(e.target.value); setError(null); }}
          autoFocus
          required
        />
      </div>

      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={loading}>
          {loading ? 'Joining...' : 'Join Project'}
        </button>
        <button type="button" className="btn btn-secondary" onClick={reset} disabled={loading}>
          Cancel
        </button>
      </div>
    </form>
  );
};

export default JoinProject;