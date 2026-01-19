import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

const API_URL = 'http://localhost:5000';

const COLORS = ['#10b981', '#6366f1', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function Dashboard({ user }) {
  const [stats, setStats] = useState(null);
  const [materialDist, setMaterialDist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboard();
  }, [user]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/dashboard/${user.id}`);
      
      if (response.data.success) {
        setStats(response.data.stats);
        setMaterialDist(response.data.material_distribution);
      } else {
        setError('Failed to load dashboard');
      }
    } catch (err) {
      console.error('Dashboard error:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'white' }}>
        <div style={{ fontSize: '48px', marginBottom: '1rem' }}>⏳</div>
        <p style={{ fontSize: '18px' }}>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', maxWidth: '600px', margin: '0 auto' }}>
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '2rem',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '1rem' }}>⚠️</div>
          <p style={{ color: '#dc2626', fontSize: '18px' }}>{error}</p>
        </div>
      </div>
    );
  }

  const totalPredictions = stats?.total_predictions || 0;

  if (totalPredictions === 0) {
    return (
      <div style={{ padding: '2rem', maxWidth: '600px', margin: '0 auto' }}>
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '3rem',
          textAlign: 'center',
          boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '1rem' }}>📊</div>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#374151', marginBottom: '1rem' }}>
            No Data Yet
          </h2>
          <p style={{ color: '#6b7280', marginBottom: '2rem' }}>
            Make some predictions to see your sustainability dashboard!
          </p>
        </div>
      </div>
    );
  }

  const pieData = materialDist.map(item => ({
    name: item.recommended_material,
    value: parseInt(item.count)
  }));

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '36px', fontWeight: 'bold', color: 'white' }}>
          📊 Sustainability Dashboard
        </h1>
        <button
          onClick={fetchDashboard}
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

      {/* Key Metrics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        <MetricCard
          icon="📦"
          label="Total Predictions"
          value={totalPredictions}
          color="#6366f1"
        />
        <MetricCard
          icon="🌱"
          label="Avg CO₂ Emission"
          value={`${parseFloat(stats.avg_co2 || 0).toFixed(1)}g`}
          color="#10b981"
        />
        <MetricCard
          icon="💰"
          label="Avg Cost"
          value={`₹${parseFloat(stats.avg_cost || 0).toFixed(2)}`}
          color="#f59e0b"
        />
        <MetricCard
          icon="📉"
          label="Min CO₂"
          value={`${parseFloat(stats.min_co2 || 0).toFixed(1)}g`}
          color="#15803d"
        />
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Material Distribution */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#374151', marginBottom: '1.5rem' }}>
            Material Usage Distribution
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Material Count Bar Chart */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#374151', marginBottom: '1.5rem' }}>
            Material Recommendation Count
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={pieData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={12} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Environmental Impact Summary */}
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '2rem',
        boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
        marginTop: '2rem'
      }}>
        <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#374151', marginBottom: '1.5rem' }}>
          Environmental Impact Summary
        </h2>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1.5rem'
        }}>
          <ImpactCard
            title="CO₂ Range"
            value={`${parseFloat(stats.min_co2 || 0).toFixed(1)}g - ${parseFloat(stats.max_co2 || 0).toFixed(1)}g`}
            description="Your CO₂ emission predictions range"
            color="#10b981"
          />
          <ImpactCard
            title="Average Emission"
            value={`${parseFloat(stats.avg_co2 || 0).toFixed(2)}g`}
            description="Mean CO₂ across all predictions"
            color="#6366f1"
          />
          <ImpactCard
            title="Sustainability Score"
            value={`${Math.max(0, Math.min(100, 100 - parseFloat(stats.avg_co2 || 0))).toFixed(0)}%`}
            description="Based on average CO₂ emissions"
            color="#f59e0b"
          />
        </div>

        <div style={{
          marginTop: '2rem',
          padding: '1.5rem',
          background: '#f0fdf4',
          border: '2px solid #86efac',
          borderRadius: '12px'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: 'bold', color: '#15803d', marginBottom: '0.5rem' }}>
            🌍 Sustainability Insights
          </h3>
          <ul style={{ marginLeft: '1.5rem', color: '#166534', lineHeight: '1.8' }}>
            <li>You've made {totalPredictions} sustainable packaging decisions</li>
            <li>Your average CO₂ emission is {parseFloat(stats.avg_co2 || 0).toFixed(2)}g per package</li>
            <li>Most recommended material: {pieData.length > 0 ? pieData[0].name : 'N/A'}</li>
            <li>Keep using eco-friendly materials to reduce your carbon footprint!</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, color }) {
  return (
    <div style={{
      background: 'white',
      borderRadius: '16px',
      padding: '1.5rem',
      boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '40px', marginBottom: '0.5rem' }}>{icon}</div>
      <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '0.5rem' }}>
        {label}
      </div>
      <div style={{ fontSize: '28px', fontWeight: 'bold', color }}>
        {value}
      </div>
    </div>
  );
}

function ImpactCard({ title, value, description, color }) {
  return (
    <div style={{
      background: '#f9fafb',
      borderRadius: '12px',
      padding: '1.5rem',
      border: `2px solid ${color}20`
    }}>
      <h3 style={{ fontSize: '14px', fontWeight: '600', color, marginBottom: '0.5rem' }}>
        {title}
      </h3>
      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#374151', marginBottom: '0.5rem' }}>
        {value}
      </div>
      <p style={{ fontSize: '12px', color: '#6b7280' }}>
        {description}
      </p>
    </div>
  );
}