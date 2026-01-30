import React from 'react';

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-dinero-200 border-t-dinero-600 rounded-full animate-spin"></div>
        <div className="text-center">
          <p className="text-slate-600 font-medium mb-2">Recherche en cours...</p>
          <div className="space-y-1 text-sm text-slate-500">
            <div>🧠 Analyse de votre requête...</div>
            <div>🌐 Collection des produits...</div>
            <div>🔍 Recherche sémantique...</div>
            <div>✨ Génération des recommandations...</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoadingSpinner;