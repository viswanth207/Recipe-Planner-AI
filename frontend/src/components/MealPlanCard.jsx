import React from "react";

function MealPlanCard({ plan }) {
  return (
    <div className="mt-6">
      <h2 className="text-2xl font-bold mb-3">Your RP-Agentic Meal Plan</h2>
      <div className="grid sm:grid-cols-3 gap-4">
        {["breakfast", "lunch", "dinner"].map(meal => (
          <div key={meal} className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
            <h3 className="font-bold capitalize text-slate-900">{meal}</h3>
            <p className="text-slate-700">{plan[meal]?.recipe_name}</p>
            <a href={plan[meal]?.youtube_link} target="_blank" rel="noreferrer" className="text-emerald-700 hover:text-emerald-800 underline">
              Watch Video
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}

export default MealPlanCard;
