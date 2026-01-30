import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { DarkModeProvider, useDarkMode } from './contexts/DarkModeContext'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import B2CPage from './pages/B2CPage'
import B2BPage from './pages/B2BPage'
import UsershopPage from './pages/UsershopPage'
import ShopGPTPage from './pages/ShopGPTPage'

function AppContent() {
  const { isDarkMode } = useDarkMode()
  
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/b2c" element={<B2CPage />} />
          <Route path="/b2b" element={<B2BPage />} />
          <Route path="/usershop" element={<UsershopPage />} />
          <Route path="/shopgpt" element={<ShopGPTPage />} />
        </Routes>
      </Layout>
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme={isDarkMode ? "dark" : "light"}
      />
    </Router>
  )
}

function App() {
  return (
    <DarkModeProvider>
      <AppContent />
    </DarkModeProvider>
  )
}

export default App
