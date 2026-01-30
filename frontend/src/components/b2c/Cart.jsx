import React, { useState, useEffect } from 'react';

function Cart({ onBack, onOrderComplete }) {
  const [cart, setCart] = useState([]);
  const [showCheckout, setShowCheckout] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Form data - Simplifié
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_phone: '',
    street: '',
    city: '',
    zip_code: '',
    country: 'USA',
    payment_method: 'card'
  });

  useEffect(() => {
    loadCart();
  }, []);

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

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity < 1) {
      removeItem(productId);
      return;
    }
    
    const newCart = cart.map(item =>
      item.id === productId ? { ...item, quantity: newQuantity } : item
    );
    saveCart(newCart);
  };

  const removeItem = (productId) => {
    const newCart = cart.filter(item => item.id !== productId);
    saveCart(newCart);
  };

  const getTotal = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmitOrder = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const orderData = {
        customer_name: formData.customer_name,
        customer_phone: formData.customer_phone,
        shipping_address: {
          street: formData.street,
          city: formData.city,
          zip_code: formData.zip_code,
          country: formData.country
        },
        items: cart.map(item => ({
          product_id: item.id,
          product_name: item.name,
          product_image: item.image_url,
          price: item.price,
          cost: item.cost || item.price,  // Inclure le coût
          quantity: item.quantity
        })),
        payment_method: formData.payment_method
      };

      const response = await fetch('http://localhost:8000/api/b2c/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
      });

      const data = await response.json();
      
      if (data.success) {
        // Clear cart
        localStorage.removeItem('cart');
        setCart([]);
        
        // Show success and order number
        alert(`✅ Commande créée avec succès!\n\nNuméro de commande: ${data.order.order_number}\n\nMerci pour votre achat!`);
        
        if (onOrderComplete) {
          onOrderComplete(data.order);
        }
      } else {
        alert('❌ Erreur lors de la création de la commande.');
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('❌ Erreur de connexion au serveur.');
    } finally {
      setLoading(false);
    }
  };

  if (cart.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <button 
            className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-all"
            onClick={onBack}
          >
            ← Retour à la boutique
          </button>
        </div>
        
        <div className="bg-white rounded-xl shadow-md border border-slate-200 p-12 text-center">
          <div className="text-6xl mb-4">🛒</div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Votre panier est vide</h2>
          <p className="text-slate-600 mb-6">Ajoutez des produits pour commencer vos achats</p>
          <button 
            className="px-6 py-3 bg-dinero-600 text-white rounded-lg hover:bg-dinero-700 transition-all font-semibold"
            onClick={onBack}
          >
            Continuer mes achats
          </button>
        </div>
      </div>
    );
  }

  if (showCheckout) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <button 
            className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-all"
            onClick={() => setShowCheckout(false)}
          >
            ← Retour au panier
          </button>
          <h1 className="text-2xl font-bold text-slate-900">💳 Paiement</h1>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <form className="bg-white rounded-xl shadow-md border border-slate-200 p-6 space-y-6" onSubmit={handleSubmitOrder}>
              <div>
                <h3 className="text-lg font-semibold text-slate-900 mb-4">📋 Informations personnelles</h3>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Nom complet *</label>
                    <input
                      type="text"
                      required
                      value={formData.customer_name}
                      onChange={(e) => handleInputChange('customer_name', e.target.value)}
                      placeholder="John Doe"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Téléphone *</label>
                    <input
                      type="tel"
                      required
                      value={formData.customer_phone}
                      onChange={(e) => handleInputChange('customer_phone', e.target.value)}
                      placeholder="+1 234 567 8900"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none"
                    />
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-slate-900 mb-4">📦 Adresse de livraison</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Adresse *</label>
                    <input
                      type="text"
                      required
                      value={formData.street}
                      onChange={(e) => handleInputChange('street', e.target.value)}
                      placeholder="123 Main Street"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none"
                    />
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">Ville *</label>
                      <input
                        type="text"
                        required
                        value={formData.city}
                        onChange={(e) => handleInputChange('city', e.target.value)}
                        placeholder="New York"
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">Code postal *</label>
                      <input
                        type="text"
                        required
                        value={formData.zip_code}
                        onChange={(e) => handleInputChange('zip_code', e.target.value)}
                        placeholder="10001"
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Pays *</label>
                    <select
                      value={formData.country}
                      onChange={(e) => handleInputChange('country', e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none"
                    >
                      <option value="USA">États-Unis</option>
                      <option value="Canada">Canada</option>
                      <option value="France">France</option>
                      <option value="UK">Royaume-Uni</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-slate-900 mb-4">💳 Méthode de paiement</h3>
                
                <div className="space-y-2">
                  <label className="flex items-center gap-3 p-3 border border-slate-300 rounded-lg cursor-pointer hover:bg-slate-50">
                    <input
                      type="radio"
                      name="payment"
                      value="card"
                      checked={formData.payment_method === 'card'}
                      onChange={(e) => handleInputChange('payment_method', e.target.value)}
                      className="text-dinero-600"
                    />
                    <span>💳 Carte bancaire</span>
                  </label>
                  
                  <label className="flex items-center gap-3 p-3 border border-slate-300 rounded-lg cursor-pointer hover:bg-slate-50">
                    <input
                      type="radio"
                      name="payment"
                      value="paypal"
                      checked={formData.payment_method === 'paypal'}
                      onChange={(e) => handleInputChange('payment_method', e.target.value)}
                      className="text-dinero-600"
                    />
                    <span>🅿️ PayPal</span>
                  </label>
                </div>
              </div>

              <button 
                type="submit" 
                className="w-full px-6 py-3 bg-dinero-600 text-white rounded-lg hover:bg-dinero-700 disabled:opacity-50 transition-all font-semibold"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Traitement en cours...
                  </>
                ) : (
                  <>
                    ✅ Confirmer la commande (${getTotal().toFixed(2)})
                  </>
                )}
              </button>
            </form>
          </div>

          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 sticky top-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">📋 Résumé de la commande</h3>
              
              <div className="space-y-3 mb-4">
                {cart.map(item => (
                  <div key={item.id} className="flex items-center gap-3">
                    <img 
                      src={item.image_url} 
                      alt={item.name} 
                      className="w-12 h-12 object-cover rounded-lg"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{item.name}</p>
                      <p className="text-xs text-slate-600">Qté: {item.quantity}</p>
                    </div>
                    <p className="font-semibold">${(item.price * item.quantity).toFixed(2)}</p>
                  </div>
                ))}
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between items-center text-lg font-bold">
                  <span>Total</span>
                  <span className="text-dinero-600">${getTotal().toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button 
          className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-all"
          onClick={onBack}
        >
          ← Retour à la boutique
        </button>
        <h1 className="text-2xl font-bold text-slate-900">
          🛒 Mon Panier ({cart.length} {cart.length > 1 ? 'articles' : 'article'})
        </h1>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          {cart.map(item => (
            <div key={item.id} className="bg-white rounded-xl shadow-md border border-slate-200 p-4">
              <div className="flex items-center gap-4">
                <img 
                  src={item.image_url} 
                  alt={item.name} 
                  className="w-20 h-20 object-cover rounded-lg"
                />
                
                <div className="flex-1">
                  <h3 className="font-semibold text-slate-900">{item.name}</h3>
                  <p className="text-dinero-600 font-bold">${item.price.toFixed(2)}</p>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <button 
                      className="w-8 h-8 bg-slate-100 hover:bg-slate-200 rounded-full flex items-center justify-center"
                      onClick={() => updateQuantity(item.id, item.quantity - 1)}
                    >
                      −
                    </button>
                    <span className="w-8 text-center font-semibold">{item.quantity}</span>
                    <button 
                      className="w-8 h-8 bg-slate-100 hover:bg-slate-200 rounded-full flex items-center justify-center"
                      onClick={() => updateQuantity(item.id, item.quantity + 1)}
                    >
                      +
                    </button>
                  </div>
                  
                  <button 
                    className="text-red-500 hover:text-red-700 p-2"
                    onClick={() => removeItem(item.id)}
                  >
                    🗑️
                  </button>
                </div>
                
                <div className="text-right">
                  <div className="font-bold text-lg">
                    ${(item.price * item.quantity).toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 sticky top-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Résumé</h3>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between">
                <span>Sous-total</span>
                <span>${getTotal().toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Livraison</span>
                <span>Gratuite</span>
              </div>
            </div>
            
            <div className="border-t pt-4 mb-6">
              <div className="flex justify-between items-center text-lg font-bold">
                <span>Total</span>
                <span className="text-dinero-600">${getTotal().toFixed(2)}</span>
              </div>
            </div>
            
            <button 
              className="w-full px-6 py-3 bg-dinero-600 text-white rounded-lg hover:bg-dinero-700 transition-all font-semibold"
              onClick={() => setShowCheckout(true)}
            >
              Procéder au paiement →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Cart;