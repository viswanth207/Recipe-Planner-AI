import React from "react";
import { useLocation } from "react-router-dom";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import VoiceBot from "../components/VoiceBot";

function AppLayout({ children }) {
  const location = useLocation();
  const isDashboard = location.pathname === "/dashboard";
  return (
    <div
      className={`min-h-screen text-slate-900 flex flex-col ${isDashboard ? "bg-gradient-to-br from-emerald-50 via-white to-green-50" : "bg-slate-50"}`}
    >
      <Navbar />
      <main className="flex-1">
        <div className="max-w-6xl mx-auto px-4 py-6">
          {children}
        </div>
      </main>
      {/* Global Voice Assistant Widget */}
      <VoiceBot />
      <Footer />
    </div>
  );
}

export default AppLayout;