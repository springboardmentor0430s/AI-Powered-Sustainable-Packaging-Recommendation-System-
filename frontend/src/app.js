import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import Landing from './components/Landing';
import Login from './components/Login';
import Predictor from './components/predictor';
import History from './components/History';
import Dashboard from './components/Dashboard';

const GOOGLE_CLIENT_ID = "17542443360-tk7esbse466phnfg781kcuks9roj973o.apps.googleusercontent.com"; // Replace with your actual Google Client ID

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in (stored in localStorage)
    const storedUser = localStorage.getItem('ecopack_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('ecopack_user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('ecopack_user');
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div style={{ fontSize: '24px', color: 'white' }}>Loading...</div>
      </div>
    );
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <Router>
        <div style={{ minHeight: '100vh' }}>
          {/* Navigation Bar */}
          {user && (
            <nav style={{
              background: 'rgba(255, 255, 255, 0.95)',
              padding: '1rem 2rem',
              boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
                <Link to="/" style={{
                  fontSize: '24px',
                  fontWeight: 'bold',
                  color: '#10b981',
                  textDecoration: 'none'
                }}>
                  🌿 EcoPackAI
                </Link>
                <Link to="/predictor" style={navLinkStyle}>Predictor</Link>
                <Link to="/history" style={navLinkStyle}>History</Link>
                <Link to="/dashboard" style={navLinkStyle}>Dashboard</Link>
              </div>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <span style={{ color: '#666' }}>{user.name || user.email}</span>
                <button onClick={handleLogout} style={{
                  background: '#ef4444',
                  color: 'white',
                  border: 'none',
                  padding: '0.5rem 1rem',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}>
                  Logout
                </button>
              </div>
            </nav>
          )}

          {/* Routes */}
          <Routes>
            <Route path="/" element={user ? <Navigate to="/predictor" /> : <Landing />} />
            <Route path="/login" element={user ? <Navigate to="/predictor" /> : <Login onLogin={handleLogin} />} />
            <Route path="/predictor" element={user ? <Predictor user={user} /> : <Navigate to="/login" />} />
            <Route path="/history" element={user ? <History user={user} /> : <Navigate to="/login" />} />
            <Route path="/dashboard" element={user ? <Dashboard user={user} /> : <Navigate to="/login" />} />
          </Routes>
        </div>
      </Router>
    </GoogleOAuthProvider>
  );
}

const navLinkStyle = {
  color: '#374151',
  textDecoration: 'none',
  fontWeight: '500',
  fontSize: '16px',
  transition: 'color 0.2s'
};

export default App;