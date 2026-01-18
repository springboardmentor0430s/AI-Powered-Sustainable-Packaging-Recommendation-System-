import React, { useState } from "react";

export default function Navbar({ onMenuClick }) {
  const [open, setOpen] = useState(false);

  return (
    <header className="h-16 sm:h-20 bg-white border-b border-slate-100 sticky top-0 z-10 px-4 sm:px-6 flex items-center justify-between">

      {/* Mobile Menu Button */}
      <button
        onClick={onMenuClick}
        className="lg:hidden p-2 text-slate-500 hover:bg-slate-50 rounded-lg mr-2"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
      </button>

      {/* Search Bar - Visual Match */}
      <div className="flex-1 max-w-xl">
        <div className="relative group">
          <span className="absolute left-4 top-2.5 text-slate-400 group-focus-within:text-blue-500 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
          </span>
          <input
            type="text"
            placeholder="Search"
            className="
              w-full h-11 pl-12 pr-4 rounded-full
              bg-slate-100 hover:bg-slate-50 text-slate-600
              border-none focus:ring-0 focus:bg-slate-50
              placeholder-slate-400 font-medium text-sm transition-all
            "
          />
        </div>
      </div>

      {/* Right Icons */}
      <div className="flex items-center gap-5 ml-6">
        {/* Language/Flag */}
        <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-full transition-colors hidden sm:block">
          <span className="text-xl">🇬🇧</span>
        </button>

        {/* Theme/Palette */}
        <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-full transition-colors hidden sm:block">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"></path></svg>
        </button>

        {/* Notifications */}
        <button className="relative p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-full transition-colors">
          <div className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></div>
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>
        </button>

        {/* User Profile */}
        <div className="relative pl-2">
          <button
            onClick={() => setOpen(!open)}
            className="w-10 h-10 rounded-full bg-slate-200 overflow-hidden border border-slate-100 shadow-sm"
          >
            <img
              src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix"
              alt="User"
              className="w-full h-full object-cover"
            />
          </button>

          {/* Dropdown Menu */}
          {open && (
            <div className="absolute right-0 top-12 w-48 bg-white rounded-xl shadow-lg border border-slate-100 py-1 animate-fade-in-up">
              <button
                onClick={() => {
                  localStorage.removeItem("token");
                  window.location.href = "/login";
                }}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-slate-50 transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
