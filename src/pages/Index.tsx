import { Link } from "react-router-dom";
import { Leaf, ArrowRight, Sparkles, Shield, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: Sparkles,
    title: "AI-Powered Analysis",
    description: "Advanced machine learning for accurate material predictions",
  },
  {
    icon: Shield,
    title: "Sustainability First",
    description: "Every recommendation prioritizes environmental impact",
  },
  {
    icon: BarChart3,
    title: "Business Intelligence",
    description: "Comprehensive analytics and reporting dashboards",
  },
];

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10 container mx-auto px-4 py-20 lg:py-32">
          <div className="max-w-3xl mx-auto text-center">
            {/* Logo */}
            <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-8 animate-fade-in">
              <div className="w-8 h-8 rounded-lg gradient-eco flex items-center justify-center">
                <Leaf className="h-4 w-4 text-primary-foreground" />
              </div>
              <span className="text-sm font-medium text-primary">EcoPackAI</span>
            </div>

            <h1 
              className="text-4xl sm:text-5xl lg:text-6xl font-display font-bold mb-6 animate-fade-in"
              style={{ animationDelay: "0.1s" }}
            >
              Sustainable Packaging,{" "}
              <span className="gradient-eco-text">Powered by AI</span>
            </h1>

            <p 
              className="text-lg sm:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto animate-fade-in"
              style={{ animationDelay: "0.2s" }}
            >
              Transform your packaging decisions with intelligent recommendations that 
              reduce environmental impact while optimizing cost and performance.
            </p>

            <div 
              className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in"
              style={{ animationDelay: "0.3s" }}
            >
              <Button asChild size="lg" className="gradient-eco text-lg px-8">
                <Link to="/auth">
                  Get Started <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="text-lg px-8">
                <Link to="/auth">Learn More</Link>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="container mx-auto px-4 py-20">
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="group p-6 rounded-2xl bg-card border border-border hover:border-primary/50 hover:eco-shadow transition-all duration-300 animate-fade-in"
              style={{ animationDelay: `${0.4 + index * 0.1}s` }}
            >
              <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-4 group-hover:gradient-eco group-hover:text-primary-foreground transition-all duration-300">
                <feature.icon className="h-7 w-7 text-primary group-hover:text-primary-foreground" />
              </div>
              <h3 className="text-xl font-display font-bold mb-2">{feature.title}</h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="container mx-auto px-4 py-20">
        <div className="relative rounded-3xl gradient-eco p-12 lg:p-16 text-center overflow-hidden">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJNMzYgMzRjMC0yLjIxLTEuNzktNC00LTRzLTQgMS43OS00IDQgMS43OSA0IDQgNCA0LTEuNzkgNC00eiIvPjwvZz48L2c+PC9zdmc+')] opacity-30" />
          <div className="relative z-10">
            <h2 className="text-3xl lg:text-4xl font-display font-bold text-primary-foreground mb-4">
              Ready to Go Green?
            </h2>
            <p className="text-lg text-primary-foreground/80 mb-8 max-w-xl mx-auto">
              Join hundreds of businesses making smarter, more sustainable packaging choices.
            </p>
            <Button asChild size="lg" variant="secondary" className="text-lg px-8">
              <Link to="/auth">
                Start Free <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>© 2024 EcoPackAI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
