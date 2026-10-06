import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Wrench } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();
  const isAuthPage = ['/login', '/register', '/forgot-password'].includes(location.pathname);

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <Wrench size={24} color="#BF5700" />
        <div>Maker<span>Hub</span></div>
      </Link>
      
      {!isAuthPage && (
        <div className="navbar-nav">
          <Link to="/portal" className="nav-link">My Projects</Link>
          <Link to="/login" className="btn btn-secondary" style={{ padding: '0.4rem 1rem' }}>Sign Out</Link>
        </div>
      )}
    </nav>
  );
};

export default Navbar;

