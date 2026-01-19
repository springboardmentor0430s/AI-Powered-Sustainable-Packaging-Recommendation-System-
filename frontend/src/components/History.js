import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:5000';

export default function History({ user }) {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchHistory();
  }, [user]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/history/${user.id}`);
      
      if (response.data.success) {
        setPredictions(response.data.predictions);
      } else {
        setError('Failed to load history');
      }
    } catch (err) {
      console.error('History error:', err);
      setError('Failed to load prediction history');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '36px', fontWeight: 'bold', color: 'white' }}>
          📜 Prediction History
        </h1>
        <button
          onClick={fetchHistory}
          style={{
            background: 'white',
            color: '#10b981',
            border: 'none',
            padding: '0.75rem 1.5rem',
            borderRadius: '12px',
            fontSize: '16px',
            fontWeight: '600',
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
          }}
        >
          🔄 Refresh
        </button>
      </div>

      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '2rem',
        boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
      }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
            <div style={{ fontSize: '48px', marginBottom: '1rem' }}>⏳</div>
            <p>Loading history...</p>
          </div>
        ) : error ? (
          <div style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#dc2626',
            padding: '1rem',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            {error}
          </div>
        ) : predictions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
            <div style={{ fontSize: '64px', marginBottom: '1rem' }}>📭</div>
            <p style={{ fontSize: '18px' }}>No predictions yet</p>
            <p style={{ fontSize: '14px' }}>Make your first prediction to see it here!</p>
          </div>
        ) : (
          <>
            <div style={{ marginBottom: '1rem', color: '#6b7280' }}>
              Total Predictions: <strong>{predictions.length}</strong>
            </div>
            
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                    <th style={thStyle}>Date</th>
                    <th style={thStyle}>Strength (MPa)</th>
                    <th style={thStyle}>Weight (kg)</th>
                    <th style={thStyle}>Bio %</th>
                    <th style={thStyle}>Recycle %</th>
                    <th style={thStyle}>CO₂ (g)</th>
                    <th style={thStyle}>Cost (₹)</th>
                    <th style={thStyle}>Material</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.map((pred) => (
                    <tr key={pred.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                      <td style={tdStyle}>{formatDate(pred.created_at)}</td>
                      <td style={tdStyle}>{pred.strength_mpa}</td>
                      <td style={tdStyle}>{pred.weight_capacity_kg}</td>
                      <td style={tdStyle}>{pred.biodegradability_pct}%</td>
                      <td style={tdStyle}>{pred.recyclability_pct}%</td>
                      <td style={{...tdStyle, fontWeight: 'bold', color: '#15803d'}}>
                        {pred.predicted_co2.toFixed(2)}
                      </td>
                      <td style={{...tdStyle, fontWeight: 'bold', color: '#92400e'}}>
                        ₹{pred.predicted_cost.toFixed(2)}
                      </td>
                      <td style={{...tdStyle, fontWeight: '600', color: '#6366f1'}}>
                        {pred.recommended_material}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Summary Stats */}
            <div style={{
              marginTop: '2rem',
              padding: '1.5rem',
              background: '#f9fafb',
              borderRadius: '12px',
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '1rem'
            }}>
              <StatCard
                label="Avg CO₂ Emission"
                value={`${(predictions.reduce((sum, p) => sum + p.predicted_co2, 0) / predictions.length).toFixed(2)}g`}
                color="#15803d"
              />
              <StatCard
                label="Avg Cost"
                value={`₹${(predictions.reduce((sum, p) => sum + p.predicted_cost, 0) / predictions.length).toFixed(2)}`}
                color="#92400e"
              />
              <StatCard
                label="Most Used Material"
                value={getMostFrequentMaterial(predictions)}
                color="#6366f1"
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '0.5rem' }}>
        {label}
      </div>
      <div style={{ fontSize: '20px', fontWeight: 'bold', color }}>
        {value}
      </div>
    </div>
  );
}

function getMostFrequentMaterial(predictions) {
  if (predictions.length === 0) return 'N/A';
  
  const counts = {};
  predictions.forEach(p => {
    counts[p.recommended_material] = (counts[p.recommended_material] || 0) + 1;
  });
  
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0];
}

const thStyle = {
  padding: '1rem',
  textAlign: 'left',
  fontSize: '14px',
  fontWeight: '600',
  color: '#374151'
};

const tdStyle = {
  padding: '1rem',
  fontSize: '14px',
  color: '#6b7280'
};