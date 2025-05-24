/**
 * API service for connecting to the Scribley backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api';
const MEDIUM_TOKEN = import.meta.env.VITE_MEDIUM_API_TOKEN;

// Enhanced request cache with longer TTL for Medium-specific endpoints
const requestCache = new Map<string, {data: unknown, timestamp: number}>();

// Different cache TTLs based on endpoint type
const CACHE_TTL = {
  DEFAULT: 30000, // 30 seconds cache for regular endpoints
  MEDIUM_USER: 3600000, // 1 hour for user information
  MEDIUM_PUBLICATIONS: 3600000, // 1 hour for publications
  MEDIUM_CONTENT: 300000, // 5 minutes for content like articles
};

// Rate limiting - enhanced for Medium API
let lastRequestTime = 0;
const MIN_REQUEST_INTERVAL = 300; // ms between requests

// Medium API specific rate limiting
// Medium's API has unclear limits, but it's best to be conservative
const mediumRateLimits = {
  requestQueue: [] as number[],
  perMinuteLimit: 10,
  perHourLimit: 50,
  perDayLimit: 300,
  lastRequestTime: 0,
  minRequestInterval: 1000, // 1 second between Medium API requests
};

// Medium-specific endpoints that need special rate limiting
const MEDIUM_ENDPOINTS = [
  '/users/me',
  '/users/me/publications',
  '/publications',
  '/articles',
];

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

// Check if URL is a Medium API endpoint that needs special handling
const isMediumEndpoint = (url: string): boolean => {
  return MEDIUM_ENDPOINTS.some(endpoint => url.includes(endpoint));
};

// Get appropriate cache TTL based on endpoint
const getCacheTTL = (url: string): number => {
  if (url.includes('/users/me')) {
    return CACHE_TTL.MEDIUM_USER;
  } else if (url.includes('/publications')) {
    return CACHE_TTL.MEDIUM_PUBLICATIONS;
  } else if (url.includes('/articles')) {
    return CACHE_TTL.MEDIUM_CONTENT;
  }
  return CACHE_TTL.DEFAULT;
};

// Enhanced helper to throttle requests with specific Medium API handling
const throttleRequest = async (url: string): Promise<void> => {
  const now = Date.now();
  
  // Medium API specific rate limiting
  if (isMediumEndpoint(url)) {
    // Clean up old request history
    const dayAgo = now - 86400000; // 24 hours in ms
    const hourAgo = now - 3600000; // 1 hour in ms
    const minuteAgo = now - 60000; // 1 minute in ms
    
    // Clean up old requests
    mediumRateLimits.requestQueue = mediumRateLimits.requestQueue.filter(time => time > dayAgo);
    
    // Check rate limits
    const requestsToday = mediumRateLimits.requestQueue.length;
    const requestsThisHour = mediumRateLimits.requestQueue.filter(time => time > hourAgo).length;
    const requestsThisMinute = mediumRateLimits.requestQueue.filter(time => time > minuteAgo).length;
    
    // Enforce minimum interval between Medium API requests
    const timeToWaitForInterval = Math.max(0, mediumRateLimits.minRequestInterval - 
      (now - mediumRateLimits.lastRequestTime));
    
    // Calculate wait time based on which limit we're approaching
    let waitTime = timeToWaitForInterval;
    
    if (requestsThisMinute >= mediumRateLimits.perMinuteLimit) {
      // Wait until the oldest request from this minute expires
      const oldestInMinute = mediumRateLimits.requestQueue
        .filter(time => time > minuteAgo)
        .sort((a, b) => a - b)[0];
        
      waitTime = Math.max(waitTime, oldestInMinute + 60000 - now + 100);
      console.warn(`Medium API rate limit approaching: ${requestsThisMinute}/${mediumRateLimits.perMinuteLimit} requests this minute`);
    }
    
    if (requestsThisHour >= mediumRateLimits.perHourLimit * 0.9) {
      console.warn(`Medium API rate limit approaching: ${requestsThisHour}/${mediumRateLimits.perHourLimit} requests this hour`);
    }
    
    if (requestsToday >= mediumRateLimits.perDayLimit * 0.9) {
      console.warn(`Medium API rate limit approaching: ${requestsToday}/${mediumRateLimits.perDayLimit} requests today`);
    }
    
    if (waitTime > 0) {
      return new Promise(resolve => setTimeout(resolve, waitTime))
        .then(() => {
          mediumRateLimits.lastRequestTime = Date.now();
          mediumRateLimits.requestQueue.push(Date.now());
        });
    }
    
    mediumRateLimits.lastRequestTime = now;
    mediumRateLimits.requestQueue.push(now);
    return Promise.resolve();
  }
  
  // Standard rate limiting for non-Medium endpoints
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

// Enhanced fetch with improved caching for GET requests
const fetchWithCache = async (url: string, options: RequestInit, useCache = true): Promise<Response> => {
  const cacheKey = `${options.method || 'GET'}-${url}-${JSON.stringify(options.body || '')}`;
  
  // Only cache GET requests
  if (useCache && (options.method === 'GET' || !options.method)) {
    const cached = requestCache.get(cacheKey);
    const cacheTTL = getCacheTTL(url);
    
    if (cached && Date.now() - cached.timestamp < cacheTTL) {
      // Return mock response from cache
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(cached.data),
      } as Response);
    }
  }
  
  // Throttle request if needed
  await throttleRequest(url);
  
  // Make the actual request
  const response = await fetch(url, options);
  
  // Cache successful GET responses with appropriate TTL
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
    // eslint-disable-next-line no-empty
    } catch {
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
  
  uploadImage: async (file: File): Promise<{ url: string, md5: string }> => {
    // Create FormData
    const formData = new FormData();
    formData.append('image', file);
    
    // Remove Content-Type header as it will be set automatically with the boundary
    const headers = getHeaders();
    delete headers['Content-Type'];
    
    try {
      // Try to upload to the server first
      const response = await fetch(`${API_BASE_URL}/images/upload`, {
        method: 'POST',
        headers: {
          'Authorization': headers['Authorization'] // Only keep the authorization header
        },
        body: formData
      });
      
      return await handleResponse<{ url: string, md5: string }>(response);
    } catch (error) {
      console.warn('Server image upload failed, using local fallback:', error);
      
      // Local fallback - create a data URL for the image
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = () => {
          if (typeof reader.result === 'string') {
            // Generate a pseudo-MD5 hash for the image (not a real MD5, just for compatibility)
            const timestamp = Date.now().toString(36);
            const randomStr = Math.random().toString(36).substring(2, 8);
            const pseudoMd5 = `local_${timestamp}_${randomStr}`;
            
            resolve({
              url: reader.result,
              md5: pseudoMd5
            });
          } else {
            reject(new Error('Failed to generate data URL'));
          }
        };
        
        reader.onerror = () => reject(new Error('Failed to read file'));
        
        reader.readAsDataURL(file);
      });
    }
  }
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

// API Service for LLM (AI) features
export interface OllamaModel {
  name: string;
  modified_at: string;
  size: number;
  digest: string;
  details?: Record<string, unknown>;
}

export interface OllamaModelsResponse {
  models: OllamaModel[];
}

export const llmService = {
  getProviders: async (): Promise<{ providers: string[], default_provider: string, is_available: boolean }> => {
    const response = await fetchWithCache(`${API_BASE_URL}/llm/providers`, {
      headers: getHeaders(),
    }, true);
    return handleResponse(response);
  },

  getOllamaModels: async (): Promise<OllamaModelsResponse> => {
    const response = await fetchWithCache(`${API_BASE_URL}/llm/ollama/models`, {
      headers: getHeaders(),
    }, true);
    return handleResponse(response);
  },

  summarizeText: async (text: string, maxLength: number = 150, provider?: string, model?: string): Promise<{ summary: string }> => {
    const response = await fetchWithCache(`${API_BASE_URL}/llm/summarize`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        text,
        max_length: maxLength,
        provider,
        model
      }),
    }, false);
    return handleResponse(response);
  },

  generateTags: async (text: string, maxTags: number = 5, provider?: string, model?: string): Promise<{ tags: string[] }> => {
    const response = await fetchWithCache(`${API_BASE_URL}/llm/tags`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        text,
        max_tags: maxTags,
        provider,
        model
      }),
    }, false);
    return handleResponse(response);
  },

  improveTitle: async (title: string, text: string, provider?: string, model?: string): Promise<{ title: string }> => {
    const response = await fetchWithCache(`${API_BASE_URL}/llm/improve-title`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        title,
        text,
        provider,
        model
      }),
    }, false);
    return handleResponse(response);
  },

  checkIssues: async (text: string, provider?: string, model?: string): Promise<Record<string, unknown>> => {
    const response = await fetchWithCache(`${API_BASE_URL}/llm/check-issues`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        text,
        provider,
        model
      }),
    }, false);
    return handleResponse(response);
  },

  generateSocialPost: async (title: string, text: string, platform: string = 'twitter', provider?: string, model?: string): Promise<{ post: string }> => {
    const response = await fetchWithCache(`${API_BASE_URL}/llm/social-post`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        title,
        text,
        platform,
        provider,
        model
      }),
    }, false);
    return handleResponse(response);
  },

  draftArticle: async (
    topic: string, 
    outline?: string[], 
    length: string = 'medium', 
    style: string = 'informative',
    provider?: string,
    model?: string
  ): Promise<{ draft: string }> => {
    const response = await fetchWithCache(`${API_BASE_URL}/llm/draft-article`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        topic,
        outline,
        length,
        style,
        provider,
        model
      }),
    }, false);
    return handleResponse(response);
  }
}; 