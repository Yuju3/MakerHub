import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Wrench, Moon, Sun, UserCircle } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();
  const isAuthPage = ['/login', '/register', '/forgot-password'].includes(location.pathname);
  
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [currentUser, setCurrentUser] = useState(() => {
    const savedUser = localStorage.getItem('currentUser');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    const updateUser = () => {
      const savedUser = localStorage.getItem('currentUser');
      setCurrentUser(savedUser ? JSON.parse(savedUser) : null);
    };
    window.addEventListener('currentUserChanged', updateUser);
    return () => window.removeEventListener('currentUserChanged', updateUser);
  }, []);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const handleSignOut = () => {
    localStorage.removeItem('currentUser');
    setCurrentUser(null);
  };

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <Wrench size={24} color="#BF5700" />
        <div>Maker<span>Hub</span></div>
      </Link>
      
      <div className="navbar-nav">
        <button onClick={toggleTheme} className="btn btn-secondary" style={{ padding: '0.4rem', borderRadius: '50%' }} aria-label="Toggle Theme">
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>

        {!isAuthPage && (
          <>
            <Link to="/portal" className="nav-link">My Projects</Link>
            {currentUser && (
              <span className="current-user" title="Current user">
                <UserCircle size={20} />
                <span>{currentUser.username}</span>
              </span>
            )}
            <Link to="/login" className="btn btn-secondary" style={{ padding: '0.4rem 1rem' }} onClick={handleSignOut}>Sign Out</Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;

