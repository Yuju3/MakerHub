import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/navbar';
import MyLoginPage from './pages/myLoginPage';
import MyRegistrationPage from './pages/myRegistrationPage';
import ForgotMyPassword from './pages/forgotMyPassword';
import MyUserPortal from './pages/myUserPortal';
import './App.css';

function App() {
  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<MyLoginPage />} />
          <Route path="/register" element={<MyRegistrationPage />} />
          <Route path="/forgot-password" element={<ForgotMyPassword />} />
          <Route path="/portal" element={<MyUserPortal />} />
        </Routes>
      </main>
      <footer className="footer">
        <p>&copy; {new Date().getFullYear()} MakerHub - The University of Texas at Austin</p>
      </footer>
    </div>
  );
}

export default App;

