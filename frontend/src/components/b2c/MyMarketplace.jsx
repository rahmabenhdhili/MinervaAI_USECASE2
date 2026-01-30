import React, { useState, useEffect, useCallback } from 'react';

function MyMarketplace() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [orders, setOrders] = useState([]);
  const [orderStats, setOrderStats] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // overview, products, orders, settings
  const [settings, setSettings] = useState(null);
  const [settingsForm, setSettingsForm] = useState({
    marketplace_name: '',
    marketplace_logo: '',
    marketplace_description: ''
  });

  useEffect(() => {
    fetchProducts();
    fetchStats();
    fetchOrders();
    fetchOrderStats();
    fetchSettings();
  }, []);

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

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/b2c/marketplace/stats');
      const data = await response.json();
      
      if (data.success) {
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Erreur stats:', error);
    }
  };

  const fetchOrderStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/b2c/orders/stats');
      const data = await response.json();
      
      if (data.success) {
        setOrderStats(data.stats);
      }
    } catch (error) {
      console.error('Erreur order stats:', error);
    }
  };

  const fetchSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/b2c/settings');
      const data = await response.json();
      
      if (data.success) {
        setSettings(data.settings);
        setSettingsForm({
          marketplace_name: data.settings.marketplace_name,
          marketplace_logo: data.settings.marketplace_logo,
          marketplace_description: data.settings.marketplace_description
        });
      }
    } catch (error) {
      console.error('Erreur settings:', error);
    }
  };

  // Fonction optimisée pour mettre à jour les champs du formulaire
  const handleSettingsChange = useCallback((field, value) => {
    setSettingsForm(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  const handleUpdateSettings = async () => {
    try {
      console.log('📤 Envoi des paramètres:', settingsForm);
      
      const response = await fetch('http://localhost:8000/api/b2c/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settingsForm)
      });
      
      console.log('📥 Réponse status:', response.status);
      const data = await response.json();
      console.log('📥 Réponse data:', data);
      
      if (data.success) {
        setSettings(data.settings);
        alert('✅ Paramètres mis à jour avec succès!');
        // Recharger pour mettre à jour le header
        await fetchSettings();
      } else {
        alert('❌ Erreur: ' + (data.error || 'Erreur inconnue'));
      }
    } catch (error) {
      console.error('❌ Erreur complète:', error);
      alert('❌ Erreur lors de la mise à jour: ' + error.message);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/b2c/orders');
      const data = await response.json();
      
      if (data.success) {
        setOrders(data.orders);
      }
    } catch (error) {
      console.error('Erreur orders:', error);
    }
  };

  const handleDelete = async (productId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce produit?')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/b2c/marketplace/products/${productId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      
      if (data.success) {
        setProducts(products.filter(p => p.id !== productId));
        fetchStats();
        fetchOrders();
        fetchOrderStats();
        alert('✅ Produit supprimé avec succès!');
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('❌ Erreur lors de la suppression.');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { text: 'En attente', color: '#ff9800', icon: '⏳' },
      confirmed: { text: 'Confirmée', color: '#2196F3', icon: '✅' },
      shipped: { text: 'Expédiée', color: '#9c27b0', icon: '🚚' },
      delivered: { text: 'Livrée', color: '#4caf50', icon: '📦' },
      cancelled: { text: 'Annulée', color: '#f44336', icon: '❌' }
    };
    return badges[status] || badges.pending;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-dinero-200 border-t-dinero-600 rounded-full animate-spin"></div>
            <p className="text-slate-600">Chargement de votre dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6">
        <div className="flex items-center gap-4">
          {settings?.marketplace_logo && (
            <img 
              src={settings.marketplace_logo} 
              alt="Logo" 
              className="h-16 w-auto rounded-lg object-contain"
            />
          )}
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              📊 {settings?.marketplace_name || 'Dashboard Vendeur'}
            </h1>
            <p className="text-slate-600">
              {settings?.marketplace_description || 'Gérez votre marketplace et suivez vos performances'}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-xl shadow-md border border-slate-200 p-2">
        <div className="flex flex-wrap gap-2">
          <button 
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
              activeTab === 'overview' 
                ? 'bg-dinero-600 text-white' 
                : 'text-slate-700 hover:bg-slate-100'
            }`}
            onClick={() => setActiveTab('overview')}
          >
            <span>📈</span>
            Vue d'ensemble
          </button>
          <button 
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
              activeTab === 'products' 
                ? 'bg-dinero-600 text-white' 
                : 'text-slate-700 hover:bg-slate-100'
            }`}
            onClick={() => setActiveTab('products')}
          >
            <span>📦</span>
            Mes Produits ({products.length})
          </button>
          <button 
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
              activeTab === 'orders' 
                ? 'bg-dinero-600 text-white' 
                : 'text-slate-700 hover:bg-slate-100'
            }`}
            onClick={() => setActiveTab('orders')}
          >
            <span>🛍️</span>
            Commandes ({orders.length})
          </button>
          <button 
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
              activeTab === 'settings' 
                ? 'bg-dinero-600 text-white' 
                : 'text-slate-700 hover:bg-slate-100'
            }`}
            onClick={() => setActiveTab('settings')}
          >
            <span>⚙️</span>
            Paramètres
          </button>
        </div>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100">Revenu Réalisé</p>
                  <p className="text-2xl font-bold">${orderStats?.total_revenue?.toFixed(2) || '0.00'}</p>
                  <p className="text-sm text-green-100">Bénéfice: ${orderStats?.total_profit?.toFixed(2) || '0.00'}</p>
                </div>
                <div className="text-3xl">💰</div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100">Commandes Livrées</p>
                  <p className="text-2xl font-bold">{orderStats?.total_orders || 0}</p>
                  <p className="text-sm text-blue-100">Marge: {orderStats?.profit_margin?.toFixed(1) || '0'}%</p>
                </div>
                <div className="text-3xl">🛍️</div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100">Produits Actifs</p>
                  <p className="text-2xl font-bold">{stats?.total_products || 0}</p>
                  <p className="text-sm text-purple-100">Catalogue: ${stats?.total_value?.toFixed(2) || '0.00'}</p>
                </div>
                <div className="text-3xl">📦</div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-100">Engagement</p>
                  <p className="text-2xl font-bold">{stats?.total_clicks || 0}</p>
                  <p className="text-sm text-orange-100">{stats?.total_views || 0} vues</p>
                </div>
                <div className="text-3xl">👆</div>
              </div>
            </div>
          </div>

          {/* Message d'aide si pas de revenus */}
          {(!orderStats || orderStats.total_revenue === 0) && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className="text-2xl">💡</div>
                <div>
                  <h3 className="font-semibold text-blue-900 mb-2">Comment générer des revenus?</h3>
                  <p className="text-blue-800">
                    Les revenus sont calculés à partir des commandes passées par vos clients dans la boutique. 
                    Ajoutez des produits à votre marketplace et partagez le lien de votre boutique pour commencer à vendre!
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Charts Section */}
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Recent Orders */}
            <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">📋 Commandes Récentes</h3>
              <div className="space-y-3">
                {orders.slice(0, 5).map((order) => (
                  <div key={order.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div>
                      <div className="font-medium">{order.order_number}</div>
                      <div className="text-sm text-slate-600">{order.customer.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">${order.pricing?.total?.toFixed(2) || '0.00'}</div>
                      <div className="text-sm text-green-600">
                        💰 +${order.pricing?.profit?.toFixed(2) || '0.00'}
                      </div>
                    </div>
                  </div>
                ))}
                {orders.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    <p>Aucune commande pour le moment</p>
                  </div>
                )}
              </div>
            </div>

            {/* Top Products */}
            <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">🔥 Produits Populaires</h3>
              <div className="space-y-3">
                {products
                  .sort((a, b) => (b.clicks || 0) - (a.clicks || 0))
                  .slice(0, 5)
                  .map((product, index) => (
                    <div key={product.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                      <div className="bg-dinero-100 text-dinero-700 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold">
                        #{index + 1}
                      </div>
                      <img 
                        src={product.image_url} 
                        alt={product.name} 
                        className="w-10 h-10 object-cover rounded-lg"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-sm">{product.name}</div>
                        <div className="text-xs text-slate-600">
                          👆 {product.clicks || 0} clics • 👁️ {product.views || 0} vues
                        </div>
                      </div>
                      <div className="font-semibold">${product.price.toFixed(2)}</div>
                    </div>
                  ))}
                {products.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    <p>Aucun produit ajouté</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Products Tab */}
      {activeTab === 'products' && (
        <div>
          {products.length === 0 ? (
            <div className="bg-white rounded-xl shadow-md border border-slate-200 p-12 text-center">
              <div className="text-6xl mb-4">📦</div>
              <h2 className="text-xl font-bold text-slate-900 mb-2">Aucun produit dans votre marketplace</h2>
              <p className="text-slate-600">Commencez par rechercher des produits et ajoutez-les à votre marketplace!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((product) => {
                const originalPrice = product.metadata?.original_price || product.price;
                const marginAmount = product.metadata?.margin_amount || 0;
                const marginPercentage = product.metadata?.margin_percentage || 0;
                
                return (
                  <div key={product.id} className="bg-white rounded-xl shadow-md border border-slate-200 p-6">
                    <div className="relative mb-4">
                      <img 
                        src={product.image_url || 'https://via.placeholder.com/300x200'} 
                        alt={product.name}
                        className="w-full h-48 object-cover rounded-lg"
                      />
                      <div className="absolute top-2 right-2 bg-dinero-100 text-dinero-700 px-2 py-1 rounded-full text-xs font-semibold">
                        {product.category}
                      </div>
                      <div className="absolute top-2 left-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded-full text-xs">
                        👆 {product.clicks || 0} • 👁️ {product.views || 0}
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <h3 className="font-bold text-slate-900">{product.name}</h3>
                      <p className="text-sm text-slate-600 line-clamp-2">{product.description}</p>
                      
                      <div className="bg-slate-50 rounded-lg p-3">
                        <div className="flex items-center justify-between text-sm mb-2">
                          <span className="text-slate-600">Prix d'origine</span>
                          <span className="font-medium">${originalPrice.toFixed(2)}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm mb-2">
                          <span className="text-slate-600">Prix de vente</span>
                          <span className="font-bold text-dinero-600">${product.price.toFixed(2)}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-600">Marge</span>
                          <span className="font-bold text-green-600">
                            +${marginAmount.toFixed(2)} ({marginPercentage}%)
                          </span>
                        </div>
                      </div>
                      
                      <div className="text-xs text-slate-500">
                        Ajouté le {new Date(product.created_at).toLocaleDateString()}
                      </div>
                      
                      <button 
                        className="w-full px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-all font-medium"
                        onClick={() => handleDelete(product.id)}
                      >
                        🗑️ Supprimer
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Orders Tab */}
      {activeTab === 'orders' && (
        <div>
          {orders.length === 0 ? (
            <div className="bg-white rounded-xl shadow-md border border-slate-200 p-12 text-center">
              <div className="text-6xl mb-4">🛍️</div>
              <h2 className="text-xl font-bold text-slate-900 mb-2">Aucune commande</h2>
              <p className="text-slate-600">Les commandes de vos clients apparaîtront ici</p>
            </div>
          ) : (
            <div className="grid gap-6">
              {orders.map((order) => (
                <div key={order.id} className="bg-white rounded-xl shadow-md border border-slate-200 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="font-bold text-lg">{order.order_number}</div>
                    <div 
                      className="px-3 py-1 rounded-full text-white text-sm font-semibold"
                      style={{ backgroundColor: getStatusBadge(order.status).color }}
                    >
                      {getStatusBadge(order.status).icon} {getStatusBadge(order.status).text}
                    </div>
                  </div>
                  
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-2">👤 Client</h4>
                      <p className="font-medium">{order.customer.name}</p>
                      <p className="text-sm text-slate-600">{order.customer.phone}</p>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-2">📦 Produits ({order.items.length})</h4>
                      {order.items.map((item, idx) => (
                        <div key={idx} className="text-sm text-slate-600">
                          • {item.product_name} x{item.quantity}
                        </div>
                      ))}
                    </div>
                    
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-2">💰 Montants</h4>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span>Prix de vente:</span>
                          <span>${order.pricing?.total?.toFixed(2) || '0.00'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Coût:</span>
                          <span>${order.pricing?.cost?.toFixed(2) || '0.00'}</span>
                        </div>
                        <div className="flex justify-between font-semibold text-green-600">
                          <span>Bénéfice:</span>
                          <span>+${order.pricing?.profit?.toFixed(2) || '0.00'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-4 pt-4 border-t text-sm text-slate-500">
                    📅 {new Date(order.created_at).toLocaleString('fr-FR')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-slate-900 mb-2">⚙️ Paramètres de la Marketplace</h2>
              <p className="text-slate-600">Personnalisez le nom et le logo de votre boutique</p>
            </div>

            <div className="space-y-6">
              {/* Logo Preview */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">🖼️ Logo de la Marketplace</label>
                <div className="mb-3">
                  <img 
                    src={settingsForm.marketplace_logo || 'https://via.placeholder.com/200x80?text=Logo'} 
                    alt="Logo Preview"
                    className="h-20 w-auto rounded-lg border border-slate-200"
                  />
                </div>
                <input
                  type="text"
                  value={settingsForm.marketplace_logo}
                  onChange={(e) => handleSettingsChange('marketplace_logo', e.target.value)}
                  placeholder="URL du logo (ex: https://example.com/logo.png)"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none"
                />
                <p className="text-xs text-slate-500 mt-1">Dimensions recommandées: 200x80 pixels</p>
              </div>

              {/* Marketplace Name */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">🏪 Nom de la Marketplace</label>
                <input
                  type="text"
                  value={settingsForm.marketplace_name}
                  onChange={(e) => handleSettingsChange('marketplace_name', e.target.value)}
                  placeholder="Ex: Ma Super Boutique"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">📝 Description</label>
                <textarea
                  value={settingsForm.marketplace_description}
                  onChange={(e) => handleSettingsChange('marketplace_description', e.target.value)}
                  placeholder="Description de votre marketplace"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none"
                  rows="3"
                />
              </div>

              {/* Actions */}
              <div>
                <button 
                  className="w-full px-6 py-3 bg-dinero-600 text-white rounded-lg hover:bg-dinero-700 transition-all font-semibold"
                  onClick={handleUpdateSettings}
                >
                  💾 Enregistrer les modifications
                </button>
              </div>
            </div>
          </div>

          {/* Preview Card */}
          <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-slate-900 mb-2">👁️ Aperçu</h2>
              <p className="text-slate-600">Voici comment apparaîtra votre marketplace</p>
            </div>

            <div className="bg-slate-50 rounded-lg p-6">
              <div className="flex items-center gap-4">
                {settingsForm.marketplace_logo && (
                  <img 
                    src={settingsForm.marketplace_logo} 
                    alt="Logo Preview"
                    className="h-12 w-auto rounded-lg"
                  />
                )}
                <div>
                  <h3 className="font-bold text-slate-900">
                    {settingsForm.marketplace_name || 'Ma Marketplace'}
                  </h3>
                  <p className="text-slate-600">
                    {settingsForm.marketplace_description || 'Description de votre marketplace'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MyMarketplace;