import axios from 'axios';

const API_URL = '/api';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
);

export const auth = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    api.post('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
};

export const contacts = {
  list: (search?: string) => api.get('/contacts', { params: { search } }),
  get: (id: number) => api.get(`/contacts/${id}`),
  create: (data: any) => api.post('/contacts', data),
  update: (id: number, data: any) => api.put(`/contacts/${id}`, data),
  delete: (id: number) => api.delete(`/contacts/${id}`),
};

export const opportunities = {
  list: (params?: any) => api.get('/opportunities', { params }),
  get: (id: number) => api.get(`/opportunities/${id}`),
  create: (data: any) => api.post('/opportunities', data),
  update: (id: number, data: any) => api.put(`/opportunities/${id}`, data),
  updateStage: (id: number, stage: string) =>
    api.put(`/opportunities/${id}/stage`, null, { params: { stage } }),
  delete: (id: number) => api.delete(`/opportunities/${id}`),
};

export const tasks = {
  list: (params?: any) => api.get('/tasks', { params }),
  get: (id: number) => api.get(`/tasks/${id}`),
  create: (data: any) => api.post('/tasks', data),
  update: (id: number, data: any) => api.put(`/tasks/${id}`, data),
  updateStatus: (id: number, status: string) =>
    api.put(`/tasks/${id}/status`, null, { params: { status } }),
  delete: (id: number) => api.delete(`/tasks/${id}`),
};

export const activities = {
  list: (params?: any) => api.get('/activities', { params }),
  get: (id: number) => api.get(`/activities/${id}`),
  create: (data: any) => api.post('/activities', data),
  update: (id: number, data: any) => api.put(`/activities/${id}`, data),
  delete: (id: number) => api.delete(`/activities/${id}`),
};

export const reports = {
  dashboard: () => api.get('/reports/dashboard'),
  pipeline: () => api.get('/reports/pipeline'),
  contacts: () => api.get('/reports/contacts'),
};

export const users = {
  list: () => api.get('/users'),
  get: (id: number) => api.get(`/users/${id}`),
};