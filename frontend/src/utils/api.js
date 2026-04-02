import axios from 'axios';

// Use the direct Lambda API URL in production, but keep using the Vite proxy in development
const API_BASE_URL = import.meta.env.PROD 
  ? 'https://4l16rbxyai.execute-api.ap-southeast-2.amazonaws.com/default'
  : '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

export default api;