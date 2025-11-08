import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { axiosInstance } from "../api";
import { useAuth } from "../context/AuthContext";

function Settings() {
  const [deliveryTime, setDeliveryTime] = useState("08:00");
  const [deliveryEnabled, setDeliveryEnabled] = useState(true);
  const [timezone, setTimezone] = useState("UTC");
  const { user } = useAuth();

  const timezones = [
    "UTC",
    "America/New_York",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Paris",
    "Asia/Kolkata",
    "Asia/Singapore",
    "Australia/Sydney",
  ];

  useEffect(() => {
    if (user) {
      if (user.delivery_time) setDeliveryTime(user.delivery_time);
      if (typeof user.delivery_enabled === "boolean") setDeliveryEnabled(user.delivery_enabled);
      if (user.timezone) setTimezone(user.timezone);
    }
  }, [user]);

  const saveSettings = async () => {
    try {
      const res = await axiosInstance.put("/auth/me/delivery", {
        delivery_time: deliveryTime,
        delivery_enabled: deliveryEnabled,
        timezone: timezone,
      });
      toast.success("Settings saved");
    } catch (e) {
      toast.error("Failed to save settings");
    }
  };

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-3xl font-extrabold">Settings</h1>
        <p className="text-slate-600 text-sm">Configure your RP-Agentic preferences</p>
      </div>
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
        <label className="block mb-2 font-medium">Delivery Time</label>
        <input type="time" value={deliveryTime} onChange={e=>setDeliveryTime(e.target.value)} className="border border-slate-300 p-2 mb-3 rounded w-full focus:outline-none focus:ring-2 focus:ring-emerald-500"/>
        <label className="block mb-2 font-medium">Timezone</label>
        <select value={timezone} onChange={e=>setTimezone(e.target.value)} className="border border-slate-300 p-2 mb-3 rounded w-full focus:outline-none focus:ring-2 focus:ring-emerald-500">
          {timezones.map(tz => (
            <option key={tz} value={tz}>{tz}</option>
          ))}
        </select>
        <div className="mb-3 flex items-center space-x-2">
          <label className="font-medium">Enable WhatsApp Delivery</label>
          <input type="checkbox" checked={deliveryEnabled} onChange={e=>setDeliveryEnabled(e.target.checked)} className="h-4 w-4"/>
        </div>
        <button onClick={saveSettings} className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded">Save Settings</button>
      </div>
    </div>
  );
}

export default Settings;
