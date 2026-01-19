import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Charts from "./Charts";
import HistorySidebar from "./HistorySidebar";
import { Clock } from "lucide-react";

export default function Dashboard() {
  const location = useLocation();
  const navigate = useNavigate();

  // Check for token in URL (from OAuth redirect)
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get("token");
    if (token) {
      localStorage.setItem("token", token);
      // Clean URL
      navigate("/dashboard", { replace: true });
    }
  }, [location, navigate]);

  const [formData, setFormData] = useState({
    productName: "Eco Bottle",
    productQuality: "High",
    countryTag: "India",
    strength: "50",
    units: "100",
    productQuantity: "1000",
    shape: "Bottle",
    // Hidden/Constants
    industry: "Food",
  });

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  // Handle selection from history
  const handleHistorySelect = (item) => {
    // Map history item format to results format if needed
    setResults({
      recommended_material: item.recommended_material,
      predicted_cost: item.predicted_cost,
      predicted_co2: item.predicted_co2,
      ai_recommendation: "Historical Data",
      top_3_alternatives: [] // or fetch/store alternatives if available in history (schema didn't have it)
    });
    // Try to re-populate form if possible, or just show results
    setFormData(prev => ({
      ...prev,
      productName: item.product_name,
      // other fields might be missing in history per current schema
    }));
    setShowHistory(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const payload = {
      Product_Name: formData.productName,
      Shape: formData.shape,
      Industry: formData.industry,
      Product_Quality: formData.productQuality,
      No_of_Units: formData.units,
      Product_Quantity: formData.productQuantity,
      Country_Tag: formData.countryTag,
      Strength: formData.strength,
    };

    try {
      const response = await fetch("http://localhost:5000/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify(payload),
      });

      if (response.status === 401) {
        alert("Session expired. Please log in again.");
        navigate("/login");
        return;
      }

      if (!response.ok) {
        throw new Error("Prediction failed");
      }

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Error fetching recommendations:", error);
      // alert("Prediction failed. Please ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      navigate("/login");
    }
  }, [navigate]);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6 sm:space-y-8 pb-20">

      {/* Form Section */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4 sm:p-6 lg:p-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 sm:mb-8 border-b border-slate-50 pb-4 gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-800">AI Packaging Analysis</h2>
              <p className="text-xs sm:text-sm text-slate-500">Optimize your product packaging with AI insights.</p>
            </div>
          </div>
          <button
            onClick={() => setShowHistory(true)}
            className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 transition-colors px-3 py-2 rounded-lg hover:bg-slate-50 w-full sm:w-auto justify-center"
          >
            <Clock size={20} />
            <span className="font-medium">History</span>
          </button>
        </div>

        <HistorySidebar
          isOpen={showHistory}
          onClose={() => setShowHistory(false)}
          onSelect={handleHistorySelect}
        />

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">

            {/* Product Name */}
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-slate-700">Product Name</label>
              <input type="text" name="productName" value={formData.productName} onChange={handleChange} className="w-full h-11 px-4 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition bg-slate-50 focus:bg-white" />
            </div>

            {/* Shape */}
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-slate-700">Shape</label>
              <input type="text" name="shape" value={formData.shape} onChange={handleChange} placeholder="e.g. Bottle, Box" className="w-full h-11 px-4 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition bg-slate-50 focus:bg-white" />
            </div>

            {/* Industry (Fixed) */}
            <div className="space-y-1.5 opacity-70">
              <label className="text-sm font-semibold text-slate-700">Industry</label>
              <input type="text" value="Food" disabled className="w-full h-11 px-4 rounded-xl border border-slate-200 bg-slate-100 text-slate-500 cursor-not-allowed" />
            </div>

            {/* Product Quality */}
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-slate-700">Product Quality</label>
              <div className="relative">
                <select name="productQuality" value={formData.productQuality} onChange={handleChange} className="w-full h-11 px-4 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition appearance-none">
                  <option>Low</option>
                  <option>Medium</option>
                  <option>High</option>
                  <option>Premium</option>
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                </div>
              </div>
            </div>

            {/* No of Units */}
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-slate-700">No. of Units</label>
              <input type="number" name="units" value={formData.units} onChange={handleChange} className="w-full h-11 px-4 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition bg-slate-50 focus:bg-white" />
            </div>

            {/* Product Quantity */}
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-slate-700">Product Quantity</label>
              <input type="number" name="productQuantity" value={formData.productQuantity} onChange={handleChange} className="w-full h-11 px-4 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition bg-slate-50 focus:bg-white" />
            </div>

            {/* Country Tag */}
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-slate-700">Country Tag</label>
              <input type="text" name="countryTag" value={formData.countryTag} onChange={handleChange} className="w-full h-11 px-4 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition bg-slate-50 focus:bg-white" />
            </div>

            {/* Strength */}
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-slate-700">Strength (MPa)</label>
              <input type="number" name="strength" value={formData.strength} onChange={handleChange} placeholder="e.g. 50" className="w-full h-11 px-4 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition bg-slate-50 focus:bg-white" />
            </div>

          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto min-w-[200px] h-12 px-6 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-md hover:shadow-lg hover:shadow-emerald-200 transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                  <span>Get Recommendations</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Results Section */}
      {results && (
        <div className="animate-fade-in-up space-y-6">

          {/* Top Recommendation (Replaces Current Analysis) */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              </div>
              <h3 className="text-xl font-bold text-slate-800">Review & Recommendation</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
              <div>
                <p className="text-slate-500 mb-2">Based on your input for <span className="font-bold text-slate-900">{formData.productName}</span>, our AI recommends:</p>
                <div className="text-4xl font-bold text-emerald-600 mb-2">{results.recommended_material}</div>
                <div className="inline-flex items-center px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-sm font-medium">
                  {results.ai_recommendation || "Highly Recommended"}
                </div>
              </div>

              <div className="space-y-4 border-l border-slate-100 pl-8">
                <div className="flex justify-between items-center">
                  <span className="text-slate-500 font-medium">Predicted Cost:</span>
                  <span className="text-slate-900 font-bold text-2xl">₹{results.predicted_cost}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-500 font-medium">Predicted CO₂:</span>
                  <span className="text-slate-900 font-bold text-2xl text-emerald-600">{results.predicted_co2} kg</span>
                </div>
              </div>
            </div>
          </div>

          {/* Visualization Charts */}
          {results.top_3_alternatives && results.top_3_alternatives.length > 0 && (
            <Charts data={results.top_3_alternatives} />
          )}

          {/* Recommendations List */}
          {results.top_3_alternatives && results.top_3_alternatives.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 mb-2">
                <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path></svg>
                <h3 className="text-lg font-bold text-slate-800">Top Alternatives</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {results.top_3_alternatives.map((item) => (
                  <div key={item.Rank} className="recommend-card bg-white p-6 rounded-xl shadow-sm border border-slate-100 hover:shadow-md transition-all">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-bold text-lg text-slate-800">#{item.Rank} {item.Material}</h3>
                      <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full">{item.AI_Recommendation}</span>
                    </div>
                    <div className="space-y-2">
                      <p className="flex justify-between text-sm"><span className="text-slate-500">Cost:</span> <span className="font-bold text-slate-900">₹{item.Predicted_Cost}</span></p>
                      <p className="flex justify-between text-sm"><span className="text-slate-500">CO₂:</span> <span className="font-bold text-emerald-600">{item.Predicted_CO2} kg</span></p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
