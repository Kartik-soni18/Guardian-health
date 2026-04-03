import axios from 'axios';

// Use environment variable for API URL with fallbacks for development and production
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD 
  ? 'https://4l16rbxyai.execute-api.ap-southeast-2.amazonaws.com/default'
  : '/api');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

export default api;