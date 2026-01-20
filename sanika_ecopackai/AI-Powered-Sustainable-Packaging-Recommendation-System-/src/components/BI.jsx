import React, { useState, useEffect } from "react";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
import {
  TrendingUp, DollarSign, Activity, Package, Calendar, Download
} from "lucide-react";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";

const COLORS = ["#10B981", "#3B82F6", "#F59E0B", "#EF4444"];

export default function BI() {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState({
    totalPredictions: 0,
    avgCo2: 0,
    avgCost: 0,
    topMaterial: "N/A"
  });
  const [history, setHistory] = useState([]);
  const [co2Trend, setCo2Trend] = useState([]);
  const [costSummary, setCostSummary] = useState([]);
  const [materialFreq, setMaterialFreq] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem("token");
        const headers = { "Authorization": `Bearer ${token}` };

        // 1. Fetch Predictions (Summary + History)
        const predRes = await fetch("http://localhost:5000/api/predictions", { headers });
        const predictions = await predRes.json();

        // Calculate Summary Metrics
        if (predictions.length > 0) {
          const total = predictions.length;
          const avgCo2 = predictions.reduce((sum, p) => sum + p.predicted_co2, 0) / total;
          const avgCost = predictions.reduce((sum, p) => sum + p.predicted_cost, 0) / total;

          // Find Mode Material
          const matCounts = {};
          predictions.forEach(p => {
            matCounts[p.recommended_material] = (matCounts[p.recommended_material] || 0) + 1;
          });
          const topMaterial = Object.keys(matCounts).reduce((a, b) => matCounts[a] > matCounts[b] ? a : b);

          setMetrics({
            totalPredictions: total,
            avgCo2: avgCo2.toFixed(2),
            avgCost: avgCost.toFixed(2),
            topMaterial
          });
          setHistory(predictions.slice(0, 10)); // Top 10 recent
        }

        // 2. Fetch Analytics
        const [trendRes, costRes, matRes] = await Promise.all([
          fetch("http://localhost:5000/api/analytics/co2-trend", { headers }),
          fetch("http://localhost:5000/api/analytics/cost-summary", { headers }),
          fetch("http://localhost:5000/api/analytics/material-summary", { headers })
        ]);

        setCo2Trend(await trendRes.json());
        setCostSummary(await costRes.json());
        setMaterialFreq(await matRes.json());

      } catch (error) {
        console.error("Error loading BI data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleExportPDF = () => {
    const doc = new jsPDF();
    doc.text("Prediction History", 14, 22);
    autoTable(doc, {
      startY: 30,
      head: [['Date', 'Product', 'Material', 'Cost', 'CO2']],
      body: history.map(item => [
        new Date(item.created_at).toLocaleDateString(),
        item.product_name,
        item.recommended_material,
        item.predicted_cost,
        item.predicted_co2
      ]),
    });
    doc.save("PredictionHistory.pdf");
  };

  const handleExportExcel = () => {
    const worksheet = XLSX.utils.json_to_sheet(history.map(item => ({
      Date: new Date(item.created_at).toLocaleDateString(),
      Product: item.product_name,
      Material: item.recommended_material,
      Cost: item.predicted_cost,
      CO2: item.predicted_co2
    })));
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Predictions");
    XLSX.writeFile(workbook, "PredictionHistory.xlsx");
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6 sm:space-y-8 pb-20 font-sans">

      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Business Intelligence</h1>
        <p className="text-slate-500 mt-1 text-sm sm:text-base">Real-time insights on sustainability and costs.</p>
      </div>

      {/* 1. Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <SummaryCard
          title="Total Predictions"
          value={metrics.totalPredictions}
          icon={<Activity className="text-blue-600" />}
          bg="bg-blue-50"
          color="text-blue-700"
        />
        <SummaryCard
          title="Avg CO₂ Emissions"
          value={`${metrics.avgCo2} kg`}
          icon={<TrendingUp className="text-emerald-600" />}
          bg="bg-emerald-50"
          color="text-emerald-700"
        />
        <SummaryCard
          title="Avg Cost"
          value={`₹${metrics.avgCost}`}
          icon={<DollarSign className="text-amber-600" />}
          bg="bg-amber-50"
          color="text-amber-700"
        />
        <SummaryCard
          title="Top Material"
          value={metrics.topMaterial}
          icon={<Package className="text-purple-600" />}
          bg="bg-purple-50"
          color="text-purple-700"
        />
      </div>

      {/* 2. Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">

        {/* CO2 Trend */}
        <div className="bg-white p-4 sm:p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 className="text-lg font-bold text-slate-800 mb-6">CO₂ Emission Trends</h3>
          <div className="h-64 sm:h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={co2Trend}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#94A3B8" />
                <YAxis tick={{ fontSize: 12 }} stroke="#94A3B8" />
                <Tooltip
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Line type="monotone" dataKey="avg_co2" stroke="#10B981" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Material Frequency */}
        <div className="bg-white p-4 sm:p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 className="text-lg font-bold text-slate-800 mb-6">Material Distribution</h3>
          <div className="h-64 sm:h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={materialFreq}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="count"
                  nameKey="material"
                >
                  {materialFreq.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cost Analysis */}
        <div className="bg-white p-4 sm:p-6 rounded-2xl shadow-sm border border-slate-100 lg:col-span-2">
          <h3 className="text-lg font-bold text-slate-800 mb-6">Cost Analysis by Material</h3>
          <div className="h-64 sm:h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={costSummary} barSize={40}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="material" stroke="#94A3B8" tick={{ fontSize: 12 }} />
                <YAxis stroke="#94A3B8" tick={{ fontSize: 12 }} />
                <Tooltip cursor={{ fill: '#F1F5F9' }} />
                <Bar dataKey="avg_cost" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-4 sm:p-6 border-b border-slate-50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h3 className="text-lg font-bold text-slate-800">Recent Predictions</h3>
          <div className="flex gap-2 w-full sm:w-auto">
            <button
              onClick={handleExportExcel}
              className="flex-1 sm:flex-none justify-center items-center gap-2 px-3 py-2 bg-emerald-50 text-emerald-600 rounded-lg hover:bg-emerald-100 transition-colors text-sm font-medium"
            >
              <Download size={16} /> <span className="sm:hidden">Export</span> Excel
            </button>
            <button
              onClick={handleExportPDF}
              className="flex-1 sm:flex-none justify-center items-center gap-2 px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors text-sm font-medium"
            >
              <Download size={16} /> <span className="sm:hidden">Export</span> PDF
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[600px]">
            <thead>
              <tr className="bg-slate-50 text-slate-500 text-xs sm:text-sm uppercase tracking-wider">
                <th className="p-4 font-semibold">Date</th>
                <th className="p-4 font-semibold">Product</th>
                <th className="p-4 font-semibold">Material</th>
                <th className="p-4 font-semibold">Cost</th>
                <th className="p-4 font-semibold">CO₂</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {history.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50 transition-colors text-sm text-slate-700">
                  <td className="p-4 whitespace-nowrap text-slate-500">
                    {new Date(item.created_at).toLocaleDateString()}
                  </td>
                  <td className="p-4 font-medium text-slate-900">{item.product_name}</td>
                  <td className="p-4">
                    <span className="px-2 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-medium">
                      {item.recommended_material}
                    </span>
                  </td>
                  <td className="p-4 font-medium">₹{item.predicted_cost.toFixed(2)}</td>
                  <td className="p-4 text-emerald-600 font-medium">{item.predicted_co2.toFixed(2)} kg</td>
                </tr>
              ))}
            </tbody>
          </table>
          {history.length === 0 && (
            <div className="p-8 text-center text-slate-500">
              No prediction history found.
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

function SummaryCard({ title, value, icon, bg, color }) {
  return (
    <div className={`rounded-2xl p-6 border border-slate-100 bg-white hover:shadow-md transition-all`}>
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-xl ${bg}`}>
          {icon}
        </div>
        {/* <span className="text-xs font-bold text-green-500 bg-green-50 px-2 py-0.5 rounded-full">+4.5%</span> */}
      </div>
      <div className="space-y-1">
        <p className="text-slate-500 text-sm font-medium">{title}</p>
        <h3 className={`text-2xl font-bold ${color}`}>{value}</h3>
      </div>
    </div>
  );
}
