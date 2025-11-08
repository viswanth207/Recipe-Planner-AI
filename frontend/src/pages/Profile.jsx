import React, { useState, useEffect } from "react";
import { axiosInstance } from "../api";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthContext";

function Profile() {
  const [profile, setProfile] = useState({ name: "", email: "", phone: "" });
  const { user, setUser } = useAuth();
  const [verifying, setVerifying] = useState(false);

  const fetchProfile = async () => {
    // Placeholder: implement API to fetch user profile
    toast.info("Profile fetch API not implemented yet");
  };

  const updateProfile = async () => {
    // Placeholder: implement API to update profile
    toast.info("Profile update API not implemented yet");
  };

  useEffect(() => { fetchProfile(); }, []);
  useEffect(() => {
    if (user) {
      setProfile({ name: user.name || "", email: user.email || "", phone: user.phone || "" });
    }
  }, [user]);

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-3xl font-extrabold">Profile</h1>
        <p className="text-slate-600 text-sm">Manage your RP-Agentic account details</p>
      </div>

      {/* Read-only user details card */}
      <div className="bg-white/90 backdrop-blur-sm border border-emerald-200 rounded-xl p-5 shadow-md">
        <h2 className="text-xl font-bold text-slate-900 mb-3">Your Info</h2>
        <div className="grid sm:grid-cols-3 gap-4 text-slate-800">
          <div>
            <p className="text-sm text-slate-500">Name</p>
            <p className="font-semibold">{profile.name || "—"}</p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Email</p>
            <p className="font-semibold">{profile.email || "—"}</p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Phone</p>
            <p className="font-semibold">{profile.phone || "—"}</p>
          </div>
        </div>
        {!user?.whatsappVerified && (
          <div className="mt-4 bg-amber-50 border border-amber-200 text-amber-900 rounded-lg p-3">
          <p className="text-sm">To receive your daily recipe plan via WhatsApp, please send the message <span className="font-semibold">join grow-complete</span> to our Twilio sandbox number.</p>
            <div className="mt-2 flex gap-2">
            <a href="https://wa.me/14155238886?text=join%20grow-complete" target="_blank" rel="noreferrer" className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg">Open WhatsApp</a>
              <button onClick={async ()=>{setVerifying(true); try { const res=await axiosInstance.put('/auth/me/whatsapp-verify',{verified:true}); if(res?.data?.ok){ toast.success('WhatsApp verified!'); setUser(prev=>({...(prev||{}), whatsappVerified:true})); } else { toast.error('Could not verify.'); } } catch(e){ toast.error(e.response?.data?.detail||'Failed'); } finally { setVerifying(false); } }} className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg disabled:opacity-60" disabled={verifying}>{verifying? 'Verifying...' : 'I sent the message'}</button>
            </div>
          </div>
        )}
      </div>

      {/* Editable form (optional) */}
      <div className="bg-white border border-emerald-200 rounded-xl p-5 shadow-sm mt-6">
        <h3 className="text-lg font-semibold mb-3 text-slate-900">Update Details</h3>
        <input type="text" value={profile.name} onChange={e=>setProfile({...profile,name:e.target.value})} placeholder="Name" className="border border-slate-300 h-11 px-4 mb-3 rounded w-full focus:outline-none focus:ring-2 focus:ring-emerald-500"/>
        <input type="text" value={profile.email} onChange={e=>setProfile({...profile,email:e.target.value})} placeholder="Email" className="border border-slate-300 h-11 px-4 mb-3 rounded w-full focus:outline-none focus:ring-2 focus:ring-emerald-500"/>
        <input type="text" value={profile.phone} onChange={e=>setProfile({...profile,phone:e.target.value})} placeholder="Phone" className="border border-slate-300 h-11 px-4 mb-3 rounded w-full focus:outline-none focus:ring-2 focus:ring-emerald-500"/>
        <button onClick={updateProfile} className="bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-700 hover:to-green-700 text-white px-4 py-2 rounded">Update Profile</button>
      </div>
    </div>
  );
}

export default Profile;
