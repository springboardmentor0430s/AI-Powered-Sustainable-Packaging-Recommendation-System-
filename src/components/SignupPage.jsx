import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { GoogleLoginButton, MicrosoftLoginButton } from "./SocialButtons";

const SignupPage = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState({ type: "", text: "" });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg({ type: "", text: "" });

    try {
      const response = await fetch("http://localhost:5000/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setMsg({
          type: "success",
          text: "Account created successfully! Redirecting to login...",
        });

        setTimeout(() => {
          navigate("/login");
        }, 800);
      } else {
        setMsg({ type: "error", text: data.error || "Signup failed" });
      }
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
      <div className="auth-card relative flex w-full max-w-5xl bg-white rounded-2xl shadow-[0_20px_60px_rgba(2,6,23,0.12)] overflow-hidden flex-col lg:flex-row">
        {/* LEFT ILLUSTRATION */}
        <div className="left-panel hidden lg:flex lg:w-1/2 relative">
          <img
            src="/illustrations/signup.png"
            alt="Signup illustration"
            className="absolute inset-0 w-full h-full object-cover opacity-80"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-black/40 to-black/70" />
          <div className="absolute bottom-12 left-12 text-white p-4">
            <h2 className="text-4xl font-bold mb-4">Join the Future</h2>
            <p className="text-lg opacity-90">Experience the next generation of sustainable packaging AI.</p>
          </div>
        </div>

        {/* RIGHT FORM */}
        <div className="right-panel w-full lg:w-1/2 px-6 sm:px-8 lg:px-12 py-12 bg-white min-w-0">
          <div className="w-full max-w-md mx-auto">
            {/* Logo */}
            <div className="mb-6 flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-600 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-emerald-200">
                A
              </div>
              <div className="text-xl font-bold text-slate-900">Aurora</div>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mb-2">
              Create account
            </h1>

            <p className="text-slate-600 mb-6 sm:mb-8 text-sm sm:text-base">
              Create your account to get started — it’s quick and easy.
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
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              {/* NAME */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full name
                </label>
                <input
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Your full name"
                  className="w-full input-lg h-11 px-4 rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                  aria-invalid={msg.type === "error"}
                />
              </div>

              {/* EMAIL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="you@company.com"
                  className="w-full input-lg h-11 px-4 rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                  aria-invalid={msg.type === "error"}
                />
              </div>

              {/* PASSWORD */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Create a password"
                    className="w-full input-lg h-11 px-4 pr-12 rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                    autoComplete="new-password"
                    aria-invalid={msg.type === "error"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 p-1 hover:text-gray-700"
                    aria-label="Toggle password visibility"
                  >
                    {showPassword ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" /></svg>
                    )}
                  </button>
                </div>
              </div>

              {/* MESSAGE */}
              {msg.text && (
                <p
                  className={`text-sm ${msg.type === "error" ? "text-red-600" : "text-green-600"
                    }`}
                >
                  {msg.text}
                </p>
              )}

              {/* SUBMIT */}
              <button
                type="submit"
                disabled={loading}
                className="w-full h-12 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition disabled:opacity-50 shadow-md hover:shadow-lg"
              >
                {loading ? "Creating account..." : "Create account"}
              </button>
            </form>

            {/* FOOTER */}
            <p className="mt-6 text-center text-sm text-gray-600">
              Already have an account?{" "}
              <Link
                to="/login"
                className="text-emerald-600 font-medium hover:underline"
              >
                Log in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
