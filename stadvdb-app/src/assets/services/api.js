// src/services/api.js
import axios from 'axios';

// Base URL for your Flask backend
const API_BASE_URL = 'http://localhost:5000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds
});

// Request interceptor for debugging
apiClient.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method.toUpperCase(), config.url, config.params);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.config.url, response.data);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ========== ORDERS API ==========
export const ordersAPI = {
  // Total Orders Over Time
  getTotalOrdersOverTime: async (params) => {
    const response = await apiClient.get('/orders/total-over-time', { params });
    return response.data;
  },

  // Orders by Location
  getOrdersByLocation: async (params) => {
    const response = await apiClient.get('/orders/by-location', { params });
    return response.data;
  },

  // Orders by Product Category
  getOrdersByProductCategory: async (params) => {
    const response = await apiClient.get('/orders/by-product-category', { params });
    return response.data;
  },
};

// ========== SALES API ==========
export const salesAPI = {
  // Add your sales endpoints here
};

// ========== CUSTOMER API ==========
export const customerAPI = {
  // Add your customer endpoints here
};

// ========== PRODUCT API ==========
export const productAPI = {
  // Add your product endpoints here
};

// ========== RIDER API ==========
export const riderAPI = {
  // Add your rider endpoints here
};

export default apiClient;