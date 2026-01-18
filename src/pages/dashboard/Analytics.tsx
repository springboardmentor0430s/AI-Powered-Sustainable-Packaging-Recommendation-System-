  import { useState } from "react";
  import { TrendingUp, TrendingDown, Leaf, DollarSign, BarChart3, Download, FileSpreadsheet } from "lucide-react";
  import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
  import { Button } from "@/components/ui/button";
  import { useAuth } from "@/hooks/useAuth";
  import { supabase } from "@/integrations/supabase/client";
  import { useQuery } from "@tanstack/react-query";
  import { useToast } from "@/hooks/use-toast";
  import {
    LineChart,
    Line,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    AreaChart,
    Area,
  } from "recharts";
  import { format } from "date-fns";

  export default function Analytics() {
    const { user } = useAuth();
    const { toast } = useToast();
    const [exporting, setExporting] = useState<string | null>(null);

    const { data: predictions } = useQuery({
      queryKey: ["predictions-analytics", user?.id],
      queryFn: async () => {
        if (!user) return [];
        
        const { data, error } = await supabase
          .from("predictions")
          .select("*")
          .eq("user_id", user.id)
          .order("created_at", { ascending: true });

        if (error) throw error;
        return data || [];
      },
      enabled: !!user,
    });

    const stats = predictions ? {
      totalPredictions: predictions.length,
      avgCO2: predictions.length 
        ? Math.round(predictions.reduce((acc, p) => acc + Number(p.co2_emission_score), 0) / predictions.length) 
        : 0,
      avgCost: predictions.length 
        ? Math.round(predictions.reduce((acc, p) => acc + Number(p.cost_score), 0) / predictions.length) 
        : 0,
      avgSustainability: predictions.length 
        ? Math.round(predictions.reduce((acc, p) => acc + Number(p.sustainability_score), 0) / predictions.length) 
        : 0,
      co2Reduction: 100 - (predictions.length 
        ? Math.round(predictions.reduce((acc, p) => acc + Number(p.co2_emission_score), 0) / predictions.length)
        : 0),
      costSavings: Math.round((predictions?.length || 0) * 12.5),
    } : null;

    const chartData = predictions?.slice(-10).map((p, index) => ({
      name: `#${index + 1}`,
      date: format(new Date(p.created_at), "MMM d"),
      co2: Number(p.co2_emission_score),
      cost: Number(p.cost_score),
      sustainability: Number(p.sustainability_score),
    })) || [];

    const materialCounts = predictions?.reduce((acc, p) => {
      acc[p.material_name] = (acc[p.material_name] || 0) + 1;
      return acc;
    }, {} as Record<string, number>) || {};

    const materialData = Object.entries(materialCounts).map(([name, count]) => ({
      name,
      count,
    }));

    const handleExportPDF = async () => {
      setExporting("pdf");
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      // Create simple PDF-like content
      const content = `
  EcoPackAI Analytics Report
  Generated: ${format(new Date(), "PPP")}

  SUMMARY
  -------
  Total Predictions: ${stats?.totalPredictions || 0}
  Average CO₂ Score: ${stats?.avgCO2 || 0}
  Average Cost Score: ${stats?.avgCost || 0}
  Average Sustainability: ${stats?.avgSustainability || 0}%
  CO₂ Reduction: ${stats?.co2Reduction || 0}%
  Estimated Savings: $${stats?.costSavings || 0}

  MATERIAL DISTRIBUTION
  ---------------------
  ${materialData.map((m) => `${m.name}: ${m.count} predictions`).join("\n")}
      `;

      const blob = new Blob([content], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ecopackai-report-${format(new Date(), "yyyy-MM-dd")}.txt`;
      a.click();
      URL.revokeObjectURL(url);

      toast({ title: "Report downloaded!", description: "Your analytics report has been saved." });
      setExporting(null);
    };

    const handleExportExcel = async () => {
      setExporting("excel");
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      // Create CSV content
      const headers = ["Date", "Material", "Tensile Strength", "Weight Capacity", "Biodegradability", "Recyclability", "CO2 Score", "Cost Score", "Sustainability"];
      const rows = predictions?.map((p) => [
        format(new Date(p.created_at), "yyyy-MM-dd"),
        p.material_name,
        p.tensile_strength,
        p.weight_capacity,
        p.biodegradability_score,
        p.recyclability_percent,
        p.co2_emission_score,
        p.cost_score,
        p.sustainability_score,
      ]) || [];

      const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ecopackai-data-${format(new Date(), "yyyy-MM-dd")}.csv`;
      a.click();
      URL.revokeObjectURL(url);

      toast({ title: "Data exported!", description: "Your data has been saved as CSV." });
      setExporting(null);
    };

    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-display font-bold">Business Dashboard</h2>
            <p className="text-muted-foreground mt-1">
              Analytics and insights from your packaging predictions
            </p>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={handleExportPDF}
              disabled={!!exporting}
            >
              {exporting === "pdf" ? (
                <div className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Export PDF
            </Button>
            <Button 
              variant="outline"
              onClick={handleExportExcel}
              disabled={!!exporting}
            >
              {exporting === "excel" ? (
                <div className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
              ) : (
                <FileSpreadsheet className="h-4 w-4 mr-2" />
              )}
              Export Excel
            </Button>
          </div>
        </div>

        {/* Stats cards */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="eco-shadow">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">CO₂ Reduction</p>
                  <p className="text-2xl font-bold">{stats?.co2Reduction || 0}%</p>
                </div>
                <div className="h-12 w-12 rounded-xl bg-success/10 flex items-center justify-center">
                  <TrendingDown className="h-6 w-6 text-success" />
                </div>
              </div>
              <p className="text-xs text-success mt-2 flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                vs. traditional materials
              </p>
            </CardContent>
          </Card>

          <Card className="eco-shadow">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Cost Savings</p>
                  <p className="text-2xl font-bold">${stats?.costSavings || 0}</p>
                </div>
                <div className="h-12 w-12 rounded-xl bg-accent/10 flex items-center justify-center">
                  <DollarSign className="h-6 w-6 text-accent" />
                </div>
              </div>
              <p className="text-xs text-accent mt-2">Estimated annual savings</p>
            </CardContent>
          </Card>

          <Card className="eco-shadow">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Predictions</p>
                  <p className="text-2xl font-bold">{stats?.totalPredictions || 0}</p>
                </div>
                <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                  <BarChart3 className="h-6 w-6 text-primary" />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">All-time analyses</p>
            </CardContent>
          </Card>

          <Card className="eco-shadow">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Avg. Sustainability</p>
                  <p className="text-2xl font-bold">{stats?.avgSustainability || 0}%</p>
                </div>
                <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Leaf className="h-6 w-6 text-primary" />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">Across all predictions</p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid lg:grid-cols-2 gap-6">
          <Card className="eco-shadow">
            <CardHeader>
              <CardTitle>Sustainability Trends</CardTitle>
              <CardDescription>Score progression over your last 10 predictions</CardDescription>
            </CardHeader>
            <CardContent>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorSustainability" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="sustainability"
                      stroke="hsl(var(--primary))"
                      fillOpacity={1}
                      fill="url(#colorSustainability)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  No data yet. Make some predictions to see trends.
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="eco-shadow">
            <CardHeader>
              <CardTitle>CO₂ vs Cost Comparison</CardTitle>
              <CardDescription>Balance between environmental and economic impact</CardDescription>
            </CardHeader>
            <CardContent>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="co2" name="CO₂ Score" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="cost" name="Cost Score" fill="hsl(var(--accent))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  No data yet. Make some predictions to see comparisons.
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Material distribution */}
        <Card className="eco-shadow">
          <CardHeader>
            <CardTitle>Top Recommended Materials</CardTitle>
            <CardDescription>Most frequently recommended sustainable materials</CardDescription>
          </CardHeader>
          <CardContent>
            {materialData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={materialData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={150} />
                  <Tooltip />
                  <Bar dataKey="count" name="Predictions" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                No material data yet. Make some predictions to see distribution.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }
