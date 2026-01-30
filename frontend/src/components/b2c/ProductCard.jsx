import { useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import AddToMarketplaceModal from './AddToMarketplaceModal';

function ProductCard({ product, score, rank }) {
  const [showMenu, setShowMenu] = useState(false);
  const [showStrategy, setShowStrategy] = useState(false);
  const [showAddToMarketplace, setShowAddToMarketplace] = useState(false);
  const [strategy, setStrategy] = useState(null);
  const [loadingStrategy, setLoadingStrategy] = useState(false);
  
  const scorePercentage = (score * 100).toFixed(1);
  
  const getScoreColor = (score) => {
    if (score >= 0.8) return '#4caf50';
    if (score >= 0.6) return '#ff9800';
    return '#f44336';
  };

  const handleGenerateStrategy = async () => {
    setShowMenu(false);
    setLoadingStrategy(true);
    setShowStrategy(true);

    try {
      const response = await fetch('http://localhost:8000/api/b2c/marketing', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_name: product.name,
          product_description: product.description || product.name
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setStrategy(data.strategy);
      } else {
        setStrategy('❌ Erreur lors de la génération de la stratégie.');
      }
    } catch (error) {
      console.error('Erreur:', error);
      setStrategy('❌ Erreur de connexion au serveur.');
    } finally {
      setLoadingStrategy(false);
    }
  };

  const handleAddToMarketplace = useCallback(() => {
    setShowMenu(false);
    setShowAddToMarketplace(true);
  }, []);

  const handleCloseMarketplace = useCallback(() => {
    setShowAddToMarketplace(false);
  }, []);

  // Déterminer la source du produit
  const source = product.source || product.metadata?.source || 'unknown';
  console.log('Product source debug:', { 
    directSource: product.source, 
    metadataSource: product.metadata?.source, 
    finalSource: source,
    productData: product 
  });
  const getSourceBadge = () => {
    switch(source) {
      case 'amazon':
        return { emoji: '🛒', text: 'Amazon', color: '#FF9900' };
      case 'alibaba':
        return { emoji: '🏭', text: 'Alibaba', color: '#FF6A00' };
      case 'walmart':
        return { emoji: '🛍️', text: 'Walmart', color: '#0071CE' };
      case 'cdiscount':
        return { emoji: '🛒', text: 'Cdiscount', color: '#E4032E' };
      default:
        return { emoji: '📦', text: 'Unknown', color: '#666' };
    }
  };

  const sourceBadge = getSourceBadge();

  // Composant Modal Strategy
  const StrategyModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowStrategy(false)}>
      <div className="bg-white rounded-2xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">📊 Stratégie Marketing</h2>
          <button 
            className="text-gray-500 hover:text-gray-700 text-2xl"
            onClick={() => setShowStrategy(false)}
          >
            ✕
          </button>
        </div>
        
        <div className="mb-4">
          <h3 className="font-semibold">{product.name}</h3>
          <p className="text-dinero-600 font-bold">${product.price.toFixed(2)}</p>
        </div>
        
        <div className="border-t pt-4">
          {loadingStrategy ? (
            <div className="flex flex-col items-center py-8">
              <div className="w-8 h-8 border-4 border-dinero-200 border-t-dinero-600 rounded-full animate-spin mb-4"></div>
              <p>Génération de la stratégie marketing...</p>
            </div>
          ) : (
            <div className="whitespace-pre-wrap text-sm">
              {strategy ? strategy : 'Aucune stratégie disponible.'}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <>
      <div className="bg-white rounded-xl shadow-md border border-slate-200 p-4 hover:shadow-lg transition-all relative">
        <div className="absolute top-2 left-2 bg-dinero-100 text-dinero-700 px-2 py-1 rounded-full text-xs font-semibold">
          #{rank}
        </div>
        
        {/* Menu 3 points */}
        <div className="absolute top-2 right-2">
          <button 
            className="text-gray-500 hover:text-gray-700 p-1"
            onClick={() => setShowMenu(!showMenu)}
            aria-label="Options"
          >
            ⋮
          </button>
          
          {showMenu && (
            <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-48">
              <button 
                className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm"
                onClick={handleGenerateStrategy}
              >
                📊 Stratégie Marketing
              </button>
              <button 
                className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm"
                onClick={handleAddToMarketplace}
              >
                🛒 Ajouter à la Marketplace
              </button>
            </div>
          )}
        </div>
        
        {/* Badge de source */}
        <div 
          className="absolute top-2 left-16 text-white px-2 py-1 rounded-full text-xs font-semibold"
          style={{ backgroundColor: sourceBadge.color }}
        >
          {sourceBadge.emoji} {sourceBadge.text}
        </div>
        
        <div className="mt-8 mb-3">
          <img 
            src={product.image_url || 'https://via.placeholder.com/300x200?text=No+Image'} 
            alt={product.name}
            className="w-full h-32 object-cover rounded-lg"
          />
        </div>

        <div className="space-y-3">
          <h3 className="font-bold text-slate-900 line-clamp-2">{product.name}</h3>
          
          <p className="text-sm text-slate-600 line-clamp-3">{product.description}</p>

          <div className="flex items-center gap-2 text-xs">
            {product.rating && (
              <div className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                ⭐ {product.rating.toFixed(1)}
              </div>
            )}
            {product.category && (
              <div className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                📦 {product.category}
              </div>
            )}
          </div>

          <div className="flex items-center justify-between">
            <div className="text-lg font-bold text-dinero-600">${product.price.toFixed(2)}</div>
            
            <div 
              className="text-white px-2 py-1 rounded-full text-xs font-semibold"
              style={{ backgroundColor: getScoreColor(score) }}
            >
              {scorePercentage}% match
            </div>
          </div>

          {product.url && (
            <a 
              href={product.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="block w-full text-center px-4 py-2 bg-dinero-50 text-dinero-600 rounded-lg hover:bg-dinero-100 transition-all text-sm font-semibold"
            >
              Voir le produit →
            </a>
          )}
        </div>
      </div>
      
      {/* Modals */}
      {showStrategy && createPortal(<StrategyModal />, document.body)}
      <AddToMarketplaceModal 
        isOpen={showAddToMarketplace}
        onClose={handleCloseMarketplace}
        product={product}
      />
    </>
  );
}

export default ProductCard;