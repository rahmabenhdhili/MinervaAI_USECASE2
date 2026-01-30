import React, { useState } from 'react';

function OrderTracking({ onBack }) {
  const [orderNumber, setOrderNumber] = useState('');
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleTrackOrder = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setOrder(null);

    try {
      const response = await fetch(`http://localhost:8000/api/b2c/orders/number/${orderNumber}`);
      const data = await response.json();
      
      if (data.success) {
        setOrder(data.order);
      } else {
        setError('Commande non trouvée');
      }
    } catch (error) {
      console.error('Erreur:', error);
      setError('Erreur de connexion au serveur');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'pending': return '⏳';
      case 'confirmed': return '✅';
      case 'shipped': return '🚚';
      case 'delivered': return '📦';
      case 'cancelled': return '❌';
      default: return '📋';
    }
  };

  const getStatusText = (status) => {
    switch(status) {
      case 'pending': return 'En attente';
      case 'confirmed': return 'Confirmée';
      case 'shipped': return 'Expédiée';
      case 'delivered': return 'Livrée';
      case 'cancelled': return 'Annulée';
      default: return status;
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'pending': return '#ff9800';
      case 'confirmed': return '#2196F3';
      case 'shipped': return '#9c27b0';
      case 'delivered': return '#4caf50';
      case 'cancelled': return '#f44336';
      default: return '#666';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button 
          className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-all"
          onClick={onBack}
        >
          ← Retour
        </button>
        <h1 className="text-2xl font-bold text-slate-900">📦 Suivi de commande</h1>
      </div>

      <div className="bg-white rounded-xl shadow-md border border-slate-200 p-8">
        <div className="max-w-md mx-auto">
          <h2 className="text-xl font-semibold text-slate-900 mb-6 text-center">
            Entrez votre numéro de commande
          </h2>
          <form onSubmit={handleTrackOrder} className="space-y-4">
            <input
              type="text"
              placeholder="Ex: ORD-00001"
              value={orderNumber}
              onChange={(e) => setOrderNumber(e.target.value)}
              required
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none text-center"
            />
            <button 
              type="submit" 
              disabled={loading}
              className="w-full px-6 py-3 bg-dinero-600 text-white rounded-lg hover:bg-dinero-700 disabled:opacity-50 transition-all font-semibold"
            >
              {loading ? 'Recherche...' : '🔍 Suivre ma commande'}
            </button>
          </form>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-center gap-3">
            <span className="text-2xl">❌</span>
            <p className="text-red-800 font-medium">{error}</p>
          </div>
        </div>
      )}

      {order && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="bg-dinero-100 text-dinero-700 px-4 py-2 rounded-full font-bold">
                {order.order_number}
              </div>
              <div 
                className="px-4 py-2 rounded-full text-white font-semibold"
                style={{ backgroundColor: getStatusColor(order.status) }}
              >
                {getStatusIcon(order.status)} {getStatusText(order.status)}
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-slate-50 rounded-lg p-4">
                <h3 className="font-semibold text-slate-900 mb-3">👤 Client</h3>
                <div className="space-y-1 text-sm">
                  <p><strong>{order.customer.name}</strong></p>
                  <p>{order.customer.email}</p>
                  <p>{order.customer.phone}</p>
                </div>
              </div>

              <div className="bg-slate-50 rounded-lg p-4">
                <h3 className="font-semibold text-slate-900 mb-3">📍 Livraison</h3>
                <div className="space-y-1 text-sm">
                  <p>{order.shipping_address.street}</p>
                  <p>{order.shipping_address.city}, {order.shipping_address.state}</p>
                  <p>{order.shipping_address.zip_code}</p>
                  <p>{order.shipping_address.country}</p>
                </div>
              </div>

              <div className="bg-slate-50 rounded-lg p-4">
                <h3 className="font-semibold text-slate-900 mb-3">💰 Montant</h3>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Sous-total:</span>
                    <span>${order.pricing.subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Livraison:</span>
                    <span>${order.pricing.shipping.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Taxes:</span>
                    <span>${order.pricing.tax.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between font-bold border-t pt-1">
                    <span>Total:</span>
                    <span>${order.pricing.total.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>

            {order.tracking_number && (
              <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">🚚 Numéro de suivi</h3>
                <p className="text-blue-800 font-mono text-lg">{order.tracking_number}</p>
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-6">📋 Historique de la commande</h3>
            <div className="space-y-4">
              {order.status_history.map((history, index) => (
                <div key={index} className="flex items-start gap-4">
                  <div 
                    className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold"
                    style={{ backgroundColor: getStatusColor(history.status) }}
                  >
                    {getStatusIcon(history.status)}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-slate-900">{getStatusText(history.status)}</p>
                    <p className="text-slate-600">{history.note}</p>
                    <p className="text-sm text-slate-500">
                      {new Date(history.timestamp).toLocaleString('fr-FR')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-6">📦 Produits commandés</h3>
            <div className="space-y-4">
              {order.items.map((item, index) => (
                <div key={index} className="flex items-center gap-4 p-4 bg-slate-50 rounded-lg">
                  <img 
                    src={item.product_image} 
                    alt={item.product_name} 
                    className="w-16 h-16 object-cover rounded-lg"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">{item.product_name}</p>
                    <p className="text-sm text-slate-600">Quantité: {item.quantity}</p>
                  </div>
                  <p className="font-semibold text-slate-900">
                    ${(item.price * item.quantity).toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default OrderTracking;