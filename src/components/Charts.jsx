import React from "react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Legend,
    CartesianGrid
} from "recharts";

export default function Charts({ data }) {
    if (!data || data.length === 0) return null;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 my-8">
            {/* CO2 Emissions Chart */}
            <div className="bg-white/10 backdrop-blur-md p-6 rounded-2xl border border-white/20 shadow-xl">
                <h3 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
                    <span className="w-2 h-8 bg-green-500 rounded-full"></span>
                    CO₂ Emissions Comparison
                </h3>
                <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" vertical={false} />
                            <XAxis
                                dataKey="Material"
                                stroke="#9ca3af"
                                tick={{ fill: '#d1d5db', fontSize: 12 }}
                                tickLine={false}
                                axisLine={false}
                            />
                            <YAxis
                                stroke="#9ca3af"
                                tick={{ fill: '#d1d5db', fontSize: 12 }}
                                tickLine={false}
                                axisLine={false}
                            />
                            <Tooltip
                                cursor={{ fill: 'transparent' }}
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    borderColor: '#374151',
                                    borderRadius: '0.5rem',
                                    color: '#fff',
                                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                                }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Bar
                                dataKey="Predicted_CO2"
                                fill="#16a34a"
                                radius={[4, 4, 0, 0]}
                                name="CO₂ (kg)"
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Cost Comparison Chart */}
            <div className="bg-white/10 backdrop-blur-md p-6 rounded-2xl border border-white/20 shadow-xl">
                <h3 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
                    <span className="w-2 h-8 bg-blue-500 rounded-full"></span>
                    Cost Comparison
                </h3>
                <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" vertical={false} />
                            <XAxis
                                dataKey="Material"
                                stroke="#9ca3af"
                                tick={{ fill: '#d1d5db', fontSize: 12 }}
                                tickLine={false}
                                axisLine={false}
                            />
                            <YAxis
                                stroke="#9ca3af"
                                tick={{ fill: '#d1d5db', fontSize: 12 }}
                                tickLine={false}
                                axisLine={false}
                            />
                            <Tooltip
                                cursor={{ fill: 'transparent' }}
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    borderColor: '#374151',
                                    borderRadius: '0.5rem',
                                    color: '#fff',
                                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                                }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Bar
                                dataKey="Predicted_Cost"
                                fill="#3b82f6"
                                radius={[4, 4, 0, 0]}
                                name="Cost (₹)"
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
