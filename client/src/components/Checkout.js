import React, { useCallback, useEffect, useState } from 'react';
import { Cpu, Server, CheckCircle, XCircle } from 'lucide-react';
import Collaborators from './Collaborators';
import ErrorCard from './ErrorCard';
import { apiRequest } from '../api';

// The backend's messages start lowercase with no period ("checked out 5 units of HWSet1").
const asSentence = (text) => {
  const sentence = `${text.charAt(0).toUpperCase()}${text.slice(1)}`;
  return /[.!?]$/.test(sentence) ? sentence : `${sentence}.`;
};

const ACTIONS = {
  checkout: { route: '/check_out', label: 'Check Out', busy: 'Checking out…', failed: 'Check-out failed' },
  checkin: { route: '/check_in', label: 'Check In', busy: 'Checking in…', failed: 'Check-in failed' },
};

const Checkout = ({ project, currentUserId }) => {
  const [hardwareSets, setHardwareSets] = useState([]);
  const [usage, setUsage] = useState({});           // hwName -> units this project holds
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [requestQtys, setRequestQtys] = useState({}); // hwName -> text in the quantity box
  const [pending, setPending] = useState(null);       // { hwName, action } while a request runs
  const [feedback, setFeedback] = useState({});       // hwName -> { type, title, text }

  // Every set's capacity and availability, plus what this project holds.
  const loadStatus = useCallback(async () => {
    const [sets, projectInfo] = await Promise.all([
      apiRequest('/get_all_hw'),
      apiRequest(`/get_project_info/${encodeURIComponent(project.projectId)}`),
    ]);
    setHardwareSets(sets);
    setUsage(projectInfo.hwUsage || {});
  }, [project.projectId]);

  const reload = useCallback(() => {
    setLoading(true);
    setLoadError('');
    loadStatus()
      .catch((error) => setLoadError(error.message))
      .finally(() => setLoading(false));
  }, [loadStatus]);

  useEffect(reload, [reload]);

  const showFeedback = (hwName, value) => setFeedback((prev) => ({ ...prev, [hwName]: value }));

  const handleAction = async (hwName, action) => {
    const quantity = Number(requestQtys[hwName]);
    if (!Number.isInteger(quantity) || quantity <= 0) {
      showFeedback(hwName, {
        type: 'error',
        title: ACTIONS[action].failed,
        text: 'Enter a whole number of units greater than 0.',
      });
      return;
    }

    setPending({ hwName, action });
    showFeedback(hwName, null);
    try {
      const result = await apiRequest(ACTIONS[action].route, {
        method: 'POST',
        body: { projectId: project.projectId, hwName, quantity, userId: currentUserId },
      });
      // Show the numbers the backend just returned right away...
      setHardwareSets((prev) => prev.map((hw) => (hw.hwName === hwName ? result.hardware : hw)));
      setUsage((prev) => ({ ...prev, [hwName]: result.projectUsage }));
      setRequestQtys((prev) => ({ ...prev, [hwName]: '' }));
      showFeedback(hwName, { type: 'success', text: asSentence(result.message) });
      // ...then pick up anything other users changed since this page loaded.
      loadStatus().catch(() => {});
    } catch (error) {
      showFeedback(hwName, { type: 'error', title: ACTIONS[action].failed, text: asSentence(error.message) });
    } finally {
      setPending(null);
    }
  };

  const renderHardware = () => {
    if (loading) {
      return <p role="status">Loading hardware…</p>;
    }
    if (loadError) {
      return (
        <ErrorCard title="Couldn't load hardware" message={asSentence(loadError)}>
          <button type="button" className="btn btn-secondary" style={{ marginTop: '0.75rem' }} onClick={reload}>
            Try again
          </button>
        </ErrorCard>
      );
    }
    if (hardwareSets.length === 0) {
      return <p>No hardware sets exist yet.</p>;
    }

    return (
      <div className="dashboard-grid" style={{ marginTop: '1rem' }}>
        {hardwareSets.map((hw, index) => {
          const held = usage[hw.hwName] || 0;
          const busy = pending?.hwName === hw.hwName;
          const message = feedback[hw.hwName];
          const inputId = `qty-${hw.hwName}`;

          return (
            <div key={hw.hwName} style={{ border: '1px solid var(--ut-dark-gray)', borderRadius: '8px', padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                {index % 2 === 0 ? <Cpu size={24} color="var(--ut-charcoal)" /> : <Server size={24} color="var(--ut-charcoal)" />}
                <h4 style={{ margin: 0 }}>{hw.hwName}</h4>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                <span>Capacity: {hw.capacity}</span>
                <span style={{ fontWeight: 600, color: hw.availability > 0 ? 'var(--success-green)' : 'var(--error-red)' }}>
                  Available: {hw.availability}
                </span>
              </div>
              <div style={{ marginBottom: '1.5rem', fontSize: '0.9rem', color: 'var(--ut-burnt-orange)', fontWeight: 600 }}>
                Checked out by this project: {held}
              </div>

              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label className="form-label" htmlFor={inputId}>Quantity</label>
                <input
                  id={inputId}
                  type="number"
                  min="1"
                  step="1"
                  className="form-control"
                  value={requestQtys[hw.hwName] ?? ''}
                  onChange={(e) => setRequestQtys((prev) => ({ ...prev, [hw.hwName]: e.target.value }))}
                  placeholder="Enter amount"
                  disabled={busy}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className="btn btn-primary"
                  style={{ flex: 1, display: 'flex', gap: '0.25rem', padding: '0.5rem' }}
                  onClick={() => handleAction(hw.hwName, 'checkout')}
                  disabled={busy || hw.availability === 0}
                  title={hw.availability === 0 ? 'None available right now' : undefined}
                >
                  <CheckCircle size={16} />
                  {busy && pending.action === 'checkout' ? ACTIONS.checkout.busy : ACTIONS.checkout.label}
                </button>
                <button
                  className="btn btn-secondary"
                  style={{ flex: 1, display: 'flex', gap: '0.25rem', padding: '0.5rem' }}
                  onClick={() => handleAction(hw.hwName, 'checkin')}
                  disabled={busy || held === 0}
                  title={held === 0 ? 'This project has none checked out' : undefined}
                >
                  <XCircle size={16} />
                  {busy && pending.action === 'checkin' ? ACTIONS.checkin.busy : ACTIONS.checkin.label}
                </button>
              </div>

              {message?.type === 'success' && (
                <p className="hw-feedback" role="status">{message.text}</p>
              )}
              {message?.type === 'error' && (
                <div className="hw-error">
                  <ErrorCard title={message.title} message={message.text} onDismiss={() => showFeedback(hw.hwName, null)} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="card">
      <div style={{ borderBottom: '2px solid var(--ut-light-gray)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <h2 style={{ color: 'var(--ut-burnt-orange)' }}>{project.name}</h2>
        <p style={{ margin: '0 0 1rem' }}>Project ID: {project.projectId}</p>
        <div style={{ marginTop: '0.75rem' }}>
          <Collaborators project={project} currentUserId={currentUserId} />
        </div>
      </div>

      <h3>Hardware Resources</h3>
      {renderHardware()}
    </div>
  );
};

export default Checkout;
