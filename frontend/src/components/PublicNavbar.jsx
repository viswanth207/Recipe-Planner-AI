import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function PublicNavbar() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const NavLink = ({ href, children }) => (
    <a href={href} className="text-slate-700 hover:text-emerald-600 transition-colors px-3 py-2 rounded">
      {children}
    </a>
  );

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur border-b border-slate-200">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="font-extrabold text-2xl tracking-tight text-slate-900">Recipe Planner</span>
        </div>
        <nav className="hidden md:flex items-center space-x-2">
          <NavLink href="#home">Home</NavLink>
          <NavLink href="#features">Features</NavLink>
          <NavLink href="#how">How It Works</NavLink>
          <NavLink href="#cta">Contact</NavLink>
          <button onClick={() => navigate('/login')} className="text-slate-700 hover:text-slate-900 px-3 py-2 rounded">
            Login
          </button>
          <button
            onClick={() => navigate('/signup')}
            className="ml-2 inline-flex items-center px-4 py-2 rounded-full text-white bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 shadow-sm"
          >
            Sign Up
          </button>
        </nav>
        <button
          className="md:hidden inline-flex items-center justify-center h-10 w-10 rounded-md border border-slate-300 text-slate-700"
          onClick={() => setOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          ☰
        </button>
      </div>
      {open && (
        <div className="md:hidden border-t border-slate-200 bg-white">
          <div className="max-w-6xl mx-auto px-4 py-3 grid gap-2">
            <NavLink href="#home">Home</NavLink>
            <NavLink href="#features">Features</NavLink>
            <NavLink href="#how">How It Works</NavLink>
            <NavLink href="#cta">Contact</NavLink>
            <button onClick={() => navigate('/login')} className="text-left text-slate-700 hover:text-slate-900 px-3 py-2 rounded">
              Login
            </button>
            <button
              onClick={() => navigate('/signup')}
              className="inline-flex items-center justify-center px-4 py-2 rounded-full text-white bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 shadow-sm"
            >
              Sign Up
            </button>
          </div>
        </div>
      )}
    </header>
  );
}

export default PublicNavbar;