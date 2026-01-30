import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDarkMode } from '../contexts/DarkModeContext';
import { ArrowLeft, Moon, Sun, Store, Search, ShoppingCart, BarChart3, Package } from 'lucide-react';

// Import B2C Components
import SearchBar from '../components/b2c/SearchBar';
import ProductCard from '../components/b2c/ProductCard';
import LoadingSpinner from '../components/b2c/LoadingSpinner';
import RecommendationSummary from '../components/b2c/RecommendationSummary';
import Shop from '../components/b2c/Shop';
import Cart from '../components/b2c/Cart';
import MyMarketplace from '../components/b2c/MyMarketplace';
import OrderTracking from '../components/b2c/OrderTracking';

const B2CPage = () => {
  const { isDarkMode, toggleDarkMode } = useDarkMode();
  
  // State management
  const [currentView, setCurrentView] = useState('search'); // search, shop, cart, dashboard, tracking
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchConfig, setSearchConfig] = useState({
    use_amazon: true,   // Enabled - API key added
    use_alibaba: true,  // Enabled - API key added
    use_walmart: true,  // Enabled - API key available
    use_cdiscount: true, // Enabled - API key available
    max_results: 20
  });
  const [summary, setSummary] = useState(null);
  const [intent, setIntent] = useState(null);

  // Search functionality
  const handleSearch = async (query) => {
    if (!query.trim()) return;
    
    setLoading(true);
    setSearchResults([]);
    setSummary(null);
    setIntent(null);

    try {
      const response = await fetch('http://localhost:8000/api/b2c/search/semantic', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          ...searchConfig
        })
      });

      const data = await response.json();
      
      // Handle both old and new response formats
      let products = [];
      if (data.products) {
        products = data.products;
      } else if (data.results) {
        // Convert results format to products format
        products = data.results.map(result => ({
          ...result.product,
          score: result.score
        }));
      }
      
      if (products.length > 0) {
        setSearchResults(products);
        setSummary(data.summary);
        setIntent(data.intent);
      } else {
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Search error:', error);
      alert('❌ Erreur lors de la recherche');
    } finally {
      setLoading(false);
    }
  };

  // Navigation functions
  const handleViewShop = () => setCurrentView('shop');
  const handleViewCart = () => setCurrentView('cart');
  const handleViewDashboard = () => setCurrentView('dashboard');
  const handleViewTracking = () => setCurrentView('tracking');
  const handleBackToSearch = () => setCurrentView('search');

  // Render different views
  const renderCurrentView = () => {
    switch (currentView) {
      case 'shop':
        return (
          <Shop 
            onViewCart={handleViewCart}
            onBack={handleBackToSearch}
          />
        );
      
      case 'cart':
        return (
          <Cart 
            onBack={handleViewShop}
            onOrderComplete={() => {
              alert('✅ Commande créée avec succès!');
              setCurrentView('shop');
            }}
          />
        );
      
      case 'dashboard':
        return <MyMarketplace />;
      
      case 'tracking':
        return <OrderTracking onBack={handleBackToSearch} />;
      
      default: // search view
        return (
          <div className="space-y-6">
            {/* Search Interface */}
            <div className={`glass-effect rounded-3xl shadow-2xl border p-8 ${
              isDarkMode 
                ? 'bg-slate-800 border-slate-700' 
                : 'border-de-york'
            }`}>
              <div className="mb-6">
                <h2 className={`text-2xl font-bold mb-2 flex items-center gap-3 ${
                  isDarkMode ? 'text-white' : 'text-viridian'
                }`}>
                  <Search className="w-6 h-6" style={{ color: 'var(--viridian)' }} />
                  Recherche de Produits
                </h2>
                <p className={`text-sm ${
                  isDarkMode ? 'text-slate-400' : 'text-shadow-green'
                }`}>
                  Recherchez des produits sur Amazon, Alibaba, Walmart et Cdiscount
                </p>
              </div>

              <SearchBar
                value={searchQuery}
                onChange={setSearchQuery}
                onSearch={handleSearch}
                disabled={loading}
              />

              {/* Search Configuration */}
              <div className="mt-4 flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="amazon"
                    checked={searchConfig.use_amazon}
                    onChange={(e) => setSearchConfig(prev => ({...prev, use_amazon: e.target.checked}))}
                    className="rounded"
                  />
                  <label htmlFor="amazon" className={isDarkMode ? 'text-slate-300' : 'text-slate-700'}>
                    🛒 Amazon ✅
                  </label>
                </div>
                
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="alibaba"
                    checked={searchConfig.use_alibaba}
                    onChange={(e) => setSearchConfig(prev => ({...prev, use_alibaba: e.target.checked}))}
                    className="rounded"
                  />
                  <label htmlFor="alibaba" className={isDarkMode ? 'text-slate-300' : 'text-slate-700'}>
                    🏭 Alibaba ✅
                  </label>
                </div>
                
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="walmart"
                    checked={searchConfig.use_walmart}
                    onChange={(e) => setSearchConfig(prev => ({...prev, use_walmart: e.target.checked}))}
                    className="rounded"
                  />
                  <label htmlFor="walmart" className={isDarkMode ? 'text-slate-300' : 'text-slate-700'}>
                    🛍️ Walmart ✅
                  </label>
                </div>
                
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="cdiscount"
                    checked={searchConfig.use_cdiscount}
                    onChange={(e) => setSearchConfig(prev => ({...prev, use_cdiscount: e.target.checked}))}
                    className="rounded"
                  />
                  <label htmlFor="cdiscount" className={isDarkMode ? 'text-slate-300' : 'text-slate-700'}>
                    🛒 Cdiscount ✅
                  </label>
                </div>

                <div className="flex items-center gap-2">
                  <label className={isDarkMode ? 'text-slate-300' : 'text-slate-700'}>
                    Max résultats:
                  </label>
                  <select
                    value={searchConfig.max_results}
                    onChange={(e) => setSearchConfig(prev => ({...prev, max_results: parseInt(e.target.value)}))}
                    className={`px-2 py-1 rounded border ${
                      isDarkMode 
                        ? 'bg-slate-700 border-slate-600 text-white' 
                        : 'bg-white border-slate-300'
                    }`}
                  >
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Loading */}
            {loading && (
              <div className={`glass-effect rounded-3xl shadow-2xl border p-8 ${
                isDarkMode 
                  ? 'bg-slate-800 border-slate-700' 
                  : 'border-de-york'
              }`}>
                <LoadingSpinner />
              </div>
            )}

            {/* Search Summary */}
            {summary && intent && !loading && (
              <div className={`glass-effect rounded-3xl shadow-2xl border p-8 ${
                isDarkMode 
                  ? 'bg-slate-800 border-slate-700' 
                  : 'border-de-york'
              }`}>
                <RecommendationSummary
                  summary={summary}
                  intent={intent}
                  totalFound={searchResults.length}
                />
              </div>
            )}

            {/* Search Results */}
            {searchResults.length > 0 && !loading && (
              <div className={`glass-effect rounded-3xl shadow-2xl border p-8 ${
                isDarkMode 
                  ? 'bg-slate-800 border-slate-700' 
                  : 'border-de-york'
              }`}>
                <h3 className={`text-xl font-bold mb-6 ${
                  isDarkMode ? 'text-white' : 'text-viridian'
                }`}>
                  🎯 Résultats de recherche ({searchResults.length})
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {searchResults.map((product, index) => (
                    <ProductCard
                      key={`${product.name}-${index}`}
                      product={product}
                      score={product.score || 0.8}
                      rank={index + 1}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* No Results */}
            {searchResults.length === 0 && !loading && searchQuery && (
              <div className={`glass-effect rounded-3xl shadow-2xl border p-8 text-center ${
                isDarkMode 
                  ? 'bg-slate-800 border-slate-700' 
                  : 'border-de-york'
              }`}>
                <div className={`text-6xl mb-4 ${
                  isDarkMode ? 'text-slate-400' : 'text-shadow-green'
                }`}>
                  🔍
                </div>
                <h3 className={`text-xl font-bold mb-2 ${
                  isDarkMode ? 'text-white' : 'text-viridian'
                }`}>
                  Aucun résultat trouvé
                </h3>
                <p className={isDarkMode ? 'text-slate-400' : 'text-shadow-green'}>
                  Essayez avec d'autres mots-clés ou vérifiez les sources sélectionnées
                </p>
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      isDarkMode 
        ? 'bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800' 
        : 'bg-gradient-to-br from-foam via-white to-pixie-green'
    }`}>
      {/* Header */}
      <div className={`glass-effect shadow-xl sticky top-0 z-50 transition-colors duration-300 ${
        isDarkMode 
          ? 'bg-slate-900/90 border-slate-700' 
          : 'border-de-york'
      } border-b`}>
        <div className="max-w-7xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className={`p-2.5 rounded-full smooth-transition border-2 ${
                  isDarkMode 
                    ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-600 hover:border-slate-500' 
                    : 'bg-foam hover:bg-pixie-green text-viridian border-de-york hover:border-viridian'
                }`}
                title="Back to Home"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <img 
                src="/dinero.png" 
                alt="Dinero Logo" 
                className="h-20 w-auto rounded-xl object-contain shadow-lg hover:scale-105 smooth-transition"
              />
              <div>
                <h1 className={`text-2xl font-extrabold tracking-tight ${
                  isDarkMode ? 'text-white' : 'text-viridian'
                }`}>Dinero Orbit</h1>
                <p className={`text-sm ${
                  isDarkMode ? 'text-slate-400' : 'text-shadow-green'
                }`}>B2C Marketplace</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {/* Navigation Buttons */}
              <button
                onClick={() => setCurrentView('search')}
                className={`p-2 rounded-lg smooth-transition ${
                  currentView === 'search'
                    ? 'gradient-primary text-white shadow-lg'
                    : (isDarkMode ? 'text-slate-300 hover:bg-slate-800' : 'text-viridian hover:bg-foam')
                }`}
                title="Recherche"
              >
                <Search size={20} />
              </button>
              
              <button
                onClick={handleViewShop}
                className={`p-2 rounded-lg smooth-transition ${
                  currentView === 'shop'
                    ? 'gradient-primary text-white shadow-lg'
                    : (isDarkMode ? 'text-slate-300 hover:bg-slate-800' : 'text-viridian hover:bg-foam')
                }`}
                title="Boutique"
              >
                <Store size={20} />
              </button>
              
              <button
                onClick={handleViewCart}
                className={`p-2 rounded-lg smooth-transition ${
                  currentView === 'cart'
                    ? 'gradient-primary text-white shadow-lg'
                    : (isDarkMode ? 'text-slate-300 hover:bg-slate-800' : 'text-viridian hover:bg-foam')
                }`}
                title="Panier"
              >
                <ShoppingCart size={20} />
              </button>
              
              <button
                onClick={handleViewDashboard}
                className={`p-2 rounded-lg smooth-transition ${
                  currentView === 'dashboard'
                    ? 'gradient-primary text-white shadow-lg'
                    : (isDarkMode ? 'text-slate-300 hover:bg-slate-800' : 'text-viridian hover:bg-foam')
                }`}
                title="Dashboard"
              >
                <BarChart3 size={20} />
              </button>

              <button
                onClick={handleViewTracking}
                className={`p-2 rounded-lg smooth-transition ${
                  currentView === 'tracking'
                    ? 'gradient-primary text-white shadow-lg'
                    : (isDarkMode ? 'text-slate-300 hover:bg-slate-800' : 'text-viridian hover:bg-foam')
                }`}
                title="Suivi"
              >
                <Package size={20} />
              </button>
              
              <button
                onClick={toggleDarkMode}
                className={`p-2 rounded-lg smooth-transition ${
                  isDarkMode 
                    ? 'text-slate-300 hover:text-white hover:bg-slate-800' 
                    : 'text-viridian hover:bg-foam'
                }`}
              >
                {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {renderCurrentView()}
      </div>
    </div>
  );
};

export default B2CPage;