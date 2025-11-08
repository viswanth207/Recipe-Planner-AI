import React from "react";

function Footer() {
  return (
    <footer className="mt-8 bg-gradient-to-r from-emerald-600 via-green-600 to-emerald-700 text-white shadow-lg backdrop-blur supports-[backdrop-filter]:backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-4 py-4 text-xs sm:text-sm text-white/90 text-center">
        <p className="leading-relaxed">© {new Date().getFullYear()} Recipe Planner — Built with React, FastAPI & Tailwind CSS</p>
        <div className="mt-2 flex items-center justify-center text-white/80">
          <a href="/privacy" className="hover:text-white transition-colors">Privacy</a>
          <span className="mx-2 text-white/40">•</span>
          <a href="/terms" className="hover:text-white transition-colors">Terms</a>
          <span className="mx-2 text-white/40">•</span>
          <a href="/contact" className="hover:text-white transition-colors">Contact</a>
        </div>
      </div>
    </footer>
  );
}

export default Footer;