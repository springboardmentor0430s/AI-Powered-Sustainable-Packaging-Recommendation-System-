import { useState } from "react";
import { Leaf, Zap, DollarSign, Recycle, Loader2, RotateCcw, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/hooks/useAuth";
import { supabase } from "@/integrations/supabase/client";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from "recharts";

interface PredictionResult {
  material_name: string;
  co2_emission_score: number;
  cost_score: number;
  sustainability_score: number;
}

export default function Home() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  
  const [tensileStrength, setTensileStrength] = useState<string>("");
  const [weightCapacity, setWeightCapacity] = useState<string>("");
  const [biodegradabilityScore, setBiodegradabilityScore] = useState<number[]>([50]);
  const [recyclabilityPercent, setRecyclabilityPercent] = useState<number[]>([50]);

  const handlePredict = async () => {
    if (!tensileStrength || !weightCapacity) {
      toast({
        variant: "destructive",
        title: "Missing inputs",
        description: "Please fill in all required fields.",
      });
      return;
    }

    setIsLoading(true);

    try {
      // Call the ML prediction edge function
      const { data, error } = await supabase.functions.invoke("predict", {
        body: {
          tensile_strength: parseFloat(tensileStrength),
          weight_capacity: parseFloat(weightCapacity),
          biodegradability_score: biodegradabilityScore[0],
          recyclability_percent: recyclabilityPercent[0],
        },
      });

      if (error) {
        throw new Error(error.message);
      }

      if (data.error) {
        throw new Error(data.error);
      }

      const prediction: PredictionResult = {
        material_name: data.material_name,
        co2_emission_score: data.co2_emission_score,
        cost_score: data.cost_score,
        sustainability_score: data.sustainability_score,
      };

      setResult(prediction);

      // Save to database
      if (user) {
        const { error: dbError } = await supabase.from("predictions").insert({
          user_id: user.id,
          tensile_strength: parseFloat(tensileStrength),
          weight_capacity: parseFloat(weightCapacity),
          biodegradability_score: biodegradabilityScore[0],
          recyclability_percent: recyclabilityPercent[0],
          ...prediction,
        });

        if (dbError) {
          console.error("Error saving prediction:", dbError);
        }
      }

      toast({
        title: "Prediction complete!",
        description: `Recommended material: ${prediction.material_name}`,
      });
    } catch (error) {
      console.error("Prediction error:", error);
      toast({
        variant: "destructive",
        title: "Prediction failed",
        description: error instanceof Error ? error.message : "Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setTensileStrength("");
    setWeightCapacity("");
    setBiodegradabilityScore([50]);
    setRecyclabilityPercent([50]);
    setResult(null);
  };

  const pieData = result ? [
    { name: "CO₂ Score", value: result.co2_emission_score, color: "hsl(var(--primary))" },
    { name: "Cost Score", value: result.cost_score, color: "hsl(var(--accent))" },
  ] : [];

  const barData = result ? [
    { name: "CO₂", value: result.co2_emission_score },
    { name: "Cost", value: result.cost_score },
    { name: "Sustainability", value: result.sustainability_score },
  ] : [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-display font-bold">AI Material Recommendation</h2>
        <p className="text-muted-foreground mt-1">
          Enter your packaging requirements for AI-powered sustainable material suggestions.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <Card className="eco-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Leaf className="h-5 w-5 text-primary" />
              Input Parameters
            </CardTitle>
            <CardDescription>
              Provide your packaging specifications
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="tensile">Tensile Strength (MPa)</Label>
                <div className="relative">
                  <Zap className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="tensile"
                    type="number"
                    placeholder="e.g., 25"
                    className="pl-10"
                    value={tensileStrength}
                    onChange={(e) => setTensileStrength(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="weight">Weight Capacity (kg)</Label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="weight"
                    type="number"
                    placeholder="e.g., 10"
                    className="pl-10"
                    value={weightCapacity}
                    onChange={(e) => setWeightCapacity(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Biodegradability Score</Label>
                  <span className="text-sm font-medium text-primary">{biodegradabilityScore[0]}%</span>
                </div>
                <Slider
                  value={biodegradabilityScore}
                  onValueChange={setBiodegradabilityScore}
                  max={100}
                  step={1}
                  className="w-full"
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Recyclability Percent</Label>
                  <span className="text-sm font-medium text-primary">{recyclabilityPercent[0]}%</span>
                </div>
                <Slider
                  value={recyclabilityPercent}
                  onValueChange={setRecyclabilityPercent}
                  max={100}
                  step={1}
                  className="w-full"
                />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <Button onClick={handlePredict} className="flex-1 gradient-eco" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Recycle className="mr-2 h-4 w-4" />
                    Get AI Recommendation
                  </>
                )}
              </Button>
              <Button variant="outline" onClick={handleClear}>
                <RotateCcw className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <Card className={`eco-shadow transition-all duration-500 ${result ? "opacity-100" : "opacity-50"}`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-accent" />
              Prediction Results
            </CardTitle>
            <CardDescription>
              {result ? "AI-recommended sustainable packaging" : "Results will appear here"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-6 animate-scale-in">
                {/* Material recommendation */}
                <div className="p-4 rounded-xl bg-primary/10 border border-primary/20">
                  <p className="text-sm text-muted-foreground mb-1">Recommended Material</p>
                  <p className="text-xl font-display font-bold text-primary">{result.material_name}</p>
                </div>

                {/* Score cards */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <p className="text-2xl font-bold text-primary">{result.co2_emission_score}</p>
                    <p className="text-xs text-muted-foreground">CO₂ Score</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <p className="text-2xl font-bold text-accent">{result.cost_score}</p>
                    <p className="text-xs text-muted-foreground">Cost Score</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <p className="text-2xl font-bold text-success">{result.sustainability_score}</p>
                    <p className="text-xs text-muted-foreground">Sustainability</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-muted-foreground">
                <p>Enter parameters and click "Get AI Recommendation"</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      {result && (
        <div className="grid lg:grid-cols-2 gap-6 animate-fade-in" style={{ animationDelay: "0.2s" }}>
          <Card className="eco-shadow">
            <CardHeader>
              <CardTitle>Score Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="eco-shadow">
            <CardHeader>
              <CardTitle>Score Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={barData}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
