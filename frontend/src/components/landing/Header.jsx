import React from "react"

function Header({ onGetStarted }) {
  return (
    <header className="flex justify-between items-center py-5 px-8 glass-effect max-w-7xl mx-auto rounded-2xl mt-4 shadow-lg">
      <div className="flex items-center group cursor-pointer">
        <img 
          src="/dinero.png" 
          alt="Dinero Logo" 
          className="h-16 w-auto rounded-xl object-contain group-hover:scale-105 transition-transform shadow-lg"
        />
      </div>
      
      <nav className="hidden md:flex gap-10 font-semibold" style={{ color: 'var(--viridian)' }}>
        <a href="#features" className="hover:opacity-80 smooth-transition">Features</a>
        <a href="#how-it-works" className="hover:opacity-80 smooth-transition">How It Works</a>
        <a href="#markets" className="hover:opacity-80 smooth-transition">Markets</a>
      </nav>
      
      <div className="flex items-center gap-6">
        <button
          onClick={onGetStarted}
          className="gradient-primary text-white px-8 py-3 rounded-full font-bold shadow-lg hover:shadow-xl hover:-translate-y-0.5 smooth-transition flex items-center gap-2"
        >
          Try Now <span>→</span>
        </button>
      </div>
    </header>
  )
}

export default Header
