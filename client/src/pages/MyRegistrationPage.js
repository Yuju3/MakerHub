import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const MyRegistrationPage = () => {
  const [formData, setFormData] = useState({
    userId: '',
    username: '',
    password: '',
    confirmPassword: ''
  });
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({...formData, [e.target.id]: e.target.value});
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      alert("Passwords do not match");
      return;
    }
    try {
      const response = await fetch('http://127.0.0.1:5000/add_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: formData.username,
          userId: formData.userId,
          password: formData.password
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Registration failed');
      alert("Account created successfully!");
      navigate('/login');
    } catch (error) {
      alert(error.message);
    }
  };

  return (
    <div className="auth-container">
      <div className="card auth-card">
        <h2>Create an Account</h2>
        <form className="auth-form" onSubmit={handleRegister}>
          <div className="form-group">
            <label className="form-label" htmlFor="userId">User ID</label>
            <input type="text" id="userId" className="form-control" onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="username">Username (UT EID)</label>
            <input type="text" id="username" className="form-control" onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input type="password" id="password" className="form-control" onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="confirmPassword">Confirm Password</label>
            <input type="password" id="confirmPassword" className="form-control" onChange={handleChange} required />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem' }}>
            Register
          </button>
        </form>
        <div className="auth-links">
          <span>Already have an account? <Link to="/login">Sign in here</Link></span>
        </div>
      </div>
    </div>
  );
};

export default MyRegistrationPage;

