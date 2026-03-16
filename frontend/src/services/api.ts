import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Auth interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Portfolio API
export const portfolioApi = {
  list: (page = 1, pageSize = 20) =>
    api.get('/portfolios/', { params: { page, page_size: pageSize } }),
  get: (id: number) => api.get(`/portfolios/${id}`),
  create: (data: Record<string, unknown>) => api.post('/portfolios/', data),
  update: (id: number, data: Record<string, unknown>) => api.patch(`/portfolios/${id}`, data),
  delete: (id: number) => api.delete(`/portfolios/${id}`),
}

// Debtor API
export const debtorApi = {
  list: (params: Record<string, unknown>) => api.get('/debtors/', { params }),
  get: (id: number) => api.get(`/debtors/${id}`),
  create: (data: Record<string, unknown>) => api.post('/debtors/', data),
  update: (id: number, data: Record<string, unknown>) => api.patch(`/debtors/${id}`, data),
}

// Court Cases API
export const courtCaseApi = {
  list: (params: Record<string, unknown>) => api.get('/court-cases/', { params }),
  get: (id: number) => api.get(`/court-cases/${id}`),
}

// Dashboard API
export const dashboardApi = {
  stats: () => api.get('/dashboard/stats'),
  casesNeedingReview: () => api.get('/dashboard/cases-needing-review'),
}

// Import API
export const importApi = {
  preview: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/imports/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  start: (filePath: string, config: Record<string, unknown>) =>
    api.post('/imports/start', config, { params: { file_path: filePath } }),
  status: (taskId: string) => api.get(`/imports/status/${taskId}`),
}

export default api
