import React, { useState, useEffect } from "react";
import { axiosInstance } from "../api";
import { toast } from "react-toastify";
import IngredientForm from "../components/IngredientForm";
import { useAuth } from "../context/AuthContext";

function Dashboard() {
  const { user, setUser } = useAuth();
  const [ingredients, setIngredients] = useState([]);
  const [selectedTime, setSelectedTime] = useState("08:00");
  // Get today's date in local timezone
  const getTodayDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };
  
  const [selectedDate, setSelectedDate] = useState(getTodayDate()); // Today's date in YYYY-MM-DD format
  const [scheduledText, setScheduledText] = useState("");
  const [showVerifyModal, setShowVerifyModal] = useState(false);

  // Prefer user's saved timezone; fall back to browser's timezone; finally UTC
  const tzPref = (user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC');

  const fetchIngredients = async () => {
    try {
      const res = await axiosInstance.get("/ingredients/");
      setIngredients(res.data);
    } catch (e) {
      toast.error("Failed to load ingredients");
    }
  };

  // Auto-reload when other components change ingredients
  useEffect(() => {
    const handler = () => fetchIngredients();
    window.addEventListener("ingredients:changed", handler);
    return () => window.removeEventListener("ingredients:changed", handler);
  }, []);

  // Delete an ingredient and refresh
  const deleteIngredient = async (name) => {
    try {
      await axiosInstance.delete(`/ingredients/${encodeURIComponent(name)}`);
      toast.success(`Deleted ${name}`);
-      fetchIngredients();
+      await fetchIngredients();
    } catch (e) {
      toast.error(e?.response?.data?.detail || `Failed to delete ${name}`);
    }
  };

  const generateAndDeliver = async () => {
    if (!user?.whatsappVerified) {
      setShowVerifyModal(true);
      return;
    }
    // Validate that the selected date/time is not in the past
    const now = new Date();
    const [hours, minutes] = selectedTime.split(':').map(Number);
    const [year, month, day] = selectedDate.split('-').map(Number);
    const selectedDateTime = new Date(year, month - 1, day, hours, minutes, 0, 0);
    const twoMinutesAgo = new Date(now.getTime() - 120000);
    if (selectedDateTime < twoMinutesAgo) {
      toast.error(`Please select current time or future date and time. Selected: ${selectedDateTime.toLocaleString()}, Current: ${now.toLocaleString()}`);
      return;
    }
    try {
      // If selected date is today and the minute matches current minute (±1m), request immediate send
      const sameMinute = (selectedDate === getTodayDate()) && (Math.abs(selectedDateTime.getTime() - now.getTime()) <= 60000);
      const payload = {
        delivery_time: selectedTime,
        delivery_date: selectedDate,
        delivery_enabled: true,
        timezone: tzPref,
        send_now: sameMinute,
        ingredients: (ingredients || []).map(i => ({ name: i.name, quantity: i.quantity, unit: i.unit })),
      };
      const res = await axiosInstance.post("/agentic/run", payload);
      const formatted = selectedDateTime.toLocaleString([], {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
      setScheduledText(formatted);
      if (res?.data?.ok) {
        if (res?.data?.whatsapp_sent) {
          toast.success(`Plan saved and sent via WhatsApp (${res?.data?.meal_key || 'meal'})`);
        } else {
          toast.success(`Plan saved. Scheduled delivery at ${selectedTime}.`);
        }
      } else {
        toast.error(res?.data?.detail || "Failed to generate & deliver");
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to generate & deliver");
    }
  };
  const getNowInTZ = (tz) => {
    // Create a Date representing now in the target timezone by parsing the localized string.
    // This approach avoids misinterpreting offsets when setting hours directly on a UTC Date.
    const str = new Date().toLocaleString('en-US', { timeZone: tz });
    return new Date(str);
  };

  const computeScheduledDateTZ = (hhmm, tz) => {
    try {
      const [h, m] = String(hhmm).split(":").map(Number);
      const nowTZ = getNowInTZ(tz);
      // Reconstruct a date in the target timezone with desired time by using locale parts
      const parts = new Intl.DateTimeFormat('en-US', {
        year: 'numeric', month: '2-digit', day: '2-digit', timeZone: tz
      }).formatToParts(nowTZ);
      const get = (type) => parts.find(p => p.type === type)?.value || '';
      const mm = get('month');
      const dd = get('day');
      const yyyy = get('year');
      // Build a local datetime string for the timezone and parse it
      const baseStr = `${mm}/${dd}/${yyyy} ${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:00`;
      const scheduled = new Date(new Date(baseStr).toLocaleString('en-US', { timeZone: tz }));
      if (scheduled.getTime() < nowTZ.getTime()) {
        // add one day (still in tz context)
        const nextDay = new Date(scheduled);
        nextDay.setDate(nextDay.getDate() + 1);
        return nextDay;
      }
      return scheduled;
    } catch {
      return getNowInTZ(tz);
    }
  };

  const confirmWhatsAppSent = async () => {
    try {
      const res = await axiosInstance.put("/auth/me/whatsapp-verify", { verified: true });
      if (res?.data?.ok) {
        toast.success("WhatsApp verified! You can now send plans.");
        setUser(prev => ({ ...(prev || {}), whatsappVerified: true }));
        setShowVerifyModal(false);
      } else {
        toast.error("Could not mark WhatsApp verified.");
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to verify WhatsApp.");
    }
  };

  // New: send the selected meal immediately via WhatsApp
  const sendNow = async () => {
    if (!user?.whatsappVerified) {
      setShowVerifyModal(true);
      return;
    }
    try {
      const res = await axiosInstance.post("/whatsapp/send", { selected_time: selectedTime });
      const hint = res?.data?.meta_raw?.twilio_hint;
      const meal = res?.data?.meal || "meal";
      const msgId = res?.data?.message_id || res?.data?.meta_message_id;
      if (res?.data?.ok) {
        toast.success(`Sent ${meal} via WhatsApp successfully${msgId ? ` (id ${msgId})` : ''}.`);
      } else {
        if (hint) {
          toast.error(hint);
        } else {
          toast.error(res?.data?.detail || "Failed to send via WhatsApp");
        }
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "WhatsApp send failed");
    }
  };

  useEffect(() => { fetchIngredients(); }, []);

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-extrabold">Dashboard</h1>
        <p className="text-slate-600 text-sm">Add your ingredients and schedule daily WhatsApp delivery</p>
      </div>

      {/* WhatsApp verification banner */}
      {!user?.whatsappVerified && (
        <div className="rounded-2xl bg-yellow-50 border border-yellow-200 p-4 flex items-center justify-between">
          <div>
            <p className="text-sm">To receive your daily recipe plan via WhatsApp, please send the message <span className="font-semibold">join grow-complete</span> to our Twilio sandbox number.</p>
          </div>
          <div className="flex gap-2">
            <a href="https://wa.me/14155238886?text=join%20grow-complete" target="_blank" rel="noreferrer" className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg">Open WhatsApp</a>
            <button onClick={confirmWhatsAppSent} className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg">I sent the message</button>
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Ingredients + Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Add Ingredients Card */}
          <div className="rounded-2xl bg-white/70 backdrop-blur-md shadow-lg ring-1 ring-white/40 p-5 transition-all duration-300 ease-in-out">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Add Ingredients</h2>
            <IngredientForm onUpdate={fetchIngredients} />
          </div>

          {/* Ingredients Table Card */}
          <div className="rounded-2xl bg-white/70 backdrop-blur-md shadow-lg ring-1 ring-white/40 p-5 transition-all duration-300 ease-in-out">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xl font-semibold text-slate-900">Your Ingredients</h2>
              <span className="text-sm text-slate-500">{ingredients.length} items</span>
            </div>
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <div className="max-h-64 overflow-auto scrollbar-thin">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-50 text-slate-700">
                    <tr>
                      <th className="text-left px-4 py-2 font-medium">Ingredient</th>
                      <th className="text-left px-4 py-2 font-medium">Quantity</th>
                      <th className="text-left px-4 py-2 font-medium">Unit</th>
                      <th className="text-left px-4 py-2 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {ingredients.map((ing, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? "bg-white" : "bg-slate-50 hover:bg-slate-100 transition-all duration-300 ease-in-out"}>
                        <td className="px-4 py-2 font-medium text-slate-900">{ing.name}</td>
                        <td className="px-4 py-2 text-slate-700">{ing.quantity}</td>
                        <td className="px-4 py-2 text-slate-700">{ing.unit}</td>
                        <td className="px-4 py-2">
                          <button onClick={() => deleteIngredient(ing.name)} className="text-sm px-3 py-1 rounded bg-red-500 hover:bg-red-600 text-white">Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="space-y-6">
          <div className="rounded-2xl bg-white/70 backdrop-blur-md shadow-lg ring-1 ring-white/40 p-5 transition-all duration-300 ease-in-out">
            <h3 className="text-lg font-semibold text-slate-900 mb-3">Send Plan</h3>
            <div className="space-y-3">
              <div>
                <label className="block mb-1 text-sm font-medium text-slate-700">Select Date</label>
                <input 
                  type="date" 
                  value={selectedDate} 
                  onChange={e=>setSelectedDate(e.target.value)} 
                  min={getTodayDate()}
                  className="border border-slate-300 h-11 px-3 rounded w-full focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all duration-300 ease-in-out" 
                />
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-slate-700">Select Time</label>
                <input type="time" value={selectedTime} onChange={e=>setSelectedTime(e.target.value)} className="border border-slate-300 h-11 px-3 rounded w-full focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all duration-300 ease-in-out" />
              </div>
            </div>
            {scheduledText && (
              <p className="mt-2 text-sm text-slate-700">Scheduled for: <span className="font-medium">{scheduledText}</span></p>
            )}
            <button onClick={generateAndDeliver} className="mt-4 w-full bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white px-4 py-3 rounded-xl shadow-lg transition-all duration-300 ease-in-out hover:shadow-emerald-300/40">
              Generate & Deliver
            </button>
            <p className="text-xs text-slate-500 mt-2">One click: we generate your plan, save it, and send via WhatsApp at your selected time. If the time matches now, it sends immediately.</p>
          </div>
        </div>
      </div>

      {/* Modal gating send if not verified */}
      {showVerifyModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
            <h3 className="text-lg font-semibold mb-2">WhatsApp Verification Required</h3>
            <p className="text-sm text-slate-700">Please send the join message on WhatsApp first.</p>
            <a href="https://wa.me/14155238886?text=join%20grow-complete" target="_blank" rel="noreferrer" className="mt-3 inline-block px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg">Open WhatsApp</a>
            <div className="mt-4 flex justify-end gap-2">
              <button onClick={() => setShowVerifyModal(false)} className="px-3 py-2 bg-slate-200 rounded-lg">Close</button>
              <button onClick={confirmWhatsAppSent} className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg">I sent it</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
