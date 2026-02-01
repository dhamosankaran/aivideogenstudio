import axios from 'axios';
import { API_BASE_URL } from '../config';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const videoApi = {
  list: (offset = 0, limit = 20) =>
    api.get('/video', { params: { offset, limit } }),

  get: (id) =>
    api.get(`/video/${id}`),

  download: (id) =>
    api.get(`/video/${id}/download`, { responseType: 'blob' }),

  stats: () =>
    api.get('/video/stats'),
};

export default api;
