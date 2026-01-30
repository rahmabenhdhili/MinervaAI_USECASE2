import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import axios from 'axios'
import { useDarkMode } from '../contexts/DarkModeContext'
import { 
  Building2, Search, TrendingUp, Shield, User, Mail, Lock, Phone, MapPin, 
  Briefcase, ArrowRight, Eye, EyeOff, Package, Award, Zap, Target, LogOut,
  CheckCircle, Moon, Sun, ArrowLeft
} from 'lucide-react'

const API_BASE_URL = 'http://localhost:8000'

const B2BPage = () => {
  const navigate = useNavigate()
  const { isDarkMode, toggleDarkMode } = useDarkMode()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [user, setUser] = useState(null)
  const [showSignUp, setShowSignUp] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [maxPrice, setMaxPrice] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [recommendationsLoading, setRecommendationsLoading] = useState(false)
  const [recommendations, setRecommendations] = useState([])
  const [formData, setFormData] = useState({
    email: '', password: '', company_name: '', contact_person: '', 
    phone: '', address: '', business_type: ''
  })
  const [loginData, setLoginData] = useState({ email: '', password: '' })
  const [message, setMessage] = useState('')

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    if (token && userData) {
      setIsLoggedIn(true)
      setUser(JSON.parse(userData))
      loadRecommendations()
    } else {
      // If user is not logged in, show login form by default
      setShowLogin(true)
    }
  }, [])

  const loadRecommendations = async () => {
    try {
      setRecommendationsLoading(true)
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/api/b2b/recommendations`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setRecommendations(response.data.recommended_products || [])
    } catch (error) {
      console.error('Failed to load recommendations:', error)
      setRecommendations([])
    } finally {
      setRecommendationsLoading(false)
    }
  }

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleLoginChange = (e) => {
    setLoginData({ ...loginData, [e.target.name]: e.target.value })
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      const response = await axios.post(`${API_BASE_URL}/api/b2b/auth/login`, loginData)
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
      setIsLoggedIn(true)
      setUser(response.data.user)
      setShowLogin(false)
      setMessage('')
      loadRecommendations()
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  const handleSignUp = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      await axios.post(`${API_BASE_URL}/api/b2b/auth/register`, formData)
      setMessage('Account created successfully! Please login to continue.')
      setFormData({
        email: '', password: '', company_name: '', contact_person: '', 
        phone: '', address: '', business_type: ''
      })
      setTimeout(() => {
        setShowSignUp(false)
        setShowLogin(true)
        setMessage('')
      }, 2000)
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const searchPayload = {
        product_name: searchQuery,
        quantity: quantity
      }
      
      // Add max_price only if it's provided
      if (maxPrice && parseFloat(maxPrice) > 0) {
        searchPayload.max_price = parseFloat(maxPrice)
      }
      
      const response = await axios.post(`${API_BASE_URL}/api/b2b/search`, searchPayload, {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      // Handle the mainB2B.py response format
      const results = []
      
      // Check if we have a valid response
      if (!response.data) {
        throw new Error('No data received from server')
      }
      
      // Handle best product
      if (response.data.best_product) {
        results.push({
          ...response.data.best_product,
          is_best: true,
          explanation: response.data.explanation
        })
      }
      
      // Handle alternatives
      if (response.data.alternatives && Array.isArray(response.data.alternatives)) {
        results.push(...response.data.alternatives.map(alt => ({
          ...alt,
          is_alternative: true
        })))
      }
      
      // If no results but we have an explanation, show it
      if (results.length === 0 && response.data.explanation) {
        setMessage(response.data.explanation)
      } else {
        setMessage('')
      }
      
      setSearchResults(results)
      loadRecommendations()
    } catch (error) {
      console.error('Search failed:', error)
      setSearchResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleSupplierClick = async (supplier) => {
    try {
      const token = localStorage.getItem('token')
      
      // Track the click with comprehensive data
      await axios.post(`${API_BASE_URL}/api/b2b/click`, {
        product_name: supplier.product_name || searchQuery || 'Unknown Product',
        brand: supplier.brand || 'Unknown',
        category: supplier.category || 'General',
        supplier: supplier.supplier_name || 'Unknown'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      // Reload recommendations after click to get updated suggestions
      loadRecommendations()
    } catch (error) {
      console.error('Click tracking failed:', error)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setIsLoggedIn(false)
    setUser(null)
    setSearchResults([])
    setRecommendations([])
    setSearchQuery('')
    setQuantity(1)
    setMaxPrice('')
    // Navigate to home page after logout
    navigate('/')
  }

  // Dashboard for logged in users
  if (isLoggedIn) {
    return (
      <div className={`min-h-screen transition-colors duration-300 ${
        isDarkMode 
          ? 'bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800' 
          : 'bg-gradient-to-br from-foam via-white to-dinero-50'
      }`}>
        <div className={`backdrop-blur-md shadow-lg border-b sticky top-0 z-50 transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-slate-900/90 border-slate-700' 
            : 'bg-white/80 border-dinero-100'
        }`}>
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Link
                  to="/"
                  className={`p-2.5 rounded-full transition-all border-2 ${
                    isDarkMode 
                      ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-600 hover:border-slate-500' 
                      : 'bg-dinero-50 hover:bg-dinero-100 text-dinero-600 border-dinero-200 hover:border-dinero-300'
                  }`}
                  title="Back to Home"
                >
                  <ArrowLeft className="w-5 h-5" />
                </Link>
                <img src="/dinero.png" alt="Dinero Logo" className="h-16 w-auto rounded-xl object-contain" />
                <div>
                  <h1 className={`text-2xl font-extrabold tracking-tight ${
                    isDarkMode ? 'text-white' : 'text-slate-900'
                  }`}>Dinero Prime</h1>
                  <p className={`text-sm ${
                    isDarkMode ? 'text-slate-400' : 'text-slate-600'
                  }`}>Welcome back, {user?.contact_person}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className={`text-sm font-bold ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>{user?.company_name}</div>
                  <div className={`text-xs ${isDarkMode ? 'text-slate-400' : 'text-slate-500'}`}>{user?.business_type}</div>
                </div>
                <button
                  onClick={toggleDarkMode}
                  className={`p-2 rounded-lg transition-colors ${
                    isDarkMode 
                      ? 'text-slate-300 hover:text-white hover:bg-slate-800' 
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
                </button>
                <button onClick={handleLogout} className="p-3 bg-red-50 hover:bg-red-100 text-red-600 rounded-full transition-all border-2 border-red-200 hover:border-red-300" title="Logout">
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-100 p-8 mb-8">
            <h2 className="text-3xl font-extrabold text-slate-900 mb-6 flex items-center gap-3">
              <Search className="w-8 h-8 text-dinero-600" />
              <span>Find Suppliers</span>
            </h2>
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-1 relative">
                  <Package className="absolute left-4 top-1/2 -translate-y-1/2 w-6 h-6 text-dinero-500" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search for products, suppliers, or categories..."
                    className="w-full pl-14 pr-4 py-5 rounded-2xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all text-lg"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading || !searchQuery.trim()}
                  className="px-8 py-5 bg-gradient-to-r from-dinero-500 to-viridian text-white rounded-2xl font-bold text-lg hover:shadow-xl transition-all disabled:opacity-50 flex items-center gap-3"
                >
                  {loading ? (
                    <>
                      <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Searching...</span>
                    </>
                  ) : (
                    <>
                      <Search className="w-6 h-6" />
                      <span>Search</span>
                    </>
                  )}
                </button>
              </div>
              
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Quantity Required
                  </label>
                  <div className="relative">
                    <Package className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dinero-500" />
                    <input
                      type="number"
                      min="1"
                      value={quantity}
                      onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                      placeholder="1"
                      className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all"
                    />
                  </div>
                </div>
                
                <div className="flex-1">
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Max Price in Dinars (Optional)
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-dinero-500 font-bold">د.ت</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={maxPrice}
                      onChange={(e) => setMaxPrice(e.target.value)}
                      placeholder="No limit (د.ت)"
                      className="w-full pl-8 pr-4 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all"
                    />
                  </div>
                </div>
              </div>
            </form>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              {searchResults.length > 0 && (
                <div className="bg-white rounded-3xl shadow-2xl border border-slate-100 p-8 mb-8">
                  <h3 className="text-2xl font-extrabold text-slate-900 mb-6 flex items-center gap-3">
                    <Target className="w-7 h-7 text-dinero-600" />
                    <span>Search Results ({searchResults.length})</span>
                  </h3>
                  <div className="space-y-4">
                    {searchResults.map((supplier, index) => (
                      <div
                        key={index}
                        onClick={() => handleSupplierClick(supplier)}
                        className={`p-6 rounded-2xl border hover:shadow-lg transition-all cursor-pointer ${
                          supplier.is_best 
                            ? 'bg-gradient-to-r from-dinero-50 to-viridian-50 border-dinero-300 ring-2 ring-dinero-200' 
                            : 'bg-gradient-to-r from-slate-50 to-dinero-50 border-slate-200 hover:border-dinero-300'
                        }`}
                      >
                        {supplier.is_best && (
                          <div className="flex items-center gap-2 mb-3">
                            <Award className="w-5 h-5 text-dinero-600" />
                            <span className="text-sm font-bold text-dinero-700 bg-dinero-100 px-3 py-1 rounded-full">
                              Best Match
                            </span>
                          </div>
                        )}
                        
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="text-xl font-bold text-slate-900 mb-2">
                              {supplier.supplier_name || supplier.name || supplier.product_name || 'Supplier'}
                            </h4>
                            <p className="text-slate-600 mb-3">
                              {supplier.description || supplier.product_name || 'Quality supplier for your business needs'}
                            </p>
                            
                            {supplier.explanation && (
                              <div className="bg-white/70 rounded-lg p-3 mb-3 border border-dinero-200">
                                <p className="text-sm text-slate-700 italic">
                                  <strong>AI Recommendation:</strong> {supplier.explanation}
                                </p>
                              </div>
                            )}
                            
                            <div className="flex items-center gap-4 text-sm mb-3">
                              {supplier.category && (
                                <span className="px-3 py-1 bg-dinero-100 text-dinero-700 rounded-full text-xs font-semibold">
                                  {supplier.category}
                                </span>
                              )}
                              {supplier.brand && (
                                <span className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-xs font-semibold">
                                  {supplier.brand}
                                </span>
                              )}
                              {supplier.similarity_score && (
                                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
                                  Match: {(supplier.similarity_score * 100).toFixed(0)}%
                                </span>
                              )}
                            </div>
                            
                            {/* Contact Information */}
                            <div className="bg-slate-50 rounded-lg p-3 mb-3 border border-slate-200">
                              <h5 className="text-sm font-bold text-slate-800 mb-2 flex items-center gap-2">
                                <User className="w-4 h-4" />
                                Contact Information
                              </h5>
                              <div className="space-y-1 text-sm text-slate-600">
                                {supplier.phone && (
                                  <div className="flex items-center gap-2">
                                    <Phone className="w-3 h-3 text-dinero-500" />
                                    <span>{supplier.phone}</span>
                                  </div>
                                )}
                                {supplier.email && (
                                  <div className="flex items-center gap-2">
                                    <Mail className="w-3 h-3 text-dinero-500" />
                                    <span>{supplier.email}</span>
                                  </div>
                                )}
                                {supplier.city && (
                                  <div className="flex items-center gap-2">
                                    <MapPin className="w-3 h-3 text-dinero-500" />
                                    <span className="text-xs">{supplier.city}</span>
                                  </div>
                                )}
                                {!supplier.phone && !supplier.email && !supplier.city && (
                                  <div className="flex items-center gap-2 text-slate-500">
                                    <Phone className="w-3 h-3" />
                                    <span className="text-xs">Contact details available upon request</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            {(supplier.total_price || supplier.price) && (
                              <div className="text-2xl font-bold text-dinero-600 mb-1">
                                {supplier.total_price || supplier.price} د.ت
                                {supplier.total_price && (
                                  <div className="text-xs text-slate-500 font-normal">
                                    Total for {quantity} units
                                  </div>
                                )}
                              </div>
                            )}
                            {supplier.unit_price && supplier.total_price && (
                              <div className="text-sm text-slate-600 mb-1">
                                {supplier.unit_price} د.ت per unit
                              </div>
                            )}
                            <div className="text-sm text-slate-500 mb-3">
                              {supplier.min_order || 'Contact for details'}
                            </div>
                            
                            {/* Contact Button */}
                            {(supplier.phone || supplier.email) && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (supplier.phone) {
                                    window.open(`tel:${supplier.phone}`)
                                  } else if (supplier.email) {
                                    window.open(`mailto:${supplier.email}`)
                                  }
                                }}
                                className="px-3 py-1 bg-dinero-500 hover:bg-dinero-600 text-white rounded-lg text-xs font-semibold transition-all flex items-center gap-1"
                              >
                                <Phone className="w-3 h-3" />
                                Contact
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {searchQuery && searchResults.length === 0 && !loading && (
                <div className="bg-white rounded-3xl shadow-2xl border border-slate-100 p-8 text-center">
                  <Package className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-xl font-bold text-slate-900 mb-2">No suppliers found</h3>
                  {message ? (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                      <p className="text-blue-800 text-sm">
                        <strong>AI Analysis:</strong> {message}
                      </p>
                    </div>
                  ) : null}
                  <p className="text-slate-600">Try searching with different keywords, adjusting quantity, or increasing your budget.</p>
                </div>
              )}
            </div>

            <div className="lg:col-span-1">
              {/* Loading State for Recommendations */}
              {recommendationsLoading && (
                <div className="bg-gradient-to-br from-white to-dinero-50 rounded-3xl shadow-2xl border-2 border-dinero-200 p-7 sticky top-24">
                  <h3 className="text-2xl font-extrabold text-slate-900 mb-6 flex items-center gap-3">
                    <Zap className="w-7 h-7 text-dinero-600" />
                    <span>Loading Recommendations...</span>
                  </h3>
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="p-4 bg-white rounded-2xl shadow-md border border-slate-100 animate-pulse">
                        <div className="h-4 bg-slate-200 rounded mb-2"></div>
                        <div className="h-3 bg-slate-100 rounded mb-2"></div>
                        <div className="h-3 bg-slate-100 rounded w-2/3"></div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Recommendations Display */}
              {!recommendationsLoading && recommendations.length > 0 && (
                <div className="bg-gradient-to-br from-white to-dinero-50 rounded-3xl shadow-2xl border-2 border-dinero-200 p-7 sticky top-24">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-2xl font-extrabold text-slate-900 flex items-center gap-3">
                      <Zap className="w-7 h-7 text-dinero-600" />
                      <span>Recommended for You</span>
                    </h3>
                    <button
                      onClick={loadRecommendations}
                      disabled={recommendationsLoading}
                      className="p-2 text-dinero-600 hover:bg-dinero-50 rounded-lg transition-all disabled:opacity-50"
                      title="Refresh recommendations"
                    >
                      <ArrowRight className={`w-4 h-4 ${recommendationsLoading ? 'animate-spin' : ''}`} />
                    </button>
                  </div>
                  <div className="space-y-4">
                    {recommendations.slice(0, 5).map((rec, index) => (
                      <div
                        key={index}
                        onClick={() => handleSupplierClick(rec)}
                        className="p-4 bg-white rounded-2xl shadow-md border border-slate-100 hover:shadow-lg transition-all cursor-pointer group"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-bold text-slate-900 text-sm group-hover:text-dinero-600 transition-colors">
                            {rec.supplier_name || 'Recommended Supplier'}
                          </h4>
                          {rec.score && (
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                              {(rec.score * 100).toFixed(0)}% match
                            </span>
                          )}
                        </div>
                        
                        <p className="text-xs text-slate-600 mb-2">
                          {rec.product_name || rec.description || 'Based on your search history'}
                        </p>
                        
                        {/* Product Details */}
                        <div className="flex items-center gap-2 mb-2">
                          {rec.brand && (
                            <span className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded-full">
                              {rec.brand}
                            </span>
                          )}
                          {rec.category && (
                            <span className="text-xs bg-dinero-100 text-dinero-700 px-2 py-1 rounded-full">
                              {rec.category}
                            </span>
                          )}
                        </div>
                        
                        {/* Price */}
                        {rec.unit_price && (
                          <div className="text-sm font-bold text-dinero-600 mb-2">
                            {rec.unit_price} د.ت per unit
                          </div>
                        )}
                        
                        {/* Contact Info for Recommendations */}
                        {(rec.phone || rec.email) && (
                          <div className="bg-slate-50 rounded p-2 mt-2 border border-slate-200">
                            <div className="space-y-1 text-xs text-slate-600">
                              {rec.phone && (
                                <div className="flex items-center gap-1">
                                  <Phone className="w-3 h-3 text-dinero-500" />
                                  <span>{rec.phone}</span>
                                </div>
                              )}
                              {rec.email && (
                                <div className="flex items-center gap-1">
                                  <Mail className="w-3 h-3 text-dinero-500" />
                                  <span>{rec.email}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  
                  {/* Recommendation Info */}
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-xs text-blue-700 text-center">
                      🚀 Recommendations improve as you search and interact with suppliers
                    </p>
                  </div>
                </div>
              )}
              
              {/* Empty State for Recommendations */}
              {!recommendationsLoading && recommendations.length === 0 && isLoggedIn && (
                <div className="bg-gradient-to-br from-white to-slate-50 rounded-3xl shadow-xl border border-slate-200 p-7 sticky top-24 text-center">
                  <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Zap className="w-8 h-8 text-slate-400" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 mb-2">No Recommendations Yet</h3>
                  <p className="text-sm text-slate-600 mb-4">
                    Start searching for suppliers to get personalized recommendations based on your interests.
                  </p>
                  <div className="text-xs text-slate-500">
                    🔍 Search • 👆 Click • 🎯 Get Recommendations
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Landing page for non-authenticated users - Authentication focused
  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      isDarkMode 
        ? 'bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800' 
        : 'bg-gradient-to-br from-foam via-white to-dinero-50'
    } flex items-center justify-center`}>
      {/* Header */}
      <div className={`backdrop-blur-md shadow-lg border-b sticky top-0 z-50 transition-colors duration-300 ${
        isDarkMode 
          ? 'bg-slate-900/90 border-slate-700' 
          : 'bg-white/80 border-dinero-100'
      } absolute top-0 left-0 right-0`}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className={`p-2.5 rounded-full transition-all border-2 ${
                  isDarkMode 
                    ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-600 hover:border-slate-500' 
                    : 'bg-dinero-50 hover:bg-dinero-100 text-dinero-600 border-dinero-200 hover:border-dinero-300'
                }`}
                title="Back to Home"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <img src="/dinero.png" alt="Dinero Logo" className="h-16 w-auto rounded-xl object-contain" />
              <div>
                <h1 className={`text-2xl font-extrabold tracking-tight ${
                  isDarkMode ? 'text-white' : 'text-slate-900'
                }`}>Dinero Prime</h1>
                <p className={`text-sm ${
                  isDarkMode ? 'text-slate-400' : 'text-slate-600'
                }`}>B2B Suppliers</p>
              </div>
            </div>
            
            <button
              onClick={toggleDarkMode}
              className={`p-2 rounded-lg transition-colors ${
                isDarkMode 
                  ? 'text-slate-300 hover:text-white hover:bg-slate-800' 
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-md mx-auto px-6 py-8 mt-20">
        <div className={`rounded-3xl p-8 shadow-2xl border ${
          isDarkMode 
            ? 'bg-slate-800 border-slate-700' 
            : 'bg-white border-slate-100'
        }`}>
          <div className="text-center mb-8">
            <h2 className={`text-3xl font-extrabold mb-2 ${
              isDarkMode ? 'text-white' : 'text-slate-900'
            }`}>Welcome to Dinero Prime</h2>
            <p className={isDarkMode ? 'text-slate-400' : 'text-slate-600'}>
              Connect with trusted suppliers and grow your business
            </p>
          </div>

          <div className="flex flex-col gap-3">
            <button
              onClick={() => {
                setShowSignUp(true)
                setShowLogin(false)
              }}
              className="w-full px-6 py-3 bg-gradient-to-r from-dinero-500 to-viridian text-white rounded-xl font-bold hover:shadow-lg transition-all flex items-center justify-center gap-2"
            >
              <Building2 className="w-5 h-5" />
              <span>Create Business Account</span>
            </button>
            <button
              onClick={() => {
                setShowLogin(true)
                setShowSignUp(false)
              }}
              className={`w-full px-6 py-3 rounded-xl font-bold border-2 hover:shadow-lg transition-all ${
                isDarkMode 
                  ? 'bg-slate-700 text-slate-300 border-slate-600 hover:border-slate-500' 
                  : 'bg-white text-dinero-600 border-dinero-200 hover:border-dinero-400'
              }`}
            >
              Already have an account? Sign In
            </button>
          </div>
        </div>
      </div>

      {/* Sign Up Modal */}
      {showSignUp && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-8">
              <div className="text-center mb-8">
                <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Create Account</h2>
                <p className="text-slate-600">Join our B2B marketplace</p>
              </div>

              {message && (
                <div className={`p-4 rounded-2xl mb-6 ${message.includes('successfully') ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" />
                    <span className="text-sm font-medium">{message}</span>
                  </div>
                </div>
              )}

              <form onSubmit={handleSignUp} className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="text"
                      name="contact_person"
                      value={formData.contact_person}
                      onChange={handleInputChange}
                      placeholder="Contact Person"
                      className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all"
                      required
                    />
                  </div>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="text"
                      name="company_name"
                      value={formData.company_name}
                      onChange={handleInputChange}
                      placeholder="Company Name"
                      className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all"
                      required
                    />
                  </div>
                </div>

                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="Business Email"
                    className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all"
                    required
                  />
                </div>

                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    placeholder="Password"
                    className="w-full pl-10 pr-12 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                      placeholder="Phone"
                      className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all"
                      required
                    />
                  </div>
                  <div className="relative">
                    <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <select
                      name="business_type"
                      value={formData.business_type}
                      onChange={handleInputChange}
                      className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all appearance-none bg-white"
                      required
                    >
                      <option value="">Business Type</option>
                      <option value="Retailer">Retailer</option>
                      <option value="Wholesaler">Wholesaler</option>
                      <option value="Manufacturer">Manufacturer</option>
                      <option value="Distributor">Distributor</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>

                <div className="relative">
                  <MapPin className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
                  <textarea
                    name="address"
                    value={formData.address}
                    onChange={handleInputChange}
                    placeholder="Business Address"
                    rows="3"
                    className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all resize-none"
                    required
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 py-3 bg-gradient-to-r from-dinero-500 to-viridian text-white rounded-xl font-bold hover:shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        <span>Creating...</span>
                      </>
                    ) : (
                      <>
                        <Award className="w-5 h-5" />
                        <span>Create Account</span>
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowSignUp(false)
                      setMessage('')
                    }}
                    className="px-6 py-3 bg-slate-100 text-slate-600 rounded-xl font-bold hover:bg-slate-200 transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </form>

              <div className="text-center mt-6">
                <p className="text-slate-600">
                  Already have an account?{' '}
                  <button
                    onClick={() => {
                      setShowSignUp(false)
                      setShowLogin(true)
                      setMessage('')
                    }}
                    className="text-dinero-600 font-bold hover:text-dinero-700"
                  >
                    Sign In
                  </button>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Login Modal */}
      {showLogin && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full">
            <div className="p-8">
              <div className="text-center mb-8">
                <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Welcome Back</h2>
                <p className="text-slate-600">Sign in to your B2B account</p>
              </div>

              {message && (
                <div className="p-4 rounded-2xl mb-6 bg-red-50 text-red-700 border border-red-200">
                  <div className="flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    <span className="text-sm font-medium">{message}</span>
                  </div>
                </div>
              )}

              <form onSubmit={handleLogin} className="space-y-6">
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="email"
                    name="email"
                    value={loginData.email}
                    onChange={handleLoginChange}
                    placeholder="Business Email"
                    className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all"
                    required
                  />
                </div>

                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={loginData.password}
                    onChange={handleLoginChange}
                    placeholder="Password"
                    className="w-full pl-10 pr-12 py-3 rounded-xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>

                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 py-3 bg-gradient-to-r from-dinero-500 to-viridian text-white rounded-xl font-bold hover:shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        <span>Signing In...</span>
                      </>
                    ) : (
                      <>
                        <ArrowRight className="w-5 h-5" />
                        <span>Sign In</span>
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowLogin(false)
                      setMessage('')
                      navigate('/')
                    }}
                    className="px-6 py-3 bg-slate-100 text-slate-600 rounded-xl font-bold hover:bg-slate-200 transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </form>

              <div className="text-center mt-6">
                <p className="text-slate-600">
                  Don't have an account?{' '}
                  <button
                    onClick={() => {
                      setShowLogin(false)
                      setShowSignUp(true)
                      setMessage('')
                    }}
                    className="text-dinero-600 font-bold hover:text-dinero-700"
                  >
                    Sign Up
                  </button>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default B2BPage