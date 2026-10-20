import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ErrorCard from '../components/ErrorCard';

const MyLoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    fetch('http://127.0.0.1:5000/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (response.status === 401) {
          const err = new Error('invalid-credentials');
          err.kind = 'invalid-credentials';
          throw err;
        }
        if (!response.ok) throw new Error(data.error || 'Login failed');
        return data;
      })
      .then((user) => {
        localStorage.setItem('currentUser', JSON.stringify(user));
        window.dispatchEvent(new Event('currentUserChanged'));
        navigate('/portal');
      })
      .catch((err) => {
        if (err.kind === 'invalid-credentials') {
          setError({
            title: 'Invalid username or password',
            message: "We couldn't find an account matching those details. Check your spelling and try again.",
            showRegister: true
          });
        } else if (err instanceof TypeError) {
          setError({
            title: 'Cannot reach the server',
            message: 'Make sure the MakerHub backend is running, then try again.'
          });
        } else {
          setError({ title: 'Sign in failed', message: err.message });
        }
      })
      .finally(() => setLoading(false));
  };

  const clearError = () => setError(null);

  return (
    <div className="auth-container">
      <div className="card auth-card">
        <h2>Sign In to MakerHub</h2>
        {error && (
          <ErrorCard title={error.title} message={error.message} onDismiss={clearError}>
            {error.showRegister && (
              <p className="error-card-message" style={{ marginTop: '0.5rem' }}>
                New here? <Link to="/register">Create an account</Link>
              </p>
            )}
          </ErrorCard>
        )}
        <form className="auth-form" onSubmit={handleLogin}>
          <div className="form-group">
            <label className="form-label" htmlFor="username">Username (UT EID)</label>
            <input 
              type="text" 
              id="username" 
              className="form-control" 
              placeholder="Enter your username"
              value={username}
              onChange={(e) => { setUsername(e.target.value); clearError(); }}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input 
              type="password" 
              id="password" 
              className="form-control" 
              placeholder="Enter your password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); clearError(); }}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <div className="auth-links">
          <Link to="/forgot-password">Forgot your password?</Link>
          <span>Don't have an account? <Link to="/register">Create an account</Link></span>
        </div>
      </div>
    </div>
  );
};

export default MyLoginPage;