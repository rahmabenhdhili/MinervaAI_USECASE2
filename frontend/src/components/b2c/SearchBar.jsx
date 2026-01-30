import React from 'react';

function SearchBar({ value, onChange, onSearch, disabled }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(value);
  };

  return (
    <form className="flex gap-4" onSubmit={handleSubmit}>
      <input
        type="text"
        className="flex-1 px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all"
        placeholder="Ex: Je cherche un laptop gaming avec RTX 4060 pour moins de 1500€"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      />
      <button 
        type="submit" 
        className="px-6 py-3 bg-dinero-600 text-white rounded-xl font-semibold hover:bg-dinero-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        disabled={disabled || !value.trim()}
      >
        🔍 Rechercher
      </button>
    </form>
  );
}

export default SearchBar;