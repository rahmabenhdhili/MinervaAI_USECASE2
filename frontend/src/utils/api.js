import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour gérer les erreurs
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Erreur API:', error);
    return Promise.reject(error);
  }
);

export const productAPI = {
  // Obtenir des recommandations
  getRecommendations: async (searchData) => {
    const response = await api.post('/usershop/recommend', searchData);
    return response.data;
  },

  // Rechercher des produits
  searchProducts: async (query, limit = 5) => {
    const response = await api.post('/usershop/search', { query, limit });
    return response.data;
  },

  // Obtenir un produit par ID
  getProductById: async (productId) => {
    const response = await api.get(`/usershop/product/${productId}`);
    return response.data;
  },

  // Charger des produits depuis un CSV
  uploadCSV: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/usershop/add-products', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Charger tous les CSV depuis un dossier
  loadFromDirectory: async (directory = 'data') => {
    const response = await api.post('/usershop/load-from-directory', { directory });
    return response.data;
  },

  // Obtenir les statistiques
  getStats: async () => {
    const response = await api.get('/usershop/stats');
    return response.data;
  },

  // Vérifier l'état de l'API
  healthCheck: async () => {
    const response = await api.get('/usershop/health');
    return response.data;
  },

  // Comparer deux produits
  compareProducts: async (productId1, productId2) => {
    const response = await api.post('/usershop/compare', {
      product_id_1: productId1,
      product_id_2: productId2
    });
    return response.data;
  },
};

// B2C API
export const b2cAPI = {
  search: (data) => api.post('/b2c/search/semantic', data),
  recommend: (data) => api.post('/b2c/recommend', data),
  getMarketplaceProducts: () => api.get('/b2c/marketplace/products'),
  addMarketplaceProduct: (data) => api.post('/b2c/marketplace/products', data),
  getOrders: () => api.get('/b2c/orders'),
  createOrder: (data) => api.post('/b2c/orders', data),
}

// B2B API
export const b2bAPI = {
  login: (data) => api.post('/b2b/auth/login', data),
  signup: (data) => api.post('/b2b/auth/signup', data),
  search: (data, token) => api.post('/b2b/search', data, {
    headers: { Authorization: `Bearer ${token}` }
  }),
}

// Usershop API - using unified backend
export const usershopAPI = {
  recommend: (data) => api.post('/usershop/recommend', data),
  compare: (data) => api.post('/usershop/compare', data),
  search: (data) => api.post('/usershop/search', data),
  uploadCSV: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/usershop/add-products', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getStats: () => api.get('/usershop/stats'),
  loadFromDirectory: (directory = 'data') => api.post('/usershop/load-from-directory', { directory }),
  healthCheck: () => api.get('/usershop/stats'),
}

// ShopGPT API
export const shopgptAPI = {
  info: () => api.get('/shopping/info'),
}

export default api;
