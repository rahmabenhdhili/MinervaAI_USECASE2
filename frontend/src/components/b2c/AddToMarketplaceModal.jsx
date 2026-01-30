import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';

function AddToMarketplaceModal({ isOpen, onClose, product }) {
  // État local du formulaire - initialisé une seule fois
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    image_url: '',
    category: 'general'
  });
  
  const [marginPercentage, setMarginPercentage] = useState(30);
  const [manualPrice, setManualPrice] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialiser le formulaire quand le produit change
  useEffect(() => {
    if (product && isOpen) {
      setFormData({
        name: product.name || '',
        description: product.description || product.name || '',
        image_url: product.image_url || '',
        category: product.category || 'general'
      });
      setMarginPercentage(30);
      setManualPrice('');
    }
  }, [product, isOpen]);

  // Handler mémorisé pour les changements de formulaire
  const handleFormChange = useCallback((field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  // Handler mémorisé pour la marge
  const handleMarginChange = useCallback((value) => {
    setMarginPercentage(value);
    if (manualPrice) setManualPrice('');
  }, [manualPrice]);

  // Handler mémorisé pour le prix manuel
  const handleManualPriceChange = useCallback((value) => {
    setManualPrice(value);
  }, []);

  // Calculs mémorisés
  const priceCalculations = useMemo(() => {
    if (!product) return { newPrice: 0, marginAmount: 0, calculatedMarginPercentage: '0.0' };
    
    const originalPrice = parseFloat(product.price) || 0;
    let newPrice;
    
    if (manualPrice && parseFloat(manualPrice) > 0) {
      newPrice = parseFloat(manualPrice);
    } else {
      const margin = parseFloat(marginPercentage) || 0;
      newPrice = originalPrice * (1 + margin / 100);
    }
    
    const marginAmount = newPrice - originalPrice;
    const calculatedMarginPercentage = originalPrice > 0 
      ? ((marginAmount / originalPrice) * 100).toFixed(1)
      : '0.0';
    
    return { newPrice, marginAmount, calculatedMarginPercentage };
  }, [product, marginPercentage, manualPrice]);

  // Handler de soumission mémorisé
  const handleSubmit = useCallback(async () => {
    if (!product || isSubmitting) return;
    
    setIsSubmitting(true);

    try {
      const response = await fetch('http://localhost:8000/api/b2c/marketplace/products', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description,
          price: priceCalculations.newPrice,
          image_url: formData.image_url,
          category: formData.category,
          metadata: {
            original_source: product.metadata?.source || 'unknown',
            original_url: product.url,
            original_price: parseFloat(product.price),
            margin_percentage: parseFloat(priceCalculations.calculatedMarginPercentage),
            margin_amount: priceCalculations.marginAmount,
            added_at: new Date().toISOString()
          }
        })
      });

      const data = await response.json();
      
      if (data.success) {
        alert('✅ Produit ajouté à votre marketplace avec succès!');
        onClose();
      } else {
        alert('❌ Erreur lors de l\'ajout du produit.');
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('❌ Erreur de connexion au serveur.');
    } finally {
      setIsSubmitting(false);
    }
  }, [product, formData, priceCalculations, isSubmitting, onClose]);

  // Ne rien rendre si pas ouvert
  if (!isOpen || !product) return null;

  const { newPrice, marginAmount, calculatedMarginPercentage } = priceCalculations;

  return createPortal(
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">🛒 Ajouter à la Marketplace</h2>
          <button 
            className="text-gray-500 hover:text-gray-700 text-2xl"
            onClick={onClose}
            type="button"
          >
            ✕
          </button>
        </div>
        
        <div className="space-y-6">
          <p className="text-gray-600">
            Personnalisez ce produit avant de l'ajouter à votre boutique e-commerce
          </p>

          {/* Calculateur de prix et marge */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-4">💰 Calculateur de Prix et Marge</h3>
            
            <div className="flex items-center gap-4 mb-4">
              <div className="bg-white rounded-lg p-3 flex-1">
                <label className="text-sm text-gray-600">Prix d'origine</label>
                <div className="text-xl font-bold text-gray-800">${product.price.toFixed(2)}</div>
              </div>
              
              <div className="text-2xl text-gray-400">→</div>
              
              <div className="bg-white rounded-lg p-3 flex-1">
                <label className="text-sm text-gray-600">Nouveau prix</label>
                <div className="text-xl font-bold text-dinero-600">${newPrice.toFixed(2)}</div>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">📊 Marge bénéficiaire (%)</label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="0"
                  max="200"
                  step="5"
                  value={marginPercentage}
                  onChange={(e) => handleMarginChange(e.target.value)}
                  className="flex-1"
                  disabled={!!manualPrice}
                />
                <input
                  type="number"
                  min="0"
                  max="500"
                  step="1"
                  value={marginPercentage}
                  onChange={(e) => handleMarginChange(e.target.value)}
                  className="w-20 px-2 py-1 border border-gray-300 rounded"
                  disabled={!!manualPrice}
                />
                <span className="text-sm text-gray-600">%</span>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">💵 Ou entrez un prix manuel</label>
              <div className="flex items-center gap-2">
                <span className="text-gray-600">$</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={manualPrice}
                  onChange={(e) => handleManualPriceChange(e.target.value)}
                  placeholder={`Ex: ${(parseFloat(product.price) * 1.5).toFixed(2)}`}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                />
                {manualPrice && (
                  <button
                    type="button"
                    className="text-red-500 hover:text-red-700"
                    onClick={() => setManualPrice('')}
                    title="Revenir au calcul par marge"
                  >
                    ✕
                  </button>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {manualPrice ? '✓ Prix manuel actif' : 'Laissez vide pour utiliser le calcul par marge'}
              </p>
            </div>

            <div className="bg-green-50 rounded-lg p-3">
              <div className="flex justify-between items-center">
                <span className="text-green-700 font-medium">Marge en $:</span>
                <span className="text-green-800 font-bold">+${marginAmount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-green-700 font-medium">Marge en %:</span>
                <span className="text-green-800 font-bold">{calculatedMarginPercentage}%</span>
              </div>
            </div>
          </div>

          {/* Image du produit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">📸 Image du produit</label>
            <div className="mb-2">
              <img 
                src={formData.image_url || 'https://via.placeholder.com/300x200'} 
                alt="Preview"
                className="w-32 h-24 object-cover rounded-lg border"
              />
            </div>
            <input
              type="text"
              value={formData.image_url}
              onChange={(e) => handleFormChange('image_url', e.target.value)}
              placeholder="URL de l'image"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          
          {/* Nom du produit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">📦 Nom du produit</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleFormChange('name', e.target.value)}
              placeholder="Nom du produit"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          
          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">📝 Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => handleFormChange('description', e.target.value)}
              placeholder="Description du produit"
              rows="4"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          
          {/* Catégorie */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">🏷️ Catégorie</label>
            <select
              value={formData.category}
              onChange={(e) => handleFormChange('category', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="general">Général</option>
              <option value="electronics">Électronique</option>
              <option value="clothing">Vêtements</option>
              <option value="home">Maison</option>
              <option value="sports">Sports</option>
              <option value="books">Livres</option>
              <option value="toys">Jouets</option>
              <option value="beauty">Beauté</option>
            </select>
          </div>
          
          {/* Actions */}
          <div className="flex gap-4 pt-4">
            <button 
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all"
              onClick={onClose}
              disabled={isSubmitting}
              type="button"
            >
              Annuler
            </button>
            <button 
              className="flex-1 px-4 py-2 bg-dinero-600 text-white rounded-lg hover:bg-dinero-700 disabled:opacity-50 transition-all"
              onClick={handleSubmit}
              disabled={isSubmitting}
              type="button"
            >
              {isSubmitting ? (
                <>
                  <div className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Ajout en cours...
                </>
              ) : (
                <>
                  ✅ Ajouter à la Marketplace
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}

export default AddToMarketplaceModal;