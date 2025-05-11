/**
 * API service for connecting to the Scribley backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api';
const MEDIUM_TOKEN = import.meta.env.VITE_MEDIUM_API_TOKEN;

// Simple request cache to prevent duplicate requests
const requestCache = new Map<string, {data: any, timestamp: number}>();
const CACHE_TTL = 30000; // 30 seconds cache

// Rate limiting - to prevent too many requests
let lastRequestTime = 0;
const MIN_REQUEST_INTERVAL = 300; // ms between requests

// Types
export interface Article {
  id: string;
  title: string;
  subtitle?: string;
  content: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  published_at?: string;
  status: 'draft' | 'public' | 'unlisted';
  medium_id?: string;
  medium_url?: string;
  publication_id?: string;
}

export interface ArticleCreate {
  title: string;
  subtitle?: string;
  content: string;
  tags: string[];
  status?: 'draft' | 'public' | 'unlisted';
  publication_id?: string;
}

export interface Publication {
  id: string;
  name: string;
  description?: string;
  url: string;
  image_url?: string;
}

export interface User {
  id: string;
  username: string;
  name: string;
  url: string;
  image_url?: string;
}

// API Error handling
export class ApiError extends Error {
  status: number;
  
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// Default headers with authentication
const getHeaders = () => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (MEDIUM_TOKEN) {
    headers['Authorization'] = `Bearer ${MEDIUM_TOKEN}`;
  }
  
  return headers;
};

// Helper to throttle requests
const throttleRequest = (): Promise<void> => {
  const now = Date.now();
  const timeToWait = Math.max(0, MIN_REQUEST_INTERVAL - (now - lastRequestTime));
  
  if (timeToWait > 0) {
    return new Promise(resolve => setTimeout(resolve, timeToWait))
      .then(() => {
        lastRequestTime = Date.now();
      });
  }
  
  lastRequestTime = now;
  return Promise.resolve();
};

// Enhanced fetch with caching for GET requests
const fetchWithCache = async (url: string, options: RequestInit, useCache = true): Promise<Response> => {
  const cacheKey = `${options.method || 'GET'}-${url}-${JSON.stringify(options.body || '')}`;
  
  // Only cache GET requests
  if (useCache && options.method === 'GET' || !options.method) {
    const cached = requestCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      // Return mock response from cache
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(cached.data),
      } as Response);
    }
  }
  
  // Throttle request if needed
  await throttleRequest();
  
  // Make the actual request
  const response = await fetch(url, options);
  
  // Cache successful GET responses
  if (useCache && response.ok && (options.method === 'GET' || !options.method)) {
    const clonedResponse = response.clone();
    clonedResponse.json().then(data => {
      requestCache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });
    }).catch(() => {
      // If we can't parse the response as JSON, don't cache it
    });
  }
  
  return response;
};

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = response.statusText;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch (e) {
      // If we can't parse the error as JSON, just use the status text
    }
    throw new ApiError(errorMessage, response.status);
  }
  return await response.json() as T;
}

// API Services
export const articleService = {
  getAll: async (params?: { status?: string, tag?: string, limit?: number, offset?: number }): Promise<Article[]> => {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.tag) queryParams.append('tag', params.tag);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    
    const url = `${API_BASE_URL}/articles?${queryParams.toString()}`;
    const response = await fetchWithCache(url, {
      headers: getHeaders(),
    }, true);
    return handleResponse<Article[]>(response);
  },
  
  getById: async (id: string): Promise<Article> => {
    const response = await fetchWithCache(`${API_BASE_URL}/articles/${id}`, {
      headers: getHeaders(),
    }, true);
    return handleResponse<Article>(response);
  },
  
  create: async (article: ArticleCreate): Promise<Article> => {
    const response = await fetchWithCache(`${API_BASE_URL}/articles`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(article),
    }, false); // Don't cache POST requests
    return handleResponse<Article>(response);
  },
  
  update: async (id: string, article: ArticleCreate): Promise<Article> => {
    const response = await fetchWithCache(`${API_BASE_URL}/articles/${id}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(article),
    }, false); // Don't cache PUT requests
    return handleResponse<Article>(response);
  },
  
  delete: async (id: string): Promise<void> => {
    const response = await fetchWithCache(`${API_BASE_URL}/articles/${id}`, {
      method: 'DELETE',
      headers: getHeaders(),
    }, false); // Don't cache DELETE requests
    if (!response.ok) {
      throw new ApiError(response.statusText, response.status);
    }
  },
  
  publish: async (id: string, options?: { status?: string, publication_id?: string }): Promise<Article> => {
    const queryParams = new URLSearchParams();
    if (options?.status) queryParams.append('status', options.status);
    if (options?.publication_id) queryParams.append('publication_id', options.publication_id);
    
    const url = `${API_BASE_URL}/articles/${id}/publish${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await fetchWithCache(url, {
      method: 'POST',
      headers: getHeaders(),
    }, false); // Don't cache POST requests
    return handleResponse<Article>(response);
  },
};

export const publicationService = {
  getAll: async (): Promise<Publication[]> => {
    const response = await fetchWithCache(`${API_BASE_URL}/publications`, {
      headers: getHeaders(),
    }, true); // Cache GET requests
    return handleResponse<Publication[]>(response);
  },
  
  getById: async (id: string): Promise<Publication> => {
    const response = await fetchWithCache(`${API_BASE_URL}/publications/${id}`, {
      headers: getHeaders(),
    }, true); // Cache GET requests
    return handleResponse<Publication>(response);
  },
  
  getContributors: async (id: string): Promise<{userId: string, role: string}[]> => {
    const response = await fetchWithCache(`${API_BASE_URL}/publications/${id}/contributors`, {
      headers: getHeaders(),
    }, true); // Cache GET requests
    return handleResponse<{userId: string, role: string}[]>(response);
  }
};

export const userService = {
  getCurrentUser: async (): Promise<User> => {
    const response = await fetchWithCache(`${API_BASE_URL}/users/me`, {
      headers: getHeaders(),
    }, true); // Cache GET requests
    return handleResponse<User>(response);
  },
  
  getUserPublications: async (): Promise<Publication[]> => {
    const response = await fetchWithCache(`${API_BASE_URL}/users/me/publications`, {
      headers: getHeaders(),
    }, true); // Cache GET requests
    return handleResponse<Publication[]>(response);
  }
}; 