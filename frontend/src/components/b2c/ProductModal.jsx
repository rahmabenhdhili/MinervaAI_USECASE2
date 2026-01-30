import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';

function ProductModal({ product, onClose, onAddToCart }) {
  // Enregistrer le clic lors de l'ouverture
  useEffect(() => {
    if (product && product.id) {
      trackProductClick(product.id);
    }
  }, [product]);

  const trackProductClick = async (productId) => {
    try {
      await fetch(`http://localhost:8000/api/b2c/marketplace/products/${productId}/click`, {
        method: 'POST'
      });
      console.log('✅ Clic enregistré pour le produit:', productId);
    } catch (error) {
      console.error('❌ Erreur tracking clic:', error);
    }
  };

  if (!product) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return createPortal(
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={handleBackdropClick}>
      <div className="bg-white rounded-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-slate-900">{product.name}</h2>
          <button 
            className="text-gray-500 hover:text-gray-700 text-2xl"
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Image */}
          <div className="relative">
            <img 
              src={product.image_url || 'https://via.placeholder.com/400x400'} 
              alt={product.name}
              className="w-full h-64 object-cover rounded-lg"
            />
            {product.clicks > 0 && (
              <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded-full text-xs font-semibold">
                🔥 {product.clicks} {product.clicks === 1 ? 'vue' : 'vues'}
              </div>
            )}
          </div>

          {/* Details */}
          <div className="space-y-4">
            {/* Category */}
            {product.category && (
              <div>
                <span className="bg-dinero-100 text-dinero-700 px-3 py-1 rounded-full text-sm font-semibold">
                  {product.category}
                </span>
              </div>
            )}

            {/* Price */}
            <div className="text-2xl font-bold text-dinero-600">
              ${product.price.toFixed(2)}
            </div>

            {/* Description */}
            <div>
              <h3 className="font-semibold text-slate-900 mb-2">📝 Description</h3>
              <p className="text-slate-600">{product.description || 'Aucune description disponible.'}</p>
            </div>

            {/* Metadata */}
            {product.metadata && (
              <div className="bg-slate-50 rounded-lg p-4">
                <h4 className="font-semibold text-slate-900 mb-2">ℹ️ Informations</h4>
                <div className="space-y-2 text-sm">
                  {product.metadata.original_source && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">Source:</span>
                      <span className="font-medium">{product.metadata.original_source}</span>
                    </div>
                  )}
                  {product.metadata.margin_percentage && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">Marge:</span>
                      <span className="font-medium text-green-600">
                        +{product.metadata.margin_percentage}%
                      </span>
                    </div>
                  )}
                  {product.metadata.original_price && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">Prix d'origine:</span>
                      <span className="font-medium">${product.metadata.original_price.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="pt-4">
              <button 
                className="w-full px-6 py-3 bg-dinero-600 text-white rounded-lg hover:bg-dinero-700 transition-all font-semibold"
                onClick={() => {
                  onAddToCart(product);
                  onClose();
                }}
              >
                🛒 Ajouter au panier
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}

export default ProductModal;