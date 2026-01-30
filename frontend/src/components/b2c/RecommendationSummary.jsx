import React from 'react';

function RecommendationSummary({ summary, intent, totalFound }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          🎯 Recommandations
        </h2>
        <span className="text-sm bg-dinero-100 text-dinero-700 px-3 py-1 rounded-full font-semibold">
          {totalFound} produits trouvés
        </span>
      </div>

      {intent && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">Intention détectée:</h4>
          <div className="space-y-2">
            {intent.product_type && (
              <div className="flex items-center gap-2">
                <span className="text-blue-700 font-medium">Type:</span>
                <span className="text-blue-800">{intent.product_type}</span>
              </div>
            )}
            {intent.usage && (
              <div className="flex items-center gap-2">
                <span className="text-blue-700 font-medium">Usage:</span>
                <span className="text-blue-800">{intent.usage}</span>
              </div>
            )}
            {intent.budget_range && (
              <div className="flex items-center gap-2">
                <span className="text-blue-700 font-medium">Budget:</span>
                <span className="text-blue-800">{intent.budget_range}</span>
              </div>
            )}
            {intent.key_features && intent.key_features.length > 0 && (
              <div>
                <span className="text-blue-700 font-medium">Caractéristiques clés:</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {intent.key_features.map((feature, index) => (
                    <span key={index} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {summary && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-semibold text-green-900 mb-2">Résumé des résultats:</h4>
          <p className="text-green-800">{summary}</p>
        </div>
      )}
    </div>
  );
}

export default RecommendationSummary;