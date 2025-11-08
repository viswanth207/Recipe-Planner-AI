import React, { useState } from "react";
import { axiosInstance } from "../api";
import { toast } from "react-toastify";

function IngredientForm({ onUpdate }) {
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unit, setUnit] = useState("");

  const addIngredient = async () => {
    try {
      await axiosInstance.post("/ingredients/", { name, quantity: parseFloat(quantity), unit });
      toast.success("Ingredient added!");
      setName(""); setQuantity(""); setUnit("");
      onUpdate();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Error adding ingredient");
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
<input type="text" placeholder="Ingredient name" value={name} onChange={e => setName(e.target.value)} className="border border-slate-300 h-11 px-3 rounded transition-all duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-emerald-500"/>
<input type="number" placeholder="Quantity" value={quantity} onChange={e => setQuantity(e.target.value)} className="border border-slate-300 h-11 px-3 rounded transition-all duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-emerald-500"/>
<input type="text" placeholder="Unit" value={unit} onChange={e => setUnit(e.target.value)} className="border border-slate-300 h-11 px-3 rounded transition-all duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-emerald-500"/>
<button onClick={addIngredient} className="bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white px-4 py-2 rounded-xl shadow-lg transition-all duration-300 ease-in-out hover:shadow-emerald-300/40">Add</button>
    </div>
  );
}

export default IngredientForm;
