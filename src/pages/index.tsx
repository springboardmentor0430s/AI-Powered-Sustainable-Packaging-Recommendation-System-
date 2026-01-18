@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

@layer base {
  :root {
    /* EcoPackAI Professional Theme - Light */
    --background: 140 20% 98%;
    --foreground: 150 30% 12%;
    
    --card: 140 15% 99%;
    --card-foreground: 150 30% 12%;
    
    --popover: 140 15% 99%;
    --popover-foreground: 150 30% 12%;
    
    --primary: 152 65% 38%;
    --primary-foreground: 0 0% 100%;
    
    --secondary: 145 25% 92%;
    --secondary-foreground: 150 30% 15%;
    
    --muted: 140 15% 94%;
    --muted-foreground: 150 15% 45%;
    
    --accent: 168 70% 42%;
    --accent-foreground: 0 0% 100%;
    
    --destructive: 0 72% 51%;
    --destructive-foreground: 0 0% 100%;
    
    --border: 145 20% 88%;
    --input: 145 20% 88%;
    --ring: 152 65% 38%;
    
    --radius: 0.75rem;
    
    /* Sidebar */
    --sidebar-background: 152 40% 18%;
    --sidebar-foreground: 140 20% 95%;
    --sidebar-primary: 152 65% 50%;
    --sidebar-primary-foreground: 0 0% 100%;
    --sidebar-accent: 152 35% 25%;
    --sidebar-accent-foreground: 140 20% 95%;
    --sidebar-border: 152 30% 25%;
    --sidebar-ring: 152 65% 50%;
    
    /* Custom tokens */
    --success: 152 65% 38%;
    --success-foreground: 0 0% 100%;
    --warning: 38 92% 50%;
    --warning-foreground: 0 0% 100%;
    --info: 200 80% 50%;
    --info-foreground: 0 0% 100%;
  }

  .dark {
    --background: 150 25% 8%;
    --foreground: 140 20% 95%;
    
    --card: 150 22% 11%;
    --card-foreground: 140 20% 95%;
    
    --popover: 150 22% 11%;
    --popover-foreground: 140 20% 95%;
    
    --primary: 152 60% 48%;
    --primary-foreground: 150 25% 8%;
    
    --secondary: 150 20% 18%;
    --secondary-foreground: 140 20% 90%;
    
    --muted: 150 18% 15%;
    --muted-foreground: 140 15% 55%;
    
    --accent: 168 65% 48%;
    --accent-foreground: 150 25% 8%;
    
    --destructive: 0 62% 55%;
    --destructive-foreground: 0 0% 100%;
    
    --border: 150 18% 20%;
    --input: 150 18% 20%;
    --ring: 152 60% 48%;
    
    /* Sidebar Dark */
    --sidebar-background: 150 30% 6%;
    --sidebar-foreground: 140 20% 90%;
    --sidebar-primary: 152 60% 48%;
    --sidebar-primary-foreground: 150 25% 8%;
    --sidebar-accent: 150 25% 12%;
    --sidebar-accent-foreground: 140 20% 90%;
    --sidebar-border: 150 20% 15%;
    --sidebar-ring: 152 60% 48%;
    
    --success: 152 60% 48%;
    --success-foreground: 150 25% 8%;
    --warning: 38 85% 55%;
    --warning-foreground: 0 0% 10%;
    --info: 200 75% 55%;
    --info-foreground: 0 0% 10%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  
  body {
    @apply bg-background text-foreground font-sans antialiased;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
  
  h1, h2, h3, h4, h5, h6 {
    @apply font-display font-bold tracking-tight;
  }
}

@layer utilities {
  .gradient-eco {
    background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--accent)) 100%);
  }
  
  .gradient-eco-text {
    background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--accent)) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .glass-effect {
    @apply backdrop-blur-md bg-card/80 border border-border/50;
  }
  
  .eco-shadow {
    box-shadow: 0 4px 20px -4px hsl(var(--primary) / 0.15),
                0 8px 40px -8px hsl(var(--primary) / 0.1);
  }
  
  .eco-shadow-lg {
    box-shadow: 0 8px 30px -6px hsl(var(--primary) / 0.2),
                0 16px 60px -12px hsl(var(--primary) / 0.15);
  }
}
