import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { toast } from 'react-toastify'
import { useDarkMode } from '../contexts/DarkModeContext'
import { usershopAPI } from '../utils/api'
import SearchForm from '../components/SearchForm'
import RecommendationResults from '../components/RecommendationResults'
import { ArrowLeft, Moon, Sun, Store } from 'lucide-react'

const UsershopPage = () => {
  const navigate = useNavigate()
  const { isDarkMode, toggleDarkMode } = useDarkMode()
  const [recommendations, setRecommendations] = useState(null)
  const [loadingRecommendations, setLoadingRecommendations] = useState(false)

  const handleSearch = async (searchData) => {
    setLoadingRecommendations(true)
    setRecommendations(null)

    try {
      console.log('Sending search data:', searchData)
      const response = await usershopAPI.recommend(searchData)
      console.log('Received recommendations:', response.data)
      setRecommendations(response.data)
      toast.success('💎 Recommendations generated successfully!')
    } catch (error) {
      console.error('Error generating recommendations:', error)
      let errorMessage = 'Error generating recommendations'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      toast.error(errorMessage)
    } finally {
      setLoadingRecommendations(false)
    }
  }

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      isDarkMode 
        ? 'bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800' 
        : 'bg-gradient-to-br from-foam via-white to-dinero-50'
    }`}>
      {/* Header */}
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
                }`}>DineroShop</h1>
                <p className={`text-sm ${
                  isDarkMode ? 'text-slate-400' : 'text-slate-600'
                }`}>Product Catalog Management</p>
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

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className={`rounded-xl shadow-md p-6 mb-6 ${
          isDarkMode ? 'bg-slate-800' : 'bg-white'
        }`}>
          <h2 className={`text-3xl font-bold mb-4 flex items-center gap-3 ${
            isDarkMode ? 'text-white' : 'text-viridian'
          }`}>
            <Store className="w-8 h-8" />
            Search Products and Get Recommendations
          </h2>
          <p className={isDarkMode ? 'text-slate-400' : 'text-viridian/70'}>
            Advanced product catalog management with CSV import, intelligent filtering, and AI-powered product comparisons
          </p>
        </div>

        {/* Search Form */}
        <SearchForm onSearch={handleSearch} loading={loadingRecommendations} />

        {/* Recommendation Results */}
        <RecommendationResults results={recommendations} />
      </div>
    </div>
  )
}

export default UsershopPage
