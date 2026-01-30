import React, { useState, useEffect } from 'react';
import ProductModal from './ProductModal';

function Shop({ onViewCart, onBack }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cart, setCart] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [settings, setSettings] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);

  useEffect(() => {
    fetchProducts();
    loadCart();
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/b2c/settings');
      const data = await response.json();
      
      if (data.success) {
        setSettings(data.settings);
      }
    } catch (error) {
      console.error('Erreur settings:', error);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/b2c/marketplace/products');
      const data = await response.json();
      
      if (data.success) {
        setProducts(data.products);
      }
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCart = () => {
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
      setCart(JSON.parse(savedCart));
    }
  };

  const saveCart = (newCart) => {
    localStorage.setItem('cart', JSON.stringify(newCart));
    setCart(newCart);
  };

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.id === product.id);
    
    if (existingItem) {
      const newCart = cart.map(item =>
        item.id === product.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      );
      saveCart(newCart);
    } else {
      const newCart = [...cart, { ...product, quantity: 1 }];
      saveCart(newCart);
    }
  };

  const handleProductClick = (product) => {
    setSelectedProduct(product);
  };

  const handleCloseModal = () => {
    setSelectedProduct(null);
  };

  const getCartItemCount = () => {
    return cart.reduce((total, item) => total + item.quantity, 0);
  };

  const categories = ['all', ...new Set(products.map(p => p.category))];
  
  const filteredProducts = products.filter(product => {
    const matchesCategory = selectedCategory === 'all' || product.category === selectedCategory;
    const matchesSearch = product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         product.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-dinero-200 border-t-dinero-600 rounded-full animate-spin"></div>
            <p className="text-slate-600">Chargement de la boutique...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Logo de la marketplace */}
          {settings?.marketplace_logo && (
            <img 
              src={settings.marketplace_logo} 
              alt="Logo" 
              className="h-12 w-auto rounded-lg object-contain"
            />
          )}
          {onBack && (
            <button 
              className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-all"
              onClick={onBack}
            >
              ← Dashboard
            </button>
          )}
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              🛍️ {settings?.marketplace_name || 'Boutique'}
            </h1>
            <p className="text-slate-600">{settings?.marketplace_description || 'Découvrez nos produits sélectionnés'}</p>
          </div>
        </div>
        
        <button 
          className="px-4 py-2 bg-dinero-600 text-white rounded-lg hover:bg-dinero-700 transition-all relative"
          onClick={onViewCart}
        >
          🛒 Panier
          {getCartItemCount() > 0 && (
            <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {getCartItemCount()}
            </span>
          )}
        </button>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="🔍 Rechercher un produit..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none"
            />
          </div>
          
          <div className="flex flex-wrap gap-2">
            {categories.map(category => (
              <button
                key={category}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedCategory === category
                    ? 'bg-dinero-600 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
                onClick={() => setSelectedCategory(category)}
              >
                {category === 'all' ? '🏷️ Tous' : category}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Products Grid */}
      {filteredProducts.length === 0 ? (
        <div className="bg-white rounded-xl shadow-md border border-slate-200 p-12 text-center">
          <div className="text-6xl mb-4">📦</div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Aucun produit trouvé</h2>
          <p className="text-slate-600">Essayez une autre recherche ou catégorie</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredProducts.map((product) => (
            <div 
              key={product.id} 
              className="bg-white rounded-xl shadow-md border border-slate-200 p-4 hover:shadow-lg transition-all cursor-pointer"
              onClick={() => handleProductClick(product)}
            >
              <div className="relative mb-3">
                <img 
                  src={product.image_url || 'https://via.placeholder.com/300x300'} 
                  alt={product.name}
                  className="w-full h-48 object-cover rounded-lg"
                />
                <div className="absolute top-2 right-2 bg-dinero-100 text-dinero-700 px-2 py-1 rounded-full text-xs font-semibold">
                  {product.category}
                </div>
              </div>
              
              <div className="space-y-2">
                <h3 className="font-bold text-slate-900 line-clamp-2">{product.name}</h3>
                <p className="text-sm text-slate-600 line-clamp-2">{product.description}</p>
                
                <div className="flex items-center justify-between">
                  <div className="text-lg font-bold text-dinero-600">${product.price.toFixed(2)}</div>
                  <div className="text-xs text-slate-500">👁️ Cliquez pour voir les détails</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Product Modal */}
      {selectedProduct && (
        <ProductModal
          product={selectedProduct}
          onClose={handleCloseModal}
          onAddToCart={addToCart}
        />
      )}
    </div>
  );
}

export default Shop;