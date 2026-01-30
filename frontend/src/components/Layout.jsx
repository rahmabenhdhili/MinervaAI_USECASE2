import { Link, useLocation } from 'react-router-dom'
import { ShoppingCart, Building2, Store, Camera, Home } from 'lucide-react'

const Layout = ({ children }) => {
  const location = useLocation()
  const isHomePage = location.pathname === '/'
  const isShopGPTPage = location.pathname === '/shopgpt'
  const isB2BPage = location.pathname === '/b2b'
  const isUsershopPage = location.pathname === '/usershop'
  const isB2CPage = location.pathname === '/b2c'

  const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/b2c', label: 'B2C Marketplace', icon: ShoppingCart },
    { path: '/b2b', label: 'B2B Suppliers', icon: Building2 },
    { path: '/usershop', label: 'Usershop', icon: Store },
    { path: '/shopgpt', label: 'ShopGPT', icon: Camera },
  ]

  // If homepage, ShopGPT page, B2B page, B2C page, or Usershop page, render children without layout
  if (isHomePage || isShopGPTPage || isB2BPage || isB2CPage || isUsershopPage) {
    return <>{children}</>
  }

  return (
    <div className="min-h-screen bg-foam">
      {/* Header */}
      <header className="bg-viridian text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-silver-tree rounded-lg flex items-center justify-center">
                <span className="text-2xl font-bold">M</span>
              </div>
              <span className="text-2xl font-bold">Dinero</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-shadow-green border-b border-viridian/20">
        <div className="container mx-auto px-4">
          <div className="flex space-x-1">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-2 px-4 py-3 transition-colors ${
                  location.pathname === path
                    ? 'bg-viridian text-white border-b-2 border-silver-tree'
                    : 'text-viridian hover:bg-pixie-green'
                }`}
              >
                <Icon size={18} />
                <span className="font-medium">{label}</span>
              </Link>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-viridian text-white mt-16">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center">
            <p className="text-sm">© 2026 Dinero Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout
