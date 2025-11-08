import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { axiosInstance, axiosVoicebot } from "../api";
import { toast } from "react-toastify";

function parseTimeToHHMM(input) {
  if (input) return null;
  const trimmed = input.trim().toLowerCase();
  const hhmm = trimmed.match(/\b(\d{1,2}):(\d{2})\b/);
  if (hhmm) {
    let h = parseInt(hhmm[1], 10);
    let m = parseInt(hhmm[2], 10);
    if (h >= 0 && h <= 23 && m >= 0 && m <= 59) {
      return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
    }
  }
  const ampm = trimmed.match(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b/);
  if (ampm) {
    let h = parseInt(ampm[1], 10);
    let m = ampm[2] ? parseInt(ampm[2], 10) : 0;
    const ap = ampm[3];
    if (h === 12) h = 0;
    if (ap === "pm") h += 12;
    if (h >= 0 && h <= 23 && m >= 0 && m <= 59) {
      return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
    }
  }
  return null;
}

function parseLocalIntent(text) {
  const t = (text || "").toLowerCase();
  // add ingredient: "add 2 kg rice" or "add 3 tomatoes"
  let m = t.match(/\badd\s+(\d+(?:\.\d+)?)\s*(\w+)?\s+([a-zA-Z ]+)$/);
  if (m) {
    const quantity = parseFloat(m[1]);
    const unit = (m[2] || "").trim();
    const name = (m[3] || "").trim();
    return { type: "add_ingredient", payload: { name, quantity, unit } };
  }
  // delete/remove ingredient: "delete onions" or "remove ingredient rice"
  m = t.match(/\b(delete|remove)\s+(?:ingredient\s+)?([a-zA-Z ]+)$/);
  if (m) {
    const name = (m[2] || "").trim();
    return { type: "delete_ingredient", payload: { name } };
  }
  // set delivery time: "set delivery time to 8:30", "delivery at 7 pm"
  m = t.match(/\b(set\s+)?delivery\s+(time\s+)?(to|at)\s+(.+)$/);
  if (m) {
    const timeStr = parseTimeToHHMM(m[4]);
    if (timeStr) return { type: "set_delivery_time", payload: { delivery_time: timeStr } };
  }
  // enable/disable delivery
  if (t.includes("enable delivery") || t.includes("turn on delivery")) {
    return { type: "set_delivery_enabled", payload: { delivery_enabled: true } };
  }
  if (t.includes("disable delivery") || t.includes("turn off delivery")) {
    return { type: "set_delivery_enabled", payload: { delivery_enabled: false } };
  }
  return { type: "unknown" };
}

export default function VoiceBot() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [status, setStatus] = useState("");
  const recognitionRef = useRef(null);
  const retryOnNoSpeechRef = useRef(false);
  const langFallbackAppliedRef = useRef(false);
  const userWantsListeningRef = useRef(false);
  const [mounted, setMounted] = useState(false);

  const selectedLanguage = (typeof navigator !== "undefined" && navigator.language) ? navigator.language : "en-US";


  useEffect(() => {
    setMounted(true);
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setStatus("Speech recognition not supported. Please use Chrome or Edge.");
      return;
    }
    const rec = new SpeechRecognition();
    rec.continuous = true; // allow longer listening to avoid premature end
    rec.interimResults = true; // show interim text while speaking
    rec.lang = selectedLanguage || (navigator.language || "en-US"); // match user locale (e.g., en-IN)
    rec.maxAlternatives = 1;
    rec.onstart = () => {
      setIsListening(true);
      setStatus("Listening...");
    };
    rec.onend = () => {
      setIsListening(false);
      // If user still wants to listen, auto-restart (helps with short pauses)
      if (userWantsListeningRef.current) {
        try { rec.start(); } catch (_) {}
      }
    };
    rec.onerror = (e) => {
      const err = e?.error || "unknown";
      if (err === "not-allowed" || err === "service-not-allowed") {
        setStatus("Microphone access blocked. Enable mic permissions in browser settings.");
      } else if (err === "no-speech") {
        // One-time auto-retry to reduce friction
        if (!retryOnNoSpeechRef.current) {
          retryOnNoSpeechRef.current = true;
          setStatus("No speech detected. Retrying once...");
          try { rec.start(); } catch (_) { /* ignore */ }
        } else {
          // Apply language fallback to en-US once if local locale might not be recognized
          if (!langFallbackAppliedRef.current) {
            langFallbackAppliedRef.current = true;
            rec.lang = "en-US";
            setStatus("No speech detected. Switching to English (US) and retrying...");
            try { rec.start(); } catch (_) { /* ignore */ }
          } else {
            setStatus("No speech detected. Try again and speak clearly.");
          }
        }
      } else {
        setStatus(`Speech error: ${err}`);
      }
    };
    rec.onnomatch = () => setStatus("Couldn’t understand. Please try again.");
    // Provide clearer feedback around audio lifecycle when supported
    rec.onaudiostart = () => setStatus("Listening...");
    rec.onaudioend = () => setStatus("Processing...");
    rec.onsoundstart = () => setStatus("Sound detected...");
    rec.onsoundend = () => setStatus("Processing...");
    rec.onspeechstart = () => setStatus("Speech detected...");
    rec.onspeechend = () => setStatus("Processing...");
    rec.onresult = (event) => {
      let interim = "";
      let finalTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const segment = event.results[i][0]?.transcript || "";
        if (event.results[i].isFinal) finalTranscript += segment;
        else interim += segment;
      }
      const displayText = finalTranscript.trim() || interim.trim();
      if (displayText) setTranscript(displayText);
      if (finalTranscript.trim()) {
        retryOnNoSpeechRef.current = false; // reset retry guard on success
        handleCommand(finalTranscript.trim());
      }
    };
    recognitionRef.current = rec;
  }, []);





  const handleCommand = async (command) => {
    setStatus("Processing...");
    const intent = parseLocalIntent(command);
    try {
      if (intent.type === "add_ingredient") {
        const { name, quantity, unit } = intent.payload;
        await axiosInstance.post("/ingredients/", { name, quantity, unit });
        toast.success(`Added ${name} (${quantity} ${unit || "units"})`);
        setStatus(`Added ${name} to your ingredients.`);
        // Notify other parts of the app (e.g., Dashboard) to refresh
        window.dispatchEvent(new CustomEvent("ingredients:changed"));
      } else if (intent.type === "delete_ingredient") {
        const { name } = intent.payload;
        await axiosInstance.delete(`/ingredients/${encodeURIComponent(name)}`);
        toast.success(`Deleted ${name}`);
        setStatus(`Deleted ${name} from your ingredients.`);
        // Notify other parts of the app (e.g., Dashboard) to refresh
        window.dispatchEvent(new CustomEvent("ingredients:changed"));
      } else if (intent.type === "set_delivery_time") {
        const { delivery_time } = intent.payload;
        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
        
        // Determine if this time is for today or tomorrow
        const now = new Date();
        const [hours, minutes] = delivery_time.split(':').map(Number);
        const deliveryDateTime = new Date();
        deliveryDateTime.setHours(hours, minutes, 0, 0);
        
        // If the delivery time has already passed today, it's for tomorrow
        let dayMessage = "";
        if (deliveryDateTime < now) {
          dayMessage = " (tomorrow)";
        } else {
          dayMessage = " (today)";
        }
        
        // When user sets a delivery time by voice, assume they want delivery enabled
        await axiosInstance.put("/auth/me/delivery", { delivery_time, delivery_enabled: true, timezone: tz });
        toast.success(`Delivery time set to ${delivery_time}${dayMessage}`);
        setStatus(`Delivery time updated to ${delivery_time}${dayMessage}.`);
        // Notify UI to update the Send Plan time selection
        try {
          window.dispatchEvent(
            new CustomEvent("delivery:time_changed", { detail: { delivery_time } })
          );
        } catch (e) {
          // no-op: event dispatch should not break core flow
        }
      } else if (intent.type === "set_delivery_enabled") {
        const { delivery_enabled } = intent.payload;
        await axiosInstance.put("/auth/me/delivery", { delivery_enabled });
        toast.success(`Delivery ${delivery_enabled ? "enabled" : "disabled"}`);
        setStatus(`Delivery ${delivery_enabled ? "enabled" : "disabled"}.`);
      } else {
        // Delegate to AI voicebot when local intent is unknown
        try {
          const res = await axiosVoicebot.post("/voicebot/process", {
            command,
            context: { locale: selectedLanguage }
          });
          const data = res?.data || {};
          const aiMsg = data.response_message || "I understood your request.";
          setStatus(aiMsg);

        } catch (err) {
          console.error("Voicebot processing failed", err);
          setStatus("I couldn’t process that. Please try again.");
          try { speakNowOnce("I couldn’t process that. Please try again."); } catch (_) {}
        }
      }
    } catch (e) {
      console.error(e);
      toast.error("Action failed");
      setStatus("Sorry, that didn't work. Please try again.");
    }
  };



  // Helper: start listening using current device and language
  const startListeningWithCurrentSettings = async () => {
    const rec = recognitionRef.current;
    if (!rec) {
      setStatus("Speech recognition not available");
      return;
    }
    
    // Check if we're in a secure context (HTTPS or localhost)
    if (!window.isSecureContext) {
      setStatus("Voice recognition requires HTTPS or localhost");
      return;
    }
    
    setTranscript("");
    setStatus("Requesting microphone access...");
    
    const ensureMic = async () => {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          setStatus("Microphone API not supported in this browser");
          return false;
        }
        
        // Request permission explicitly first
        const constraints = { audio: true };
        
        console.log("Requesting microphone with constraints:", constraints);
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        
        // Clean up stream after getting permission
        stream.getTracks().forEach(track => track.stop());
        return true;
      } catch (err) {
        console.error("Microphone access error:", err);
        if (err.name === 'NotAllowedError') {
          setStatus("Microphone permission denied. Please allow microphone access in your browser settings.");
        } else if (err.name === 'NotFoundError') {
          setStatus("No microphone found. Please connect a microphone and try again.");
        } else if (err.name === 'NotReadableError') {
          setStatus("Microphone is already in use by another application.");
        } else {
          setStatus(`Microphone error: ${err.message || err.name || 'Unknown error'}`);
        }
        return false;
      }
      return true;
    };
    const ok = await ensureMic();
    if (!ok) return;
    setStatus("Listening...");
    retryOnNoSpeechRef.current = false;
    userWantsListeningRef.current = true;
    try { rec.lang = selectedLanguage; } catch (_) {}
    try {
      rec.start();
    } catch (e) {
      setStatus("Could not start mic. Click allow mic access and try again.");
    }
  };





  const toggleListening = () => {
    const rec = recognitionRef.current;
    if (!rec) {
      setStatus("Speech recognition not available. Please use Chrome, Edge, or Safari.");
      return;
    }
    
    if (isListening) {
      try {
        rec.stop();
      } catch (e) {
        console.warn("Error stopping recognition:", e);
      }
      userWantsListeningRef.current = false;
      setStatus("Stopped listening");
    } else {
      userWantsListeningRef.current = true;
      startListeningWithCurrentSettings();
    }
  };



  return createPortal(
    <div className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 left-auto z-50 group">
      <div
        className={`bg-white/30 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl overflow-hidden transition-all duration-500 ease-out ${isExpanded ? "w-80" : "w-16"} ${isExpanded ? "" : "h-16"} ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
      >
        <div className="p-4">
          {isExpanded ? (
            <div className="space-y-4">
              {/* Title */}
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-800">🎤 AI Voice Assistant</h2>
                <button onClick={() => setIsExpanded(false)} className="text-gray-500 hover:text-gray-700 transition-colors">×</button>
              </div>
              <div className="border-t border-white/30" />

              {/* Mic Button */}
              <div className="flex justify-center">
                <button
                  onClick={toggleListening}
                  disabled={false}
                  className={`w-16 h-16 rounded-full bg-gradient-to-r from-emerald-500 to-green-600 text-white flex items-center justify-center shadow-lg transition-all hover:shadow-[0_0_15px_rgba(16,185,129,0.5)] hover:scale-105 active:scale-95 ${isListening ? "animate-pulse ring-4 ring-emerald-300/40" : "ring-2 ring-white/30"}`}
                  aria-label="Toggle Mic"
                  title="Start/Stop Voice Assistant"
                >
                  {isListening ? "🔴" : "🎤"}
                </button>
              </div>

              {/* Hint / Status */}
              <div className="text-center text-sm text-gray-600 font-medium">
                {status || (isListening ? "Listening..." : "Click mic and speak")}
              </div>

              {/* Transcript */}
              <div className="bg-white/40 backdrop-blur-md border border-white/30 rounded-xl p-3 text-sm h-28 overflow-y-auto text-gray-700">
                {transcript || ""}
              </div>









              {/* Examples */}
              <div>
                <div className="text-xs text-gray-500 mb-2">Examples:</div>
                <div className="flex flex-wrap gap-2">
                  <span className="bg-white/50 px-3 py-1 rounded-full text-xs text-gray-700">add 2 kg rice</span>
                  <span className="bg-white/50 px-3 py-1 rounded-full text-xs text-gray-700">delete onions</span>
                  <span className="bg-white/50 px-3 py-1 rounded-full text-xs text-gray-700">set delivery time to 7:30 pm</span>
                  <span className="bg-white/50 px-3 py-1 rounded-full text-xs text-gray-700">enable delivery</span>
                </div>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setIsExpanded(true)}
              className="w-14 h-14 rounded-full bg-gradient-to-r from-emerald-500 to-green-600 text-white text-2xl flex items-center justify-center shadow-lg transition-all hover:shadow-[0_0_15px_rgba(16,185,129,0.5)] hover:scale-105 active:scale-95"
              aria-label="Open AI Voice Assistant"
              title="Voice Assistant"
            >
              🎤
            </button>
          )}
        </div>
      </div>
      {/* Hover Tooltip */}
      <div className="absolute bottom-full right-0 mb-2 px-2 py-1 rounded-md text-xs font-medium bg-slate-900/90 text-white shadow-md opacity-0 translate-y-1 transition-all duration-200 pointer-events-none group-hover:opacity-100 group-hover:translate-y-0">
        Voice Assistant
      </div>
    </div>,
    document.body
  );
}