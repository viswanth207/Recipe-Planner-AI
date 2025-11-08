import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { axiosInstance } from "../api";
import { toast } from "react-toastify";
import { useNavigate } from "react-router-dom";

function Onboarding() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    if (user?.whatsappVerified) {
      navigate("/dashboard");
    }
  }, [user, navigate]);

  const confirm = async () => {
    setVerifying(true);
    try {
      const res = await axiosInstance.put("/auth/me/whatsapp-verify", { verified: true });
      if (res?.data?.ok) {
        toast.success("WhatsApp verified! Redirecting to Dashboard...");
        setUser(prev => ({ ...(prev || {}), whatsappVerified: true }));
        navigate("/dashboard");
      } else {
        toast.error("Could not mark WhatsApp verified.");
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to verify WhatsApp.");
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4">
      {/* Background image with dark overlay */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: "url('/meal-pattern.svg')", filter: "blur(2px)" }}
      />
      <div className="absolute inset-0 bg-black/40" />

      {/* Centered card */}
      <div className="relative max-w-xl w-full bg-white rounded-2xl shadow-2xl ring-1 ring-slate-200/60 p-8 fade-in">
        <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-yellow-500">
          Welcome to RP-Agentic
        </h1>
        <p className="mt-3 text-slate-600 text-sm">To receive meal plans via WhatsApp, first join our Twilio sandbox.</p>

        {/* Light transparent info card with icon */}
        <div className="mt-6 bg-white/70 backdrop-blur-sm border border-white/60 rounded-xl p-5">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">🥗</span>
            <div className="flex-1">
              <p className="text-sm text-slate-700">Send the message <span className="font-semibold">join grow-complete</span> to our sandbox number.</p>
              <div className="mt-3 flex flex-col sm:flex-row gap-3">
                <a
                  href="https://wa.me/14155238886?text=join%20grow-complete"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center justify-center px-5 py-2.5 rounded-full text-white bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 shadow-md transition-all duration-200 hover:scale-[1.02]"
                >
               
                  Open WhatsApp
                </a>
                <button
                  onClick={confirm}
                  disabled={verifying}
                  className="inline-flex items-center justify-center px-5 py-2.5 rounded-full text-white bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 shadow-md transition-all duration-200 hover:scale-[1.02] disabled:opacity-60"
                >
             
                  {verifying ? "Verifying..." : "I sent the message"}
                </button>
              </div>
            </div>
          </div>
        </div>

        <p className="mt-4 text-xs text-slate-500">After confirming, we'll redirect you to your dashboard.</p>
      </div>
    </div>
  );
}

export default Onboarding;