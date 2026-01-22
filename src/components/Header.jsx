import React from "react";

export default function Header({ onToggle, mode }) {
  return (
    <header className="bg-slate-900 shadow-md">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">

        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center text-white font-bold">
          </div>
          <span className="text-white text-lg font-semibold">
            EcoPackAI
          </span>
        </div>

        {/* Navbar Buttons */}
        <div className="flex items-center gap-3">
          <button
            className="
              px-4 h-9 rounded-lg
              text-sm font-medium
              text-slate-300
              hover:text-white hover:bg-white/10
              transition
            "
          >
            Help
          </button>

          <button
            onClick={onToggle}
            className="
              px-4 h-9 rounded-lg
              bg-gradient-to-r from-cyan-400 to-teal-400
              text-slate-900 font-semibold
              shadow-md
              hover:shadow-lg
              transition
            "
          >
            {mode === "login" ? "Sign up" : "Log in"}
          </button>
        </div>
      </div>
    </header>
  );
}
