import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  GoogleLoginButton,
  MicrosoftLoginButton,
} from "./SocialButtons";

export default function LoginPage({ onLoginSuccess }) {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState({ type: "", text: "" });

  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg({ type: "", text: "" });

    try {
      const response = await fetch("http://localhost:5000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        setMsg({
          type: "error",
          text: data.error || "Login failed",
        });
        return;
      }

      // ✅ STORE JWT TOKEN
      localStorage.setItem("token", data.token);

      setMsg({
        type: "success",
        text: "Login successful! Redirecting...",
      });

      // ✅ REDIRECT TO DASHBOARD
      setTimeout(() => {
        navigate("/dashboard");
      }, 700);

    } catch (err) {
      setMsg({ type: "error", text: "Server error. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = "http://localhost:5000/auth/google";
  };

  const handleMicrosoftLogin = () => {
    window.location.href = "http://localhost:5000/auth/microsoft";
  };

  return (
    <div className="min-h-screen auth-wrapper flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="auth-card flex w-full max-w-5xl bg-white rounded-2xl shadow-lg overflow-hidden flex-col lg:flex-row">
        {/* LEFT ILLUSTRATION */}
        <div className="left-panel hidden lg:flex w-1/2 items-center justify-center bg-slate-50">
          <img
            src="/illustrations/login.png"
            alt="Login illustration"
            className="max-w-md w-full object-contain"
          />
        </div>

        {/* RIGHT FORM */}
        <div className="right-panel w-full lg:w-1/2 px-6 sm:px-8 lg:px-12 py-10 min-w-0">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mb-2">
            Welcome back
          </h1>
          <p className="text-gray-600 mb-6 sm:mb-8 text-sm sm:text-base">
            Sign in to continue to <span className="font-medium text-emerald-600">EcoPackAI</span>
          </p>

          {/* SOCIAL LOGIN */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-6">
            <GoogleLoginButton disabled={loading} onClick={handleGoogleLogin} />
            <MicrosoftLoginButton disabled={loading} onClick={handleMicrosoftLogin} />
          </div>

          {/* DIVIDER */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-white px-4 text-sm text-gray-500">
                or continue with email
              </span>
            </div>
          </div>

          {/* FORM */}
          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            {/* EMAIL */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email address
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="you@example.com"
                className="w-full input-lg h-11 px-4 rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                aria-invalid={msg.type === "error"}
                required
              />
            </div>

            {/* PASSWORD */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-sm text-blue-600 hover:underline"
                >
                  Forgot password?
                </Link>
              </div>

              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
                  className="w-full input-lg h-11 px-4 pr-12 rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                  aria-invalid={msg.type === "error"}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 p-1"
                  aria-label={
                    showPassword ? "Hide password" : "Show password"
                  }
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
              </div>
            </div>

            {/* MESSAGE */}
            {msg.text && (
              <p
                className={`text-sm ${msg.type === "error"
                  ? "text-red-600"
                  : "text-green-600"
                  }`}
              >
                {msg.text}
              </p>
            )}

            {/* SUBMIT */}
            <button
              type="submit"
              disabled={loading}
              className="w-full h-12 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition disabled:opacity-50"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          {/* FOOTER */}
          <p className="text-sm text-gray-600 text-center mt-6">
            Don’t have an account?{" "}
            <Link
              to="/signup"
              className="text-emerald-600 font-medium hover:underline"
            >
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
