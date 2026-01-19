import React, { useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API_URL = 'http://localhost:5000';

export default function Predictor({ user }) {
  const [formData, setFormData] = useState({
    strength_mpa: '',
    weight_capacity_kg: '',
    biodegradability_pct: '',
    recyclability_pct: ''
  });
  
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_URL}/api/predict`, {
        ...formData,
        user_id: user.id
      });
      
      if (response.data.success) {
        setPredictions(response.data);
      } else {
        setError('Prediction failed. Please try again.');
      }
    } catch (err) {
      console.error('Prediction error:', err);
      setError('Failed to get predictions. Please check your inputs and try again.');
    } finally {
      setLoading(false);
    }
  };

  const chartData = predictions?.recommendations.map((rec, idx) => ({
    name: rec.material,
    score: (rec.score * 100).toFixed(1),
    co2: rec.co2,
    cost: rec.cost
  })) || [];

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '36px', fontWeight: 'bold', color: 'white', marginBottom: '2rem' }}>
        📦 Material Predictor
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Input Form */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
        }}>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#374151', marginBottom: '1.5rem' }}>
            Package Parameters
          </h2>

          {error && (
            <div style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#dc2626',
              padding: '1rem',
              borderRadius: '8px',
              marginBottom: '1rem',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={labelStyle}>Strength (MPa)</label>
              <input
                type="number"
                name="strength_mpa"
                value={formData.strength_mpa}
                onChange={handleChange}
                required
                min="0"
                step="0.1"
                style={inputStyle}
                placeholder="e.g., 50"
              />
              <p style={hintStyle}>Material tensile strength in megapascals</p>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={labelStyle}>Weight Capacity (kg)</label>
              <input
                type="number"
                name="weight_capacity_kg"
                value={formData.weight_capacity_kg}
                onChange={handleChange}
                required
                min="0"
                step="0.1"
                style={inputStyle}
                placeholder="e.g., 10"
              />
              <p style={hintStyle}>Maximum weight the package can hold</p>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={labelStyle}>Biodegradability (%)</label>
              <input
                type="number"
                name="biodegradability_pct"
                value={formData.biodegradability_pct}
                onChange={handleChange}
                required
                min="0"
                max="100"
                step="1"
                style={inputStyle}
                placeholder="e.g., 80"
              />
              <p style={hintStyle}>Percentage of material that is biodegradable</p>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={labelStyle}>Recyclability (%)</label>
              <input
                type="number"
                name="recyclability_pct"
                value={formData.recyclability_pct}
                onChange={handleChange}
                required
                min="0"
                max="100"
                step="1"
                style={inputStyle}
                placeholder="e.g., 90"
              />
              <p style={hintStyle}>Percentage of material that can be recycled</p>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                background: loading ? '#9ca3af' : '#10b981',
                color: 'white',
                border: 'none',
                padding: '1rem',
                borderRadius: '12px',
                fontSize: '18px',
                fontWeight: 'bold',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background 0.2s'
              }}
            >
              {loading ? 'Predicting...' : '🎯 Get Predictions'}
            </button>
          </form>
        </div>

        {/* Results */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
        }}>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#374151', marginBottom: '1.5rem' }}>
            Prediction Results
          </h2>

          {!predictions ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
              <div style={{ fontSize: '64px', marginBottom: '1rem' }}>📊</div>
              <p>Enter package parameters and click "Get Predictions" to see results</p>
            </div>
          ) : (
            <>
              {/* Metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
                <div style={{
                  background: '#f0fdf4',
                  border: '2px solid #86efac',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '14px', color: '#15803d', fontWeight: '600', marginBottom: '0.5rem' }}>
                    CO₂ Emission
                  </div>
                  <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#15803d' }}>
                    {predictions.predicted_co2}g
                  </div>
                </div>
                <div style={{
                  background: '#fef3c7',
                  border: '2px solid #fbbf24',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '14px', color: '#92400e', fontWeight: '600', marginBottom: '0.5rem' }}>
                    Estimated Cost
                  </div>
                  <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#92400e' }}>
                    ₹{predictions.predicted_cost}
                  </div>
                </div>
              </div>

              {/* Top Recommendation */}
              <div style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: '12px',
                padding: '1.5rem',
                color: 'white',
                marginBottom: '2rem'
              }}>
                <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '0.5rem' }}>
                  🏆 Recommended Material
                </div>
                <div style={{ fontSize: '28px', fontWeight: 'bold' }}>
                  {predictions.recommendations[0].material}
                </div>
                <div style={{ fontSize: '14px', opacity: 0.9, marginTop: '0.5rem' }}>
                  Match Score: {(predictions.recommendations[0].score * 100).toFixed(1)}%
                </div>
              </div>

              {/* Top 3 Chart */}
              <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#374151', marginBottom: '1rem' }}>
                Top 3 Materials Comparison
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={12} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="score" fill="#10b981" name="Match Score %" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

const labelStyle = {
  display: 'block',
  fontSize: '14px',
  fontWeight: '600',
  color: '#374151',
  marginBottom: '0.5rem'
};

const inputStyle = {
  width: '100%',
  padding: '0.75rem',
  fontSize: '16px',
  border: '2px solid #e5e7eb',
  borderRadius: '8px',
  outline: 'none',
  transition: 'border-color 0.2s'
};

const hintStyle = {
  fontSize: '12px',
  color: '#9ca3af',
  marginTop: '0.25rem'
};