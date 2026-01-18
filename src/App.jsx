import React, { useState } from "react";
import {
  Routes,
  Route,
  Navigate,
  useNavigate,
  useLocation,
} from "react-router-dom";

import LoginPage from "./components/LoginPage";
import SignupPage from "./components/SignupPage";
import Header from "./components/Header";

import DashboardLayout from "./components/DashboardLayout";
import Dashboard from "./components/Dashboard";
import BI from "./components/BI";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  const [mode, setMode] = useState("signup");
  const navigate = useNavigate();
  const location = useLocation();

  // Auth pages check for Header
  const isAuthPage =
    location.pathname === "/login" || location.pathname === "/signup" || location.pathname === "/";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-blue-50">

      {/* Header is global but only shown on auth pages per original design */}
      {isAuthPage && (
        <>
          <Header
            mode={mode}
            onToggle={() => {
              const next = mode === "login" ? "signup" : "login";
              setMode(next);
              navigate(`/${next}`);
            }}
          />
        </>
      )}

      <Routes>
        {/* Public Routes */}
        <Route
          path="/login"
          element={<LoginPage onLoginSuccess={() => navigate("/dashboard")} />}
        />
        <Route path="/signup" element={<SignupPage />} />

        {/* Protected Dashboard Routes */}
        <Route
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/bi" element={<BI />} />
        </Route>

        {/* Default Redirects */}
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Routes>

      {/* Footer only on Auth Pages */}
      {isAuthPage && (
        <footer className="mt-8 text-center text-sm text-gray-400 pb-8">
          Built with care • © {new Date().getFullYear()} Aurora
        </footer>
      )}
    </div>
  );
}
