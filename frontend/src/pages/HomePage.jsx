import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useDarkMode } from '../contexts/DarkModeContext'
import { 
  ShoppingCart, 
  Building2, 
  Store, 
  Camera, 
  ArrowRight, 
  Zap, 
  Shield, 
  TrendingUp, 
  Users, 
  Globe, 
  Clock, 
  Star, 
  CheckCircle,
  Search,
  Brain,
  Target,
  BarChart3,
  Sparkles,
  Award,
  Heart,
  Moon,
  Sun,
  Menu,
  X
} from 'lucide-react'

const HomePage = () => {
  const { isDarkMode, toggleDarkMode } = useDarkMode()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const services = [
    {
      title: 'Dinero Orbit',
      description: 'Real-time product scraping from Amazon, Alibaba, Walmart, and Cdiscount with AI-powered recommendations and price comparison',
      icon: ShoppingCart,
      path: '/b2c',
      color: 'bg-de-york',
      features: ['Real-time Scraping', 'Price Comparison', 'AI Recommendations']
    },
    {
      title: 'Dinero Prime',
      description: 'Connect with verified suppliers worldwide, optimize procurement costs, and get personalized business recommendations',
      icon: Building2,
      path: '/b2b',
      color: 'bg-silver-tree',
      features: ['Verified Suppliers', 'Cost Optimization', 'Bulk Pricing']
    },
    {
      title: 'DineroShop',
      description: 'Advanced product catalog management with CSV import, intelligent filtering, and AI-powered product comparisons',
      icon: Store,
      path: '/usershop',
      color: 'bg-moss-green',
      features: ['CSV Import', 'Smart Filtering', 'Product Comparison']
    },
    {
      title: 'Dinero VISION',
      description: 'Revolutionary image-based product search using computer vision, OCR technology, and natural language processing',
      icon: Camera,
      path: '/shopgpt',
      color: 'bg-pixie-green',
      features: ['Image Recognition', 'OCR Technology', 'Visual Search']
    },
  ]

  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Intelligence',
      description: 'Advanced machine learning algorithms provide personalized recommendations and insights'
    },
    {
      icon: Zap,
      title: 'Lightning Fast',
      description: 'Optimized performance with sub-3 second response times across all services'
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Bank-level security with encrypted data transmission and secure API endpoints'
    },
    {
      icon: Globe,
      title: 'Global Marketplace',
      description: 'Access to international suppliers and products from major e-commerce platforms'
    }
  ]

  const stats = [
    { icon: Target, value: '1M+', label: 'Products Indexed', color: 'text-de-york' },
    { icon: Users, value: '50K+', label: 'Active Users', color: 'text-silver-tree' },
    { icon: Globe, value: '25+', label: 'Countries Served', color: 'text-moss-green' },
    { icon: Star, value: '4.9', label: 'User Rating', color: 'text-pixie-green' }
  ]

  return (
    <div className={`min-h-screen font-sans selection:bg-dinero-100 transition-colors duration-300 ${
      isDarkMode 
        ? 'bg-slate-900 text-slate-100' 
        : 'bg-white text-slate-900'
    }`}>
      
      {/* Header */}
      <header className={`sticky top-0 z-50 backdrop-blur-md transition-colors duration-300 ${
        isDarkMode 
          ? 'bg-slate-900/90 border-slate-700' 
          : 'bg-white/90 border-slate-200'
      } border-b`}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <img 
                src="/dinero.png" 
                alt="Dinero Logo" 
                className="h-10 w-auto rounded-lg object-contain"
              />
              <h1 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-viridian'}`}>
                Dinero Platform
              </h1>
            </div>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-8">
              {services.map((service) => (
                <Link
                  key={service.path}
                  to={service.path}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                    isDarkMode 
                      ? 'text-slate-300 hover:text-white hover:bg-slate-800' 
                      : 'text-viridian/70 hover:text-viridian hover:bg-foam'
                  }`}
                >
                  <service.icon size={18} />
                  <span className="font-medium">{service.title}</span>
                </Link>
              ))}
            </nav>
            
            {/* Dark Mode Toggle & Mobile Menu */}
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleDarkMode}
                className={`p-2 rounded-lg transition-colors ${
                  isDarkMode 
                    ? 'text-slate-300 hover:text-white hover:bg-slate-800' 
                    : 'text-viridian hover:bg-foam'
                }`}
              >
                {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
              </button>
              
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className={`md:hidden p-2 rounded-lg transition-colors ${
                  isDarkMode 
                    ? 'text-slate-300 hover:text-white hover:bg-slate-800' 
                    : 'text-viridian hover:bg-foam'
                }`}
              >
                {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>
          
          {/* Mobile Navigation */}
          {isMobileMenuOpen && (
            <nav className="md:hidden mt-4 pb-4 border-t border-slate-200 dark:border-slate-700">
              <div className="flex flex-col space-y-2 mt-4">
                {services.map((service) => (
                  <Link
                    key={service.path}
                    to={service.path}
                    className={`flex items-center space-x-3 px-3 py-3 rounded-lg transition-colors ${
                      isDarkMode 
                        ? 'text-slate-300 hover:text-white hover:bg-slate-800' 
                        : 'text-viridian/70 hover:text-viridian hover:bg-foam'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <service.icon size={20} />
                    <span className="font-medium">{service.title}</span>
                  </Link>
                ))}
              </div>
            </nav>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <div className={`relative overflow-hidden py-20 transition-colors duration-300 ${
        isDarkMode 
          ? 'bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800' 
          : 'bg-gradient-to-br from-foam via-white to-dinero-50'
      }`}>
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center space-y-6">
            <div className="flex justify-center mb-8">
              <img 
                src="/dinero.png" 
                alt="Dinero Logo" 
                className="h-32 w-auto rounded-2xl object-contain shadow-2xl hover:scale-105 transition-transform"
              />
            </div>
            <h1 className={`text-6xl font-extrabold tracking-tight ${
              isDarkMode ? 'text-white' : 'text-viridian'
            }`}>
              Dinero Platform
            </h1>
            <p className={`text-2xl max-w-3xl mx-auto leading-relaxed ${
              isDarkMode ? 'text-slate-300' : 'text-viridian/80'
            }`}>
              Transform your shopping experience with our comprehensive AI-powered platform. 
              Discover, compare, and purchase products with unprecedented intelligence and efficiency.
            </p>
            <div className="flex justify-center space-x-4 mt-8">
              <div className={`flex items-center space-x-2 backdrop-blur-sm px-4 py-2 rounded-full ${
                isDarkMode ? 'bg-slate-800/80' : 'bg-white/80'
              }`}>
                <Sparkles className={isDarkMode ? 'text-slate-300' : 'text-viridian'} size={20} />
                <span className={`font-semibold ${isDarkMode ? 'text-slate-300' : 'text-viridian'}`}>AI-Powered</span>
              </div>
              <div className={`flex items-center space-x-2 backdrop-blur-sm px-4 py-2 rounded-full ${
                isDarkMode ? 'bg-slate-800/80' : 'bg-white/80'
              }`}>
                <Award className={isDarkMode ? 'text-slate-300' : 'text-viridian'} size={20} />
                <span className={`font-semibold ${isDarkMode ? 'text-slate-300' : 'text-viridian'}`}>Enterprise Grade</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Background Wave */}
        <div className="absolute bottom-0 left-0 w-full -z-10 opacity-20 pointer-events-none">
          <svg viewBox="0 0 1440 320" xmlns="http://www.w3.org/2000/svg">
            <path
              fill="#51ae93"
              fillOpacity="1"
              d="M0,224L48,213.3C96,203,192,181,288,181.3C384,181,480,203,576,224C672,245,768,267,864,250.7C960,235,1056,181,1152,154.7C1248,128,1344,128,1392,128L1440,128V320H1392C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320H0Z"
            ></path>
          </svg>
        </div>
      </div>

      {/* Services Grid */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-16">
          <h2 className={`text-4xl font-bold mb-4 ${isDarkMode ? 'text-white' : 'text-viridian'}`}>Our Services</h2>
          <p className={`text-xl max-w-2xl mx-auto ${isDarkMode ? 'text-slate-400' : 'text-viridian/70'}`}>
            Choose from our specialized AI-powered services designed to meet your unique shopping and business needs
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 gap-8">
          {services.map((service) => (
            <Link
              key={service.path}
              to={service.path}
              className={`group rounded-3xl shadow-xl hover:shadow-2xl transition-all p-8 border-2 border-transparent transform hover:-translate-y-1 ${
                isDarkMode 
                  ? 'bg-slate-800 hover:border-slate-600' 
                  : 'bg-white hover:border-viridian'
              }`}
            >
              <div className="flex items-start space-x-6">
                <div className={`${service.color} p-4 rounded-2xl shadow-lg group-hover:scale-110 transition-transform`}>
                  <service.icon className="text-white" size={40} />
                </div>
                <div className="flex-1">
                  <h3 className={`text-3xl font-bold mb-3 ${isDarkMode ? 'text-white' : 'text-viridian'}`}>
                    {service.title}
                  </h3>
                  <p className={`mb-4 leading-relaxed ${isDarkMode ? 'text-slate-400' : 'text-viridian/70'}`}>
                    {service.description}
                  </p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {service.features.map((feature, index) => (
                      <span key={index} className={`px-3 py-1 rounded-full text-sm font-medium ${
                        isDarkMode 
                          ? 'bg-slate-700 text-slate-300' 
                          : 'bg-foam text-viridian'
                      }`}>
                        {feature}
                      </span>
                    ))}
                  </div>
                  <div className={`flex items-center font-bold group-hover:translate-x-2 transition-transform ${
                    isDarkMode ? 'text-slate-300' : 'text-silver-tree'
                  }`}>
                    <span>Explore Service</span>
                    <ArrowRight size={20} className="ml-2" />
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Features Section */}
      <div className={`py-20 transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-800' : 'bg-foam'
      }`}>
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className={`text-4xl font-bold mb-4 ${isDarkMode ? 'text-white' : 'text-viridian'}`}>Why Choose Dinero?</h2>
            <p className={`text-xl max-w-2xl mx-auto ${isDarkMode ? 'text-slate-400' : 'text-viridian/70'}`}>
              Built with cutting-edge technology to deliver exceptional performance and user experience
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div key={index} className={`rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow ${
                isDarkMode ? 'bg-slate-700' : 'bg-white'
              }`}>
                <div className={`p-3 rounded-xl w-fit mb-4 ${
                  isDarkMode ? 'bg-slate-600' : 'bg-viridian/10'
                }`}>
                  <feature.icon className={isDarkMode ? 'text-slate-300' : 'text-viridian'} size={32} />
                </div>
                <h3 className={`text-xl font-bold mb-3 ${isDarkMode ? 'text-white' : 'text-viridian'}`}>{feature.title}</h3>
                <p className={`leading-relaxed ${isDarkMode ? 'text-slate-400' : 'text-viridian/70'}`}>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="max-w-7xl mx-auto px-6 pb-20">
        <div className="bg-gradient-to-br from-viridian to-silver-tree rounded-3xl shadow-2xl p-12 text-white">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">Global Impact</h2>
            <p className="text-white/80 text-lg max-w-2xl mx-auto">
              Trusted by thousands of users worldwide, delivering exceptional results across all markets
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center group">
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 hover:bg-white/20 transition-colors">
                  <div className="flex justify-center mb-4">
                    <stat.icon size={40} className="text-white group-hover:scale-110 transition-transform" />
                  </div>
                  <div className="text-4xl font-bold mb-2">{stat.value}</div>
                  <div className="text-white/80 font-semibold">{stat.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className={`py-12 px-6 transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-800 text-slate-400' : 'bg-slate-900 text-slate-400'
      }`}>
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8">
            {/* Company Info */}
            <div>
              <div className="flex items-center mb-4">
                <img 
                  src="/dinero.png" 
                  alt="Dinero Logo" 
                  className="h-14 w-auto rounded-xl object-contain shadow-md"
                />
              </div>
              <p className="text-sm leading-relaxed">
                Intelligent shopping platform connecting users with the best products and deals across global marketplaces.
              </p>
            </div>
            
            {/* Services */}
            <div>
              <h4 className="text-white font-bold mb-4">Our Services</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/b2c" className="hover:text-white transition-colors">
                    Dinero Orbit
                  </Link>
                </li>
                <li>
                  <Link to="/b2b" className="hover:text-white transition-colors">
                    Dinero Prime
                  </Link>
                </li>
                <li>
                  <Link to="/usershop" className="hover:text-white transition-colors">
                    DineroShop
                  </Link>
                </li>
                <li>
                  <Link to="/shopgpt" className="hover:text-white transition-colors">
                    Dinero VISION
                  </Link>
                </li>
              </ul>
            </div>
            
            {/* Company */}
            <div>
              <h4 className="text-white font-bold mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li>Founded in 2024</li>
                <li>AI-First Approach</li>
                <li>Global Reach</li>
                <li>Customer Focused</li>
              </ul>
            </div>
          </div>
          
          <div className="mt-12 pt-8 border-t border-slate-800 text-center text-sm">
            <p className="flex items-center justify-center space-x-2">
              <span>Built with</span>
              <Heart size={16} className="text-red-400" />
              <span>© 2026 Dinero Platform. All rights reserved.</span>
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default HomePage
