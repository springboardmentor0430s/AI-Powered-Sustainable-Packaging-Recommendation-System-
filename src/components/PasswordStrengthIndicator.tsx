import { useMemo } from "react";
import { Check, X } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface PasswordStrengthIndicatorProps {
  password: string;
}

interface Requirement {
  label: string;
  met: boolean;
}

export function PasswordStrengthIndicator({ password }: PasswordStrengthIndicatorProps) {
  const requirements: Requirement[] = useMemo(() => {
    return [
      { label: "At least 8 characters", met: password.length >= 8 },
      { label: "Contains uppercase letter", met: /[A-Z]/.test(password) },
      { label: "Contains lowercase letter", met: /[a-z]/.test(password) },
      { label: "Contains a number", met: /[0-9]/.test(password) },
      { label: "Contains special character", met: /[!@#$%^&*(),.?":{}|<>]/.test(password) },
    ];
  }, [password]);

  const strength = useMemo(() => {
    const metCount = requirements.filter((r) => r.met).length;
    if (metCount === 0) return { score: 0, label: "Very Weak", color: "bg-destructive" };
    if (metCount <= 2) return { score: 20, label: "Weak", color: "bg-destructive" };
    if (metCount === 3) return { score: 40, label: "Fair", color: "bg-warning" };
    if (metCount === 4) return { score: 70, label: "Good", color: "bg-info" };
    return { score: 100, label: "Strong", color: "bg-success" };
  }, [requirements]);

  if (!password) return null;

  return (
    <div className="space-y-3 animate-fade-in">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Password strength</span>
          <span
            className={`font-medium ${
              strength.score >= 70
                ? "text-success"
                : strength.score >= 40
                ? "text-warning"
                : "text-destructive"
            }`}
          >
            {strength.label}
          </span>
        </div>
        <Progress value={strength.score} className="h-2" />
      </div>
      
      <div className="grid grid-cols-1 gap-1.5">
        {requirements.map((req, index) => (
          <div
            key={index}
            className={`flex items-center gap-2 text-sm transition-colors ${
              req.met ? "text-success" : "text-muted-foreground"
            }`}
          >
            {req.met ? (
              <Check className="h-3.5 w-3.5" />
            ) : (
              <X className="h-3.5 w-3.5" />
            )}
            <span>{req.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
