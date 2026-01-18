import { Leaf, Target, Heart, Award, TrendingUp, MapPin } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { supabase } from "@/integrations/supabase/client";
import { useQuery } from "@tanstack/react-query";
import logoEcoWrap from "@/assets/logo-eco-wrap-systems.png";
import logoEnviroX from "@/assets/logo-envirox.png";
import logoEarthKind from "@/assets/logo-earth-kind.png";
import WashingtonMap from "@/components/WashingtonMap";

const partners = [
  { name: "Eco Wrap Systems", description: "Sustainable packaging solutions", logo: logoEcoWrap },
  { name: "EnviroX", description: "Green technology innovators", logo: logoEnviroX },
  { name: "Earth Kind", description: "Eco-friendly materials partner", logo: logoEarthKind },
];

const values = [
  {
    icon: Leaf,
    title: "Sustainability First",
    description: "Every recommendation prioritizes environmental impact reduction.",
  },
  {
    icon: Target,
    title: "Precision AI",
    description: "Advanced machine learning for accurate material predictions.",
  },
  {
    icon: Heart,
    title: "Customer Focus",
    description: "Designed around your unique packaging needs.",
  },
];

export default function About() {
  const { user } = useAuth();

  const { data: stats } = useQuery({
    queryKey: ["user-stats", user?.id],
    queryFn: async () => {
      if (!user) return null;
      
      const { data, error } = await supabase
        .from("predictions")
        .select("sustainability_score, co2_emission_score")
        .eq("user_id", user.id);

      if (error) throw error;

      const totalPredictions = data?.length || 0;
      const avgSustainability = data?.length
        ? Math.round(data.reduce((acc, p) => acc + Number(p.sustainability_score), 0) / data.length)
        : 0;
      const totalCO2Saved = data?.length
        ? Math.round(data.reduce((acc, p) => acc + (100 - Number(p.co2_emission_score)), 0))
        : 0;

      return { totalPredictions, avgSustainability, totalCO2Saved };
    },
    enabled: !!user,
  });

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero section */}
      <div className="relative overflow-hidden rounded-2xl gradient-eco p-8 lg:p-12 text-primary-foreground">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJNMzYgMzRjMC0yLjIxLTEuNzktNC00LTRzLTQgMS43OS00IDQgMS43OSA0IDQgNCA0LTEuNzkgNC00eiIvPjwvZz48L2c+PC9zdmc+')] opacity-30" />
        <div className="relative z-10 max-w-2xl">
          <h1 className="text-3xl lg:text-4xl font-display font-bold mb-4">
            About EcoPackAI
          </h1>
          <p className="text-lg opacity-90 leading-relaxed">
            EcoPackAI is your intelligent partner in sustainable packaging decisions. 
            Our AI-powered platform analyzes your packaging requirements and recommends 
            eco-friendly materials that reduce environmental impact while maintaining 
            cost efficiency and product protection.
          </p>
        </div>
      </div>

      {/* Stats cards */}
      {stats && (
        <div className="grid sm:grid-cols-3 gap-4">
          <Card className="eco-shadow">
            <CardContent className="pt-6 text-center">
              <div className="w-12 h-12 rounded-xl gradient-eco flex items-center justify-center mx-auto mb-3">
                <Award className="h-6 w-6 text-primary-foreground" />
              </div>
              <p className="text-3xl font-bold text-primary">{stats.totalPredictions}</p>
              <p className="text-sm text-muted-foreground mt-1">Total Predictions</p>
            </CardContent>
          </Card>
          <Card className="eco-shadow">
            <CardContent className="pt-6 text-center">
              <div className="w-12 h-12 rounded-xl bg-accent flex items-center justify-center mx-auto mb-3">
                <TrendingUp className="h-6 w-6 text-accent-foreground" />
              </div>
              <p className="text-3xl font-bold text-accent">{stats.avgSustainability}%</p>
              <p className="text-sm text-muted-foreground mt-1">Avg. Sustainability</p>
            </CardContent>
          </Card>
          <Card className="eco-shadow">
            <CardContent className="pt-6 text-center">
              <div className="w-12 h-12 rounded-xl bg-success flex items-center justify-center mx-auto mb-3">
                <Leaf className="h-6 w-6 text-success-foreground" />
              </div>
              <p className="text-3xl font-bold text-success">{stats.totalCO2Saved}</p>
              <p className="text-sm text-muted-foreground mt-1">CO₂ Points Saved</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Our values */}
      <div>
        <h2 className="text-2xl font-display font-bold mb-6">Our Values</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {values.map((value, index) => (
            <Card 
              key={index} 
              className="eco-shadow hover:eco-shadow-lg transition-shadow duration-300"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <CardHeader>
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-2">
                  <value.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-lg">{value.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{value.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Partners */}
      <div>
        <h2 className="text-2xl font-display font-bold mb-6">Our Partners</h2>
        <div className="grid sm:grid-cols-3 gap-6">
          {partners.map((partner, index) => (
            <Card 
              key={index} 
              className="eco-shadow text-center hover:border-primary/50 transition-colors duration-300"
            >
              <CardContent className="pt-8 pb-6">
                <div className="w-20 h-20 rounded-2xl bg-background flex items-center justify-center mx-auto mb-4 overflow-hidden">
                  <img src={partner.logo} alt={partner.name} className="w-full h-full object-contain" />
                </div>
                <h3 className="text-xl font-display font-bold">{partner.name}</h3>
                <p className="text-sm text-muted-foreground mt-1">{partner.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Location Map */}
      <div>
        <h2 className="text-2xl font-display font-bold mb-6 flex items-center gap-2">
          <MapPin className="h-6 w-6 text-primary" />
          Our Location
        </h2>
        <WashingtonMap />
        <p className="text-sm text-muted-foreground mt-3 text-center">
          EcoPackAI Headquarters - Washington, DC
        </p>
      </div>

      {/* Mission */}
      <Card className="eco-shadow border-primary/20">
        <CardHeader>
          <CardTitle className="text-xl gradient-eco-text">Our Mission</CardTitle>
          <CardDescription>Making sustainable packaging accessible to all</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground leading-relaxed">
            At EcoPackAI, we believe that sustainability and business success go hand in hand. 
            Our mission is to empower businesses of all sizes to make informed, eco-conscious 
            packaging decisions through the power of artificial intelligence. By analyzing 
            your specific requirements—tensile strength, weight capacity, biodegradability, 
            and recyclability—we provide personalized recommendations that minimize environmental 
            impact while optimizing cost and performance. Together, we can build a greener future, 
            one package at a time.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
