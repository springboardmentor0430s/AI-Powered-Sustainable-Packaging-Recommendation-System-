import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      {/* Hero Section */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '24px',
        padding: '4rem',
        maxWidth: '900px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '64px', marginBottom: '1rem' }}>🌿</div>
        <h1 style={{
          fontSize: '48px',
          fontWeight: 'bold',
          color: '#10b981',
          marginBottom: '1rem'
        }}>
          EcoPackAI
        </h1>
        <p style={{
          fontSize: '24px',
          color: '#6b7280',
          marginBottom: '2rem'
        }}>
          AI-Powered Sustainable Packaging Solutions
        </p>

        {/* Features */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '2rem',
          margin: '3rem 0',
          textAlign: 'left'
        }}>
          <FeatureCard
            icon="🎯"
            title="Smart Predictions"
            description="ML models predict CO₂ emissions and costs with 99% accuracy"
          />
          <FeatureCard
            icon="♻️"
            title="Eco-Friendly"
            description="Get recommendations for sustainable packaging materials"
          />
          <FeatureCard
            icon="📊"
            title="Analytics"
            description="Track your environmental impact with detailed dashboards"
          />
        </div>

        {/* CTA Buttons */}
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '2rem' }}>
          <button
            onClick={() => navigate('/login')}
            style={{
              background: '#10b981',
              color: 'white',
              border: 'none',
              padding: '1rem 3rem',
              fontSize: '18px',
              borderRadius: '12px',
              cursor: 'pointer',
              fontWeight: 'bold',
              boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
              transition: 'transform 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.transform = 'scale(1.05)'}
            onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
          >
            Get Started →
          </button>
        </div>
      </div>

      {/* Info Section */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.9)',
        borderRadius: '16px',
        padding: '2rem',
        maxWidth: '900px',
        marginTop: '2rem',
        boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
      }}>
        <h2 style={{ fontSize: '28px', fontWeight: 'bold', color: '#374151', marginBottom: '1rem' }}>
          Why Choose EcoPackAI?
        </h2>
        <p style={{ fontSize: '16px', color: '#6b7280', lineHeight: '1.8' }}>
          Traditional packaging heavily relies on non-biodegradable materials, causing environmental damage 
          and financial inefficiency. EcoPackAI uses advanced machine learning to recommend optimal packaging 
          materials based on your product attributes, sustainability parameters, and industry standards. 
          Make data-driven decisions towards greener supply chains and reduce your carbon footprint today.
        </p>
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div style={{
      background: '#f9fafb',
      padding: '1.5rem',
      borderRadius: '12px',
      border: '2px solid #e5e7eb'
    }}>
      <div style={{ fontSize: '32px', marginBottom: '0.5rem' }}>{icon}</div>
      <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#374151', marginBottom: '0.5rem' }}>
        {title}
      </h3>
      <p style={{ fontSize: '14px', color: '#6b7280' }}>{description}</p>
    </div>
  );
}