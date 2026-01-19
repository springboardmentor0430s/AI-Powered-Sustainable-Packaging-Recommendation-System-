import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';

const API_URL = 'http://localhost:5000';

export default function Login({ onLogin }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}
    >
      <div
        style={{
          background: 'white',
          borderRadius: '24px',
          padding: '3rem',
          maxWidth: '450px',
          width: '100%',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '64px', marginBottom: '1rem' }}>🌿</div>
          <h1
            style={{
              fontSize: '32px',
              fontWeight: 'bold',
              color: '#10b981',
              marginBottom: '0.5rem'
            }}
          >
            Welcome to EcoPackAI
          </h1>
          <p style={{ fontSize: '16px', color: '#6b7280' }}>
            Sign in to start making sustainable packaging decisions
          </p>
        </div>

        {/* Error Box */}
        {error && (
          <div
            style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#dc2626',
              padding: '1rem',
              borderRadius: '8px',
              marginBottom: '1rem',
              fontSize: '14px'
            }}
          >
            {error}
          </div>
        )}

        {/* Google Login */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <GoogleLogin
            onSuccess={async (credentialResponse) => {
              try {
                setLoading(true);
                setError('');

                console.log(
                  'GOOGLE ID TOKEN:',
                  credentialResponse.credential
                );

                const response = await axios.post(
                  `${API_URL}/api/auth/google`,
                  {
                    credential: credentialResponse.credential
                  },
                  {
                    headers: {
                      'Content-Type': 'application/json'
                    }
                  }
                );

                console.log('BACKEND LOGIN RESPONSE:', response.data);

                // Pass user data to parent (App.js)
                onLogin(response.data);
              } catch (err) {
                console.error('Login error:', err);
                setError('Login failed. Please try again.');
              } finally {
                setLoading(false);
              }
            }}
            onError={() => {
              setError('Google login failed. Please try again.');
            }}
          />
        </div>

        {/* Footer */}
        <div
          style={{
            marginTop: '2rem',
            padding: '1rem',
            background: '#f9fafb',
            borderRadius: '8px',
            fontSize: '13px',
            color: '#6b7280',
            textAlign: 'center'
          }}
        >
          🔒 Secure authentication powered by Google
        </div>

        {loading && (
          <p
            style={{
              marginTop: '1rem',
              textAlign: 'center',
              color: '#6b7280'
            }}
          >
            Signing in...
          </p>
        )}
      </div>
    </div>
  );
}
