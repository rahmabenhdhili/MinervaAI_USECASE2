import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useDarkMode } from '../contexts/DarkModeContext'
import { 
  Camera, 
  Upload, 
  Search, 
  ShoppingCart, 
  Store, 
  Wallet, 
  Package, 
  Bot, 
  TrendingDown, 
  CheckCircle, 
  AlertCircle, 
  X, 
  ArrowLeft,
  Loader2,
  Target,
  Sparkles,
  Moon,
  Sun
} from 'lucide-react'

const API_BASE_URL = 'http://localhost:8000'

function ShopGPTPage() {
  const { isDarkMode, toggleDarkMode } = useDarkMode()
  const [selectedMarket, setSelectedMarket] = useState('aziza')
  const [budget, setBudget] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [selectedImage, setSelectedImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [cart, setCart] = useState(null)
  const [error, setError] = useState(null)
  const [showCamera, setShowCamera] = useState(false)
  const [stream, setStream] = useState(null)
  const [addingToCart, setAddingToCart] = useState(false)
  const [quantity, setQuantity] = useState(1)
  const videoRef = useRef(null)
  const canvasRef = useRef(null)

  const markets = [
    { 
      id: 'aziza', 
      name: 'Aziza', 
      logo: '/logos/aziza.png'
    },
    { 
      id: 'carrefour', 
      name: 'Carrefour', 
      logo: '/logos/carrefour.png'
    },
    { 
      id: 'mg', 
      name: 'MG', 
      logo: '/logos/mg.png'
    },
    { 
      id: 'geant', 
      name: 'Géant', 
      logo: '/logos/geant.jpg'
    },
    { 
      id: 'monoprix', 
      name: 'Monoprix', 
      logo: '/logos/monoprix.png'
    },
    { 
      id: 'el_mazraa', 
      name: 'Mazraa Market', 
      logo: '/logos/Mazraa.png'
    }
  ]

  // Cleanup camera on unmount
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
      }
    }
  }, [stream])

  const startCamera = async () => {
    try {
      setError(null)
      setShowCamera(true)
      
      if (!navigator.mediaDevices?.getUserMedia) {
        setError('Camera not supported in this browser')
        setShowCamera(false)
        return
      }

      const constraints = {
        video: {
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      }

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
        setStream(mediaStream)
        
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play()
        }
      }
    } catch (err) {
      setShowCamera(false)
      let errorMsg = 'Camera error: '
      if (err.name === 'NotAllowedError') {
        errorMsg += 'Permission denied. Please allow camera access.'
      } else if (err.name === 'NotFoundError') {
        errorMsg += 'No camera found.'
      } else {
        errorMsg += err.message || 'Unknown error'
      }
      setError(errorMsg)
    }
  }

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
      if (videoRef.current) {
        videoRef.current.srcObject = null
      }
    }
    setShowCamera(false)
  }

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) {
      setError('Camera not ready')
      return
    }

    const video = videoRef.current
    const canvas = canvasRef.current

    if (video.videoWidth === 0) {
      setError('Video not ready, please wait')
      return
    }

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `product-${Date.now()}.jpg`, { type: 'image/jpeg' })
        setSelectedImage(file)
        
        const reader = new FileReader()
        reader.onloadend = () => {
          setImagePreview(reader.result)
        }
        reader.readAsDataURL(file)
        
        stopCamera()
      } else {
        setError('Failed to capture photo')
      }
    }, 'image/jpeg', 0.95)
  }

  const handleImageSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedImage(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setImagePreview(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    
    if (!selectedImage || !budget) {
      setError('Please select an image and enter your budget')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('image', selectedImage)
      formData.append('market', selectedMarket)
      formData.append('budget', budget)
      if (sessionId) {
        formData.append('session_id', sessionId)
      }

      const response = await axios.post(
        `${API_BASE_URL}/api/shopping/search-by-image`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
      
      if (response.data.product_not_found) {
        // Show both message and suggestion if available
        const errorMsg = response.data.message + 
          (response.data.suggestion ? `\n\n${response.data.suggestion}` : '')
        setError(errorMsg)
        setResults(null)
        return
      }
      
      setResults(response.data)
      setCart(response.data.cart)
      setSessionId(response.data.session_id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleAddToCart = async () => {
    if (!results || !results.product || !sessionId) {
      setError('No product to add to cart')
      return
    }

    setAddingToCart(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('session_id', sessionId)
      formData.append('product_id', results.product.id)
      formData.append('product_name', results.product.name)
      formData.append('product_price', results.product.price)
      formData.append('product_market', results.product.market)
      formData.append('product_description', results.product.description || '')
      formData.append('quantity', quantity)

      const response = await axios.post(
        `${API_BASE_URL}/api/shopping/cart/add`,
        formData
      )
      
      setCart(response.data.cart)
      
      setTimeout(() => {
        setResults(null)
        setSelectedImage(null)
        setImagePreview(null)
        setQuantity(1) // Reset quantity
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add to cart')
    } finally {
      setAddingToCart(false)
    }
  }

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      isDarkMode 
        ? 'bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800' 
        : 'bg-gradient-to-br from-foam via-white to-dinero-50'
    }`}>
      {/* Header */}
      <div className={`backdrop-blur-md shadow-lg sticky top-0 z-50 transition-colors duration-300 ${
        isDarkMode 
          ? 'bg-slate-900/90 border-slate-700' 
          : 'bg-white/80 border-dinero-100'
      } border-b`}>
        <div className="max-w-7xl mx-auto px-6 py-3">
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
              <img 
                src="/dinero.png" 
                alt="Dinero Logo" 
                className="h-20 w-auto rounded-xl object-contain"
              />
              <div>
                <h1 className={`text-2xl font-extrabold tracking-tight ${
                  isDarkMode ? 'text-white' : 'text-slate-900'
                }`}>Dinero VISION</h1>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {cart && cart.items && cart.items.length > 0 && (
                <div className={`flex items-center gap-3 px-5 py-3 rounded-full border-2 ${
                  isDarkMode 
                    ? 'bg-slate-800 border-slate-600' 
                    : 'bg-dinero-50 border-dinero-200'
                }`}>
                  <ShoppingCart className={`w-5 h-5 ${isDarkMode ? 'text-slate-300' : 'text-dinero-600'}`} />
                  <div className="text-left">
                    <div className={`text-xs font-medium ${isDarkMode ? 'text-slate-400' : 'text-slate-500'}`}>Cart Total</div>
                    <div className={`text-lg font-bold ${isDarkMode ? 'text-white' : 'text-dinero-600'}`}>{cart.total.toFixed(2)} TND</div>
                  </div>
                </div>
              )}
              
              <button
                onClick={toggleDarkMode}
                className={`p-2 rounded-lg transition-colors ${
                  isDarkMode 
                    ? 'text-slate-300 hover:text-white hover:bg-slate-800' 
                    : 'text-dinero-600 hover:bg-dinero-50'
                }`}
              >
                {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Search Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSearch} className="bg-white rounded-3xl shadow-2xl border border-slate-100 p-8 space-y-8 hover:shadow-3xl transition-shadow">
              {/* Market Selection */}
              <div>
                <label className="block text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Store className="w-5 h-5 text-dinero-600" />
                  <span>Select Supermarket</span>
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {markets.map(market => (
                    <button
                      key={market.id}
                      type="button"
                      onClick={() => setSelectedMarket(market.id)}
                      disabled={loading}
                      className={`p-5 rounded-2xl border-2 transition-all transform hover:scale-105 ${
                        selectedMarket === market.id
                          ? 'border-dinero-500 bg-gradient-to-br from-dinero-50 to-dinero-100 shadow-lg scale-105'
                          : 'border-slate-200 hover:border-dinero-300 hover:bg-slate-50'
                      }`}
                    >
                      <div className="h-16 flex items-center justify-center mb-3">
                        <img 
                          src={market.logo} 
                          alt={market.name}
                          className="max-h-full max-w-full object-contain"
                        />
                      </div>
                      <div className="text-sm font-bold text-slate-800">{market.name}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Budget Input */}
              <div>
                <label htmlFor="budget" className="block text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Wallet className="w-5 h-5 text-dinero-600" />
                  <span>Shopping Budget</span>
                </label>
                <div className="relative">
                  <Wallet className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-dinero-500" />
                  <input
                    id="budget"
                    type="number"
                    placeholder="Enter your budget"
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                    disabled={loading}
                    min="0"
                    step="0.01"
                    className="w-full pl-16 pr-20 py-5 rounded-2xl border-2 border-slate-200 focus:border-dinero-500 focus:ring-4 focus:ring-dinero-50 outline-none transition-all text-lg font-semibold bg-slate-50 focus:bg-white"
                  />
                  <span className="absolute right-6 top-1/2 -translate-y-1/2 text-slate-500 font-bold text-lg">
                    TND
                  </span>
                </div>
              </div>

              {/* Image Capture */}
              <div>
                <label className="block text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Camera className="w-5 h-5 text-dinero-600" />
                  <span>Product Photo</span>
                </label>
                
                {!imagePreview && !showCamera && (
                  <div className="space-y-4">
                    <button
                      type="button"
                      onClick={startCamera}
                      disabled={loading}
                      className="w-full py-5 px-6 bg-gradient-to-r from-dinero-500 to-dinero-600 text-white rounded-2xl font-bold hover:from-dinero-600 hover:to-dinero-700 transition-all shadow-xl hover:shadow-2xl flex items-center justify-center gap-3 transform hover:scale-[1.02]"
                    >
                      <Camera className="w-7 h-7" />
                      <span className="text-lg">Take Photo</span>
                    </button>
                    
                    <div className="relative">
                      <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-slate-200"></div>
                      </div>
                      <div className="relative flex justify-center text-sm">
                        <span className="px-4 bg-white text-slate-500 font-medium">or</span>
                      </div>
                    </div>
                    
                    <label className="block w-full py-5 px-6 bg-white border-2 border-dinero-400 text-dinero-600 rounded-2xl font-bold hover:bg-dinero-50 transition-all cursor-pointer text-center shadow-lg hover:shadow-xl transform hover:scale-[1.02]">
                      <Upload className="w-7 h-7 inline-block mr-3" />
                      <span className="text-lg">Upload Photo</span>
                      <input
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handleImageSelect}
                        disabled={loading}
                        className="hidden"
                      />
                    </label>
                  </div>
                )}

                {/* Camera View */}
                {showCamera && (
                  <div className="relative rounded-3xl overflow-hidden bg-black shadow-2xl border-4 border-dinero-500">
                    <video 
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-96 object-cover"
                    />
                    <canvas ref={canvasRef} className="hidden" />
                    
                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                      <div className="w-72 h-72 border-4 border-dinero-400 rounded-3xl shadow-2xl animate-pulse"></div>
                      <p className="mt-6 text-white bg-black/70 px-6 py-3 rounded-full text-sm font-bold backdrop-blur-sm flex items-center gap-2">
                        <Package className="w-4 h-4" />
                        <span>Position product within frame</span>
                      </p>
                    </div>
                    
                    <div className="absolute bottom-8 left-0 right-0 flex justify-center gap-4 pointer-events-auto">
                      <button
                        type="button"
                        onClick={capturePhoto}
                        className="w-20 h-20 bg-white rounded-full shadow-2xl hover:scale-110 transition-transform flex items-center justify-center border-4 border-dinero-500"
                      >
                        <Camera className="w-10 h-10 text-dinero-600" />
                      </button>
                      <button
                        type="button"
                        onClick={stopCamera}
                        className="px-8 py-4 bg-red-500 text-white rounded-full shadow-2xl hover:bg-red-600 transition-all font-bold text-lg flex items-center gap-2"
                      >
                        <X className="w-5 h-5" />
                        <span>Cancel</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* Image Preview */}
                {imagePreview && !showCamera && (
                  <div className="relative rounded-3xl overflow-hidden border-4 border-dinero-300 shadow-2xl bg-gradient-to-br from-dinero-50 to-white p-2">
                    <img src={imagePreview} alt="Selected product" className="w-full h-96 object-contain rounded-2xl bg-white" />
                    <div className="absolute top-6 right-6 flex gap-2">
                      <div className="px-4 py-2 bg-green-500 text-white rounded-full font-bold text-sm shadow-lg flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" />
                        <span>Ready</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedImage(null)
                          setImagePreview(null)
                        }}
                        className="w-12 h-12 bg-red-500 text-white rounded-full shadow-xl hover:bg-red-600 transition-all flex items-center justify-center hover:scale-110"
                      >
                        <X className="w-6 h-6" />
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Search Button */}
              <button 
                type="submit" 
                disabled={loading || !selectedImage || !budget}
                className="w-full py-6 px-8 bg-gradient-to-r from-dinero-500 via-dinero-600 to-viridian text-white rounded-2xl font-extrabold text-xl hover:shadow-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-4 transform hover:scale-[1.02] shadow-xl"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-7 h-7 animate-spin" />
                    <span>Searching for best prices...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-7 h-7" />
                    <span>Find Best Price</span>
                  </>
                )}
              </button>

              {/* Error Message */}
              {error && (
                <div className="p-5 bg-red-50 border-2 border-red-300 rounded-2xl text-red-700 flex items-start gap-4 shadow-lg animate-pulse">
                  <AlertCircle className="w-6 h-6 flex-shrink-0 mt-0.5" />
                  <span className="font-semibold">{error}</span>
                </div>
              )}
            </form>

            {/* Results */}
            {results && results.product && (
              <div className="mt-8 bg-gradient-to-br from-white to-dinero-50 rounded-3xl shadow-2xl border-2 border-dinero-200 p-8 space-y-6 animate-fadeIn">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-3xl font-extrabold text-slate-900 flex items-center gap-3">
                      <Sparkles className="w-8 h-8 text-dinero-600" />
                      <span>Product Found!</span>
                    </h2>
                    <div className="flex gap-2 mt-3">
                      <span className={`px-4 py-2 rounded-full text-sm font-bold shadow-md flex items-center gap-2 ${
                        results.within_budget ? 'bg-green-500 text-white' : 'bg-orange-500 text-white'
                      }`}>
                        {results.within_budget ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                        <span>{results.budget_status}</span>
                      </span>
                      <span className="px-4 py-2 rounded-full text-sm font-bold bg-dinero-500 text-white shadow-md flex items-center gap-2">
                        <Target className="w-4 h-4" />
                        <span>{(results.match_confidence * 100).toFixed(0)}% Match</span>
                      </span>
                    </div>
                  </div>
                  <div className="text-right bg-white rounded-2xl p-4 shadow-lg border-2 border-dinero-300">
                    <div className="text-4xl font-extrabold text-dinero-600">{results.product.price.toFixed(2)} TND</div>
                    <div className="text-sm text-slate-500 font-semibold">per unit</div>
                  </div>
                </div>

                <div className="bg-white rounded-2xl p-6 shadow-md border border-slate-100">
                  <h3 className="text-2xl font-extrabold text-slate-900">{results.product.name}</h3>
                  <div className="flex gap-2 mt-3">
                    <span className="px-4 py-2 rounded-full text-sm font-bold bg-dinero-500 text-white shadow-md flex items-center gap-2">
                      <Store className="w-4 h-4" />
                      <span>{results.product.market}</span>
                    </span>
                    {results.product.brand && (
                      <span className="px-4 py-2 rounded-full text-sm font-bold bg-slate-700 text-white shadow-md flex items-center gap-2">
                        <span>🏷️</span>
                        <span>{results.product.brand}</span>
                      </span>
                    )}
                  </div>
                  <p className="mt-4 text-slate-600 font-medium leading-relaxed">{results.product.description}</p>
                  
                  {/* Quantity Selector */}
                  <div className="mt-6 p-4 bg-dinero-50 rounded-xl border-2 border-dinero-200">
                    <label className="block text-sm font-bold text-slate-800 mb-3">Quantity</label>
                    <div className="flex items-center gap-4">
                      <button
                        type="button"
                        onClick={() => setQuantity(Math.max(1, quantity - 1))}
                        className="w-12 h-12 rounded-full bg-white border-2 border-dinero-300 text-dinero-600 font-bold text-xl hover:bg-dinero-100 transition-all shadow-md"
                      >
                        −
                      </button>
                      <input
                        type="number"
                        min="1"
                        value={quantity}
                        onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                        className="w-20 h-12 text-center text-2xl font-bold border-2 border-dinero-300 rounded-xl focus:border-dinero-500 focus:ring-2 focus:ring-dinero-200 outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => setQuantity(quantity + 1)}
                        className="w-12 h-12 rounded-full bg-white border-2 border-dinero-300 text-dinero-600 font-bold text-xl hover:bg-dinero-100 transition-all shadow-md"
                      >
                        +
                      </button>
                      <div className="ml-auto text-right">
                        <div className="text-xs text-slate-500 font-semibold">Total</div>
                        <div className="text-2xl font-extrabold text-dinero-600">
                          {(results.product.price * quantity).toFixed(2)} TND
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {results.recommendation && (
                  <div className="p-6 bg-gradient-to-br from-dinero-100 via-shadow-green/30 to-dinero-50 rounded-2xl border-2 border-dinero-300 shadow-lg">
                    <h4 className="font-extrabold text-slate-900 mb-3 flex items-center gap-2 text-lg">
                      <Bot className="w-6 h-6 text-dinero-600" />
                      <span>AI Recommendation</span>
                    </h4>
                    <p className="text-slate-800 font-medium leading-relaxed bg-white rounded-xl p-4 shadow-md">{results.recommendation}</p>
                  </div>
                )}

                {results.alternatives && results.alternatives.length > 0 && (
                  <div className="p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-2xl border-2 border-green-300 shadow-lg">
                    <h4 className="font-extrabold text-slate-900 mb-5 flex items-center gap-2 text-lg">
                      <TrendingDown className="w-6 h-6 text-green-600" />
                      <span>Cheaper Alternative Found!</span>
                    </h4>
                    <div className="space-y-3">
                      {results.alternatives.map((alt, idx) => (
                        <div key={idx} className="flex items-center justify-between p-5 bg-white rounded-2xl shadow-md hover:shadow-lg transition-shadow">
                          <div>
                            <div className="font-bold text-slate-900 text-lg">{alt.product.name}</div>
                            <div className="text-sm text-slate-600 font-semibold mt-1 flex items-center gap-2">
                              <Store className="w-4 h-4" />
                              <span>{alt.product.market} • {alt.product.price.toFixed(2)} TND</span>
                            </div>
                          </div>
                          <div className="px-5 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-full font-extrabold text-sm shadow-lg flex items-center gap-2">
                            <TrendingDown className="w-4 h-4" />
                            <span>Save {alt.savings.toFixed(2)} TND</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cross-Market Recommendations */}
                {results.cross_market_recommendations && results.cross_market_recommendations.length > 0 && (
                  <div className="p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl border-2 border-blue-300 shadow-lg">
                    <h4 className="font-extrabold text-slate-900 mb-3 flex items-center gap-2 text-lg">
                      <Store className="w-6 h-6 text-blue-600" />
                      <span>Available in Other Markets</span>
                    </h4>
                    <p className="text-slate-600 text-sm mb-4 leading-relaxed">
                      We found this product in other supermarkets. Compare prices to get the best deal!
                    </p>
                    <div className="space-y-3">
                      {results.cross_market_recommendations.map((rec, idx) => (
                        <div key={idx} className="flex items-center justify-between p-4 bg-white rounded-xl shadow-md hover:shadow-lg transition-all">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
                              <Store className="w-6 h-6 text-blue-600" />
                            </div>
                            <div>
                              <div className="font-bold text-slate-900">{rec.market}</div>
                              <div className="text-xs text-slate-500 font-semibold">{rec.product_name}</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-xl font-extrabold text-blue-600">{rec.price.toFixed(2)} TND</div>
                            {rec.price_difference && (
                              <div className={`text-xs font-bold ${rec.price_difference > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                {rec.price_difference > 0 ? '+' : ''}{rec.price_difference.toFixed(2)} TND
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button 
                  onClick={handleAddToCart}
                  disabled={addingToCart}
                  className="w-full py-6 px-8 bg-gradient-to-r from-dinero-500 via-dinero-600 to-viridian text-white rounded-2xl font-extrabold text-xl hover:shadow-2xl transition-all shadow-xl disabled:opacity-50 flex items-center justify-center gap-4 transform hover:scale-[1.02]"
                >
                  {addingToCart ? (
                    <>
                      <Loader2 className="w-7 h-7 animate-spin" />
                      <span>Adding to cart...</span>
                    </>
                  ) : (
                    <>
                      <ShoppingCart className="w-7 h-7" />
                      <span>Add to Cart</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Right Column - Cart */}
          <div className="lg:col-span-1">
            {cart && cart.items && cart.items.length > 0 && (
              <div className="bg-gradient-to-br from-white to-dinero-50 rounded-3xl shadow-2xl border-2 border-dinero-200 p-7 sticky top-24">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-extrabold text-slate-900 flex items-center gap-3">
                    <ShoppingCart className="w-7 h-7 text-dinero-600" />
                    <span>Your Cart</span>
                  </h3>
                  <span className="px-4 py-2 bg-gradient-to-r from-dinero-500 to-dinero-600 text-white rounded-full font-bold text-sm shadow-lg">
                    {cart.items.length} {cart.items.length === 1 ? 'item' : 'items'}
                  </span>
                </div>
                
                <div className="space-y-3 mb-6">
                  {cart.items.map((item, idx) => (
                    <div key={idx} className="p-5 bg-white rounded-2xl shadow-md border border-slate-100 hover:shadow-lg transition-shadow">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <div className="font-bold text-slate-900">{item.product.name}</div>
                          <div className="text-xs text-slate-500 mt-1 font-semibold flex items-center gap-1">
                            <Store className="w-3 h-3" />
                            <span>{item.product.market}</span>
                          </div>
                        </div>
                        <div className="text-lg font-extrabold text-dinero-600 bg-dinero-50 px-3 py-1 rounded-full">×{item.quantity}</div>
                      </div>
                      <div className="flex justify-between items-center pt-3 border-t border-slate-100">
                        <div className="text-xs text-slate-500 font-semibold">{item.product.price.toFixed(2)} TND each</div>
                        <div className="font-extrabold text-dinero-600 text-lg">{item.subtotal.toFixed(2)} TND</div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="space-y-4 pt-5 border-t-2 border-dinero-200">
                  <div className="flex justify-between text-sm bg-slate-50 p-3 rounded-xl">
                    <span className="text-slate-600 font-semibold">Subtotal</span>
                    <span className="font-bold">{(cart.total - (cart.items.length > 0 ? 0.1 : 0)).toFixed(2)} TND</span>
                  </div>
                  
                  {cart.items.length > 0 && (
                    <div className="flex justify-between text-sm bg-blue-50 p-3 rounded-xl border border-blue-200">
                      <span className="text-blue-700 font-semibold">Droit de timbre</span>
                      <span className="font-bold text-blue-700">0.10 TND</span>
                    </div>
                  )}
                  
                  <div className="flex justify-between text-xl font-extrabold bg-dinero-100 p-4 rounded-xl">
                    <span>Total</span>
                    <span className="text-dinero-600">{cart.total.toFixed(2)} TND</span>
                  </div>
                  <div className="flex justify-between text-sm bg-slate-50 p-3 rounded-xl">
                    <span className="text-slate-600 font-semibold">Budget</span>
                    <span className="font-bold">{cart.budget.toFixed(2)} TND</span>
                  </div>
                  <div className={`flex justify-between text-base font-extrabold p-4 rounded-xl shadow-md ${
                    cart.is_over_budget ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                  }`}>
                    <span className="flex items-center gap-2">
                      {cart.is_over_budget ? (
                        <>
                          <AlertCircle className="w-5 h-5" />
                          <span>Over Budget</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-5 h-5" />
                          <span>Remaining</span>
                        </>
                      )}
                    </span>
                    <span>{Math.abs(cart.remaining).toFixed(2)} TND</span>
                  </div>
                </div>
              </div>
            )}

            {/* Cart message removed - no longer displayed */}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ShopGPTPage
