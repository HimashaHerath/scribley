import { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { ApiError } from './api';

interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

// Local cache for fetch results to prevent unnecessary rerenders
const hookCache = new Map<string, {data: any, timestamp: number}>();
const CACHE_TTL = 120000; // 2 minutes

// Basic fetch hook with loading, error states
export function useFetch<T>(
  fetchFn: () => Promise<T>,
  dependencies: any[] = [],
  initialData: T | null = null,
  cacheKey?: string
): FetchState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<FetchState<T>>({
    data: initialData,
    loading: true,
    error: null,
  });
  
  // Use a ref to store the latest fetch function without causing rerenders
  const fetchFnRef = useRef(fetchFn);
  fetchFnRef.current = fetchFn;
  
  // Create a stable stringified version of dependencies for cache key
  const depsKey = JSON.stringify(dependencies);
  
  // Used to avoid race conditions
  const fetchIdRef = useRef(0);

  const fetchData = useCallback(async (ignoreCache = false) => {
    setState(prev => ({ ...prev, loading: prev.data === null }));
    
    // Create a unique ID for this fetch request
    const fetchId = ++fetchIdRef.current;
    
    // Check cache if we have a cache key and are not ignoring cache
    if (cacheKey && !ignoreCache) {
      const cached = hookCache.get(cacheKey + depsKey);
      if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        if (fetchId === fetchIdRef.current) {
          setState({ data: cached.data, loading: false, error: null });
          return;
        }
      }
    }
    
    try {
      const data = await fetchFnRef.current();
      
      // Only update state if this is still the latest fetch
      if (fetchId === fetchIdRef.current) {
        setState({ data, loading: false, error: null });
        
        // Cache the result if we have a cache key
        if (cacheKey) {
          hookCache.set(cacheKey + depsKey, {
            data,
            timestamp: Date.now()
          });
        }
      }
    } catch (error) {
      console.error('Fetch error:', error);
      const apiError = error instanceof Error 
        ? error 
        : new Error('An unexpected error occurred');
      
      // Only update state if this is still the latest fetch
      if (fetchId === fetchIdRef.current) {
        setState(prevState => ({ 
          data: prevState.data, // Keep any existing data on error
          loading: false, 
          error: apiError 
        }));
        
        // Show error toast only for new fetch operations (not on mount with existing data)
        if (!state.data || ignoreCache) {
          toast.error(apiError instanceof Error ? apiError.message : 'Failed to fetch data');
        }
      }
    }
  }, [depsKey, cacheKey]);

  // Use effect to load data when dependencies change
  useEffect(() => {
    let isMounted = true;
    
    // Reset fetchId on dependency changes
    if (isMounted) {
      fetchData(false);
    }
    
    return () => {
      isMounted = false;
    };
  }, [fetchData, depsKey]);

  // Return a stable refetch function that ignores cache
  const refetch = useCallback(() => fetchData(true), [fetchData]);

  return { ...state, refetch };
}

// Hook for articles with filtering
export function useArticles(options?: { 
  status?: string; 
  tag?: string; 
  limit?: number; 
  offset?: number 
}) {
  // Stringify options for stable dependency comparison
  const optionsKey = JSON.stringify(options || {});
  
  // Use a ref to store options to avoid recreating the fetch function
  const optionsRef = useRef(options || {});
  optionsRef.current = options || {};
  
  // Create a stable fetch function that reads from the ref
  const fetchArticles = useCallback(async () => {
    const { articleService } = await import('./api');
    return articleService.getAll(optionsRef.current);
  }, []);
  
  return {
    ...useFetch(fetchArticles, [optionsKey], [], 'articles'),
    filters: optionsRef.current,
  };
}

// Hook for articles by ID
export function useArticle(id: string | undefined) {
  // Use a ref to avoid recreating the fetch function
  const idRef = useRef(id);
  idRef.current = id;
  
  const fetchArticle = useCallback(async () => {
    if (!idRef.current) throw new Error('Article ID is required');
    const { articleService } = await import('./api');
    return articleService.getById(idRef.current);
  }, []);

  return useFetch(fetchArticle, [id], null, `article-${id}`);
}

// Hook for publications
export function usePublications() {
  const fetchPublications = useCallback(async () => {
    const { publicationService } = await import('./api');
    return publicationService.getAll();
  }, []);

  return useFetch(fetchPublications, [], [], 'publications');
}

// Hook for current user
export function useCurrentUser() {
  const fetchUser = useCallback(async () => {
    const { userService } = await import('./api');
    return userService.getCurrentUser();
  }, []);

  return useFetch(fetchUser, [], null, 'current-user');
}

// Mutation hook for creating/updating/deleting resources
export function useMutation<T, P>(
  mutationFn: (params: P) => Promise<T>
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<T | null>(null);

  const execute = async (params: P) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await mutationFn(params);
      setData(result);
      setLoading(false);
      return result;
    } catch (error) {
      console.error('Mutation error:', error);
      const apiError = error instanceof Error 
        ? error 
        : new Error('An unexpected error occurred');
      
      setError(apiError);
      setLoading(false);
      
      // Show error toast
      toast.error(apiError instanceof Error ? apiError.message : 'Operation failed');
      throw error;
    }
  };

  return {
    execute,
    loading,
    error,
    data,
  };
}

export function useSubmit<TData, TInput = void>(
  submitFn: (input?: TInput) => Promise<TData>,
  options: {
    onSuccess?: (data: TData) => void;
    onError?: (error: Error) => void;
    successMessage?: string;
  } = {}
) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<TData | null>(null);

  const submit = async (input?: TInput) => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      const result = await submitFn(input);
      setData(result);
      setIsSubmitting(false);
      
      if (options.successMessage) {
        toast.success(options.successMessage);
      }
      
      if (options.onSuccess) {
        options.onSuccess(result);
      }
      
      return result;
    } catch (err) {
      const error = err as Error;
      setError(error);
      setIsSubmitting(false);
      
      toast.error(error.message || 'An error occurred');
      
      if (options.onError) {
        options.onError(error);
      }
      
      throw error;
    }
  };

  return {
    submit,
    isSubmitting,
    error,
    data,
  };
} 