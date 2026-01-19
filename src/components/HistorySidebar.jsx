import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { X, Clock, ChevronRight } from 'lucide-react';

export default function HistorySidebar({ isOpen, onClose, onSelect }) {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchHistory();
        }
    }, [isOpen]);

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("token");
            // Assuming backend is at localhost:5000
            const res = await axios.get("http://localhost:5000/history", {
                headers: { Authorization: `Bearer ${token}` }
            });
            setHistory(res.data);
        } catch (err) {
            console.error("Failed to fetch history", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            {/* Backdrop */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity"
                    onClick={onClose}
                />
            )}

            {/* Sidebar */}
            <div className={`fixed inset-y-0 right-0 w-96 bg-gray-900/95 backdrop-blur-xl border-l border-white/10 transform transition-transform duration-300 ease-in-out z-50 ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>

                {/* Header */}
                <div className="p-6 border-b border-white/10 flex justify-between items-center bg-gray-900/50">
                    <div className="flex items-center gap-3">
                        <Clock className="w-5 h-5 text-green-400" />
                        <h2 className="text-xl font-bold text-white">Prediction History</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/10 rounded-full text-gray-400 hover:text-white transition"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="overflow-y-auto h-[calc(100vh-80px)] p-6 space-y-4">
                    {loading ? (
                        <div className="text-center text-gray-400 mt-10">Loading history...</div>
                    ) : history.length === 0 ? (
                        <div className="text-center text-gray-500 mt-10">No history found.</div>
                    ) : (
                        history.map((item) => (
                            <div
                                key={item.id}
                                className="group bg-white/5 border border-white/5 p-4 rounded-xl cursor-pointer hover:bg-white/10 hover:border-green-500/30 transition-all duration-200"
                                onClick={() => {
                                    // Optionally pass item back to dashboard to 'replay' it
                                    // Note: 'item' has database structure, might need mapping if Dashboard expects 'results' format
                                    onSelect && onSelect(item);
                                }}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <h4 className="font-bold text-lg text-white group-hover:text-green-400 transition-colors">
                                        {item.product_name}
                                    </h4>
                                    <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-green-400" />
                                </div>

                                <div className="flex items-center gap-2 mb-3">
                                    <span className="text-xs font-medium px-2 py-1 rounded bg-green-500/20 text-green-400 border border-green-500/20">
                                        {item.recommended_material}
                                    </span>
                                </div>

                                <div className="grid grid-cols-2 gap-2 text-sm">
                                    <div className="flex flex-col">
                                        <span className="text-gray-500 text-xs">Cost</span>
                                        <span className="text-gray-300 font-mono">₹{item.predicted_cost}</span>
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-gray-500 text-xs">CO₂ Emissions</span>
                                        <span className="text-gray-300 font-mono">{item.predicted_co2} kg</span>
                                    </div>
                                </div>

                                <div className="mt-3 pt-3 border-t border-white/5 flex justify-between items-center text-xs text-gray-500">
                                    <span>{new Date(item.created_at).toLocaleDateString()}</span>
                                    <span>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </>
    );
}
