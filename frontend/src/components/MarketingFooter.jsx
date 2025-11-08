import React from "react";

function MarketingFooter() {
  return (
    <footer className="bg-slate-900 text-white">
      {/* Top content: multi-column info */}
      <div className="max-w-6xl mx-auto px-4 py-16 grid gap-8 md:grid-cols-3 lg:grid-cols-5">
        {/* Brand / About */}
        <div>
          <h4 className="text-lg font-semibold">RP-Agentic</h4>
          <p className="mt-2 text-sm text-white/80">
            Your personal AI recipe planner. Plan meals, manage ingredients, and receive daily
            WhatsApp recipes tailored to your preferences.
          </p>
          <p className="mt-3 text-sm text-white/60">Built with React, FastAPI & Tailwind CSS.</p>
        </div>

        {/* Product */}
        <div>
          <h5 className="text-base font-semibold">Product</h5>
          <ul className="mt-3 space-y-2 text-sm">
            <li><a href="#features" className="text-white/80 hover:text-emerald-300 transition-colors">Features</a></li>
            <li><a href="#how" className="text-white/80 hover:text-emerald-300 transition-colors">How It Works</a></li>
            <li><a href="#demo" className="text-white/80 hover:text-emerald-300 transition-colors">Demo</a></li>
            <li><a href="#cta" className="text-white/80 hover:text-emerald-300 transition-colors">Contact</a></li>
          </ul>
        </div>

        {/* Resources */}
        <div>
          <h5 className="text-base font-semibold">Resources</h5>
          <ul className="mt-3 space-y-2 text-sm">
            <li><a href="#" className="text-white/80 hover:text-emerald-300 transition-colors">Documentation</a></li>
            <li><a href="#" className="text-white/80 hover:text-emerald-300 transition-colors">Blog</a></li>
            <li><a href="#" className="text-white/80 hover:text-emerald-300 transition-colors">Support</a></li>
            <li><a href="#" className="text-white/80 hover:text-emerald-300 transition-colors">Status</a></li>
          </ul>
        </div>

        {/* Company */}
        <div>
          <h5 className="text-base font-semibold">Company</h5>
          <ul className="mt-3 space-y-2 text-sm">
            <li><a href="#" className="text-white/80 hover:text-emerald-300 transition-colors">About</a></li>
            <li><a href="#" className="text-white/80 hover:text-emerald-300 transition-colors">Careers</a></li>
            <li><a href="#" className="text-white/80 hover:text-emerald-300 transition-colors">Press</a></li>
            <li><a href="#" className="text-white/80 hover:text-emerald-300 transition-colors">Contact</a></li>
          </ul>
        </div>

        {/* Newsletter */}
        <div className="md:col-span-3 lg:col-span-1">
          <h5 className="text-base font-semibold">Stay in the loop</h5>
          <p className="mt-2 text-sm text-white/80">Subscribe for product updates and tips.</p>
          <form onSubmit={(e) => e.preventDefault()} className="mt-3 flex gap-2">
            <input
              type="email"
              required
              placeholder="Enter your email"
              className="flex-1 rounded-md bg-white/10 text-white placeholder-white/60 border border-white/20 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
            <button
              type="submit"
              className="rounded-md bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2"
            >
              Subscribe
            </button>
          </form>
          <p className="mt-2 text-xs text-white/60">We respect your privacy. Unsubscribe anytime.</p>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-white/10">
        <div className="max-w-6xl mx-auto px-4 py-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-white/80">© {new Date().getFullYear()} RP-Agentic — All rights reserved.</p>
          <div className="flex items-center gap-4 text-sm">
            <a href="#" className="text-white/70 hover:text-white transition-colors">Privacy</a>
            <span className="text-white/30">•</span>
            <a href="#" className="text-white/70 hover:text-white transition-colors">Terms</a>
            <span className="text-white/30">•</span>
            <a href="#" className="text-white/70 hover:text-white transition-colors">Security</a>
          </div>
          <div className="flex items-center gap-4">
            <a href="#" aria-label="LinkedIn" className="text-white/80 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5"><path d="M4.98 3.5C4.98 4.88 3.86 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1s2.48 1.12 2.48 2.5zM.5 7h4V23h-4V7zm7 0h3.8v2.2h.1c.5-.9 1.8-2.2 3.8-2.2 4 0 4.8 2.6 4.8 6V23h-4v-5.4c0-1.3 0-3-1.8-3s-2.1 1.4-2.1 2.9V23h-4V7z"/></svg>
            </a>
            <a href="#" aria-label="GitHub" className="text-white/80 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5"><path d="M12 2C6.48 2 2 6.58 2 12.26c0 4.53 2.87 8.37 6.85 9.73.5.09.68-.22.68-.48 0-.24-.01-.87-.01-1.7-2.79.62-3.38-1.36-3.38-1.36-.46-1.2-1.13-1.52-1.13-1.52-.92-.64.07-.63.07-.63 1.02.07 1.56 1.06 1.56 1.06.9 1.58 2.36 1.12 2.94.85.09-.67.35-1.12.64-1.37-2.23-.26-4.58-1.15-4.58-5.13 0-1.13.39-2.05 1.03-2.78-.1-.26-.45-1.31.1-2.73 0 0 .84-.27 2.75 1.06A9.3 9.3 0 0 1 12 7.07c.85 0 1.71.12 2.51.35 1.9-1.33 2.74-1.06 2.74-1.06.56 1.42.21 2.47.1 2.73.64.73 1.03 1.65 1.03 2.78 0 4-2.36 4.86-4.6 5.12.36.33.69.98.69 1.98 0 1.43-.01 2.58-.01 2.94 0 .26.18.58.69.48A10.03 10.03 0 0 0 22 12.26C22 6.58 17.52 2 12 2Z"/></svg>
            </a>
            <a href="#" aria-label="Twitter" className="text-white/80 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5"><path d="M22.46 6c-.77.35-1.6.58-2.46.69a4.26 4.26 0 0 0 1.87-2.35 8.54 8.54 0 0 1-2.71 1.05A4.25 4.25 0 0 0 12.1 9.2a12.07 12.07 0 0 1-8.77-4.45 4.25 4.25 0 0 0 1.32 5.67c-.67-.02-1.3-.21-1.85-.51v.05a4.25 4.25 0 0 0 3.41 4.17c-.63.17-1.29.2-1.94.07a4.25 4.25 0 0 0 3.97 2.95 8.52 8.52 0 0 1-5.29 1.83c-.35 0-.69-.02-1.03-.06A12.05 12.05 0 0 0 8.16 21c7.31 0 11.31-6.06 11.31-11.31 0-.17 0-.34-.01-.51A8.02 8.02 0 0 0 22.46 6Z"/></svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default MarketingFooter;