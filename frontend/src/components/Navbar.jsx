import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const initials = (user?.name || user?.email || "U").charAt(0).toUpperCase();

  return (
    <header className="sticky top-0 z-40 bg-gradient-to-r from-emerald-600 via-green-600 to-emerald-700 text-white shadow-lg backdrop-blur supports-[backdrop-filter]:backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between transition-all duration-300 ease-in-out">
        <div className="flex items-center space-x-3">
          <span className="font-extrabold text-2xl md:text-3xl tracking-tight">Recipe Planner</span>
         
        </div>
        <nav className="flex items-center space-x-6">
          <NavLink to="/dashboard" className={({isActive})=>`text-sm sm:text-base px-3 py-2 rounded transition-all duration-300 ease-in-out ${isActive?"bg-white/10":"hover:bg-white/10"}`}>Dashboard</NavLink>
          <NavLink to="/profile" className={({isActive})=>`text-sm sm:text-base px-3 py-2 rounded transition-all duration-300 ease-in-out ${isActive?"bg-white/10":"hover:bg-white/10"}`}>Profile</NavLink>
          {user && (
            <div className="relative">
              <button
                onClick={() => setOpen((o) => !o)}
                className="h-10 w-10 rounded-full bg-white/20 text-white flex items-center justify-center ring-1 ring-white/30 hover:bg-white/30 focus:outline-none transition-all duration-300 ease-in-out"
                aria-label="Profile menu"
              >
                <span className="text-base font-bold">{initials}</span>
              </button>
              {open && (
                <div className="absolute right-0 mt-2 w-44 bg-white text-slate-900 rounded-lg shadow-lg ring-1 ring-slate-200 transition-all duration-300 ease-in-out">
                  <button className="w-full text-left px-3 py-2 hover:bg-slate-100" onClick={() => { setOpen(false); navigate('/profile'); }}>
                    View Profile
                  </button>
                  <button className="w-full text-left px-3 py-2 hover:bg-slate-100" onClick={() => { setOpen(false); logout(); }}>
                    Logout
                  </button>
                </div>
              )}
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Navbar;