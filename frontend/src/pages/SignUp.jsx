import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthContext";

function SignUp() {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "" });
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const success = await signup(form);
      if (success) {
        toast.success("SignUp successful!");
        navigate("/onboarding");
      } else {
        toast.error("Signup failed. Please try again.");
      }
    } catch (e) {
      toast.error("Signup failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-bg flex items-center justify-center" style={{ backgroundImage: "linear-gradient(rgba(249,250,251,0.88), rgba(238,242,255,0.88)), url('/meal-planner.svg')", backgroundSize: 'cover, cover', backgroundPosition: 'center, center -60px', backgroundRepeat: 'no-repeat' }}>
      <div className="w-full max-w-6xl grid md:grid-cols-2 rounded-2xl shadow-2xl overflow-hidden">
        {/* Left visual panel */}
        <div className="hidden md:block relative bg-gradient-to-br from-emerald-600 via-green-600 to-emerald-700 p-8">
          <div className="absolute inset-0 opacity-20">
            <div className="absolute top-8 left-8 h-20 w-20 rounded-full border-2 border-white/30"></div>
            <div className="absolute bottom-10 right-10 h-24 w-24 rounded-full border-2 border-white/20"></div>
            <div className="absolute top-24 right-16 h-8 w-8 rounded-full border-2 border-white/40"></div>
          </div>
          <div className="relative text-white">
            <h2 className="text-3xl font-extrabold mb-2">Join RP-Agentic</h2>
            <p className="text-sm text-emerald-100">Create your account to start professional meal planning.</p>
            <div className="mt-6">
              <img src="/meal-planner.svg" alt="Meal planner decorative" className="w-full rounded-xl shadow-lg ring-1 ring-white/20" />
            </div>
          </div>
        </div>

        {/* Right form panel */}
        <div className="bg-white p-10">
          <h3 className="text-2xl font-bold mb-4 text-slate-900">Create Account</h3>
          <form onSubmit={handleSubmit}>
            {["name","email","phone","password"].map(field => (
              <input
                key={field}
                name={field}
                type={field==="password"?"password":"text"}
                placeholder={field.charAt(0).toUpperCase()+field.slice(1)}
                value={form[field]}
                onChange={handleChange}
                className="border border-slate-300 h-11 px-4 mb-3 w-full rounded-full focus:outline-none focus:ring-2 focus:ring-emerald-500"
                required
              />
            ))}
            <button type="submit" className="bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white w-full py-3 rounded-full font-semibold">Sign Up</button>
          </form>
          <p className="mt-4 text-sm text-slate-600 text-center">
            Already have an account? <span className="text-emerald-700 cursor-pointer" onClick={()=>navigate("/login")}>Login</span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default SignUp;
