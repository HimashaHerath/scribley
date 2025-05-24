import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { articleService, publicationService, type Article, type ArticleCreate } from './api';

interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

// Local cache for fetch results to prevent unnecessary rerenders
const hookCache = new Map<string, {data: unknown, timestamp: number}>();
const CACHE_TTL = 120000; // 2 minutes

// Basic fetch hook with loading, error states
export function useFetch<T>(
  fetchFn: () => Promise<T>,
  dependencies: unknown[] = [],
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
          setState({ data: cached.data as T, loading: false, error: null });
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
      console.error('Error details:', {
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
        context: { depsKey, cacheKey }
      });
      
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

// Custom hook for managing article form state and logic
export function useArticleForm(article?: Article, isEditing = false) {
  const navigate = useNavigate();
  
  type ArticleStatus = 'draft' | 'public' | 'unlisted';
  
  // Initialize draft management
  const {
    draft: savedDraft,
    saveDraft,
    clearDraft,
    isRecovered,
    lastSavedFormatted
  } = useArticleDraft(
    article?.id,
    article ? {
      title: article.title,
      subtitle: article.subtitle,
      content: article.content,
      tags: article.tags,
      status: article.status,
      publication_id: article.publication_id
    } : undefined
  );
  
  // Form state, using saved draft if available
  const [title, setTitle] = useState(savedDraft?.title || article?.title || '');
  const [subtitle, setSubtitle] = useState(savedDraft?.subtitle || article?.subtitle || '');
  const [content, setContent] = useState(savedDraft?.content || article?.content || '');
  const [tags, setTags] = useState(
    savedDraft?.tags 
      ? (Array.isArray(savedDraft.tags) ? savedDraft.tags.join(', ') : savedDraft.tags)
      : article?.tags?.join(', ') || ''
  );
  const [status, setStatus] = useState<ArticleStatus>(
    (savedDraft?.status as ArticleStatus) || 
    (article?.status as ArticleStatus) || 
    'draft'
  );
  const [publicationId, setPublicationId] = useState(
    savedDraft?.publication_id || article?.publication_id || 'none'
  );
  
  const [showAPIWarning, setShowAPIWarning] = useState(true);
  const [showDraftRecoveryNotice, setShowDraftRecoveryNotice] = useState(isRecovered);
  
  // AI Assistant panel state
  const [isAssistantOpen, setIsAssistantOpen] = useState<boolean>(false);
  
  // Function to manually trigger draft saving
  const triggerSaveDraft = useCallback(() => {
    // Don't save if we're just showing the recovered draft
    if (isRecovered && showDraftRecoveryNotice) return;
    
    // Prepare draft data
    const draftData: Partial<ArticleCreate> = {
      title,
      subtitle,
      content,
      tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0),
      status,
      publication_id: publicationId === 'none' ? undefined : publicationId
    };
    
    saveDraft(draftData);
  }, [title, subtitle, content, tags, status, publicationId, saveDraft, isRecovered, showDraftRecoveryNotice]);
  
  // Auto-save draft when form data changes
  useEffect(() => {
    const autoSaveTimer = setTimeout(() => {
      triggerSaveDraft(); // Use the new trigger function
    }, 2000); // Auto-save after 2 seconds of inactivity
    
    return () => clearTimeout(autoSaveTimer);
  }, [triggerSaveDraft]); // Depend on triggerSaveDraft
  
  // Discard recovered draft
  const discardRecoveredDraft = useCallback(() => {
    if (article) {
      setTitle(article.title || '');
      setSubtitle(article.subtitle || '');
      setContent(article.content || '');
      setTags(article.tags?.join(', ') || '');
      setStatus((article.status as ArticleStatus) || 'draft');
      setPublicationId(article.publication_id || 'none');
    } else {
      setTitle('');
      setSubtitle('');
      setContent('');
      setTags('');
      setStatus('draft');
      setPublicationId('none');
    }
    
    clearDraft();
    setShowDraftRecoveryNotice(false);
  }, [article, clearDraft]);
  
  // Fetch publications for select box
  const { data: publications } = useFetch(
    useCallback(async () => {
      return publicationService.getAll();
    }, []), 
    [],
    []
  );
  
  // Create article submission
  const { submit: createArticle, isSubmitting: isCreating } = useSubmit<Article, ArticleCreate>(
    useCallback((input?: ArticleCreate) => {
      if (!input) throw new Error("Article data is required");
      return articleService.create(input);
    }, []),
    {
      onSuccess: (newArticle) => {
        clearDraft(); // Clear the draft after successful creation
        navigate(`/articles/${newArticle.id}`);
      },
      successMessage: 'Article created successfully'
    }
  );
  
  // Update article submission
  const { submit: updateArticle, isSubmitting: isUpdating } = useSubmit<Article, { id: string; article: ArticleCreate }>(
    useCallback((input?: { id: string; article: ArticleCreate }) => {
      if (!input) throw new Error("Article ID and data are required");
      return articleService.update(input.id, input.article);
    }, []),
    {
      onSuccess: (updatedArticle) => {
        clearDraft(); // Clear the draft after successful update
        navigate(`/articles/${updatedArticle.id}`);
      },
      successMessage: 'Article updated successfully'
    }
  );
  
  const isSubmitting = isCreating || isUpdating;
  
  // Toggle AI Assistant panel
  const toggleAssistantPanel = useCallback(() => {
    setIsAssistantOpen(prev => !prev);
  }, []);
  
  // Handle content insertion from AI Assistant
  const handleInsertContent = useCallback((newContent: string, newTitle?: string) => {
    // Update content
    setContent((prevContent: string) => prevContent + newContent);
    
    // Update title if provided and empty
    if (newTitle && !title) {
      setTitle(newTitle);
    }
  }, [title]);
  
  // Handle form submission
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    
    // Convert tags string to array
    const tagsArray = tags
      .split(',')
      .map((tag: string) => tag.trim())
      .filter((tag: string) => tag.length > 0);
    
    const articleData: ArticleCreate = {
      title,
      subtitle: subtitle || undefined,
      content,
      tags: tagsArray,
      status,
      publication_id: publicationId === 'none' ? undefined : publicationId
    };
    
    if (isEditing && article) {
      updateArticle({ id: article.id, article: articleData });
    } else {
      createArticle(articleData);
    }
  }, [
    title, subtitle, content, tags, status, publicationId, 
    isEditing, article, updateArticle, createArticle
  ]);
  
  return {
    // Form state
    title,
    setTitle,
    subtitle,
    setSubtitle,
    content,
    setContent,
    tags,
    setTags,
    status,
    setStatus,
    publicationId,
    setPublicationId,
    showAPIWarning,
    setShowAPIWarning,
    
    // Draft recovery
    isRecovered,
    showDraftRecoveryNotice,
    setShowDraftRecoveryNotice,
    discardRecoveredDraft,
    lastSavedFormatted,
    triggerSaveDraft, // Expose triggerSaveDraft instead of raw saveDraft
    
    // AI Assistant state
    isAssistantOpen,
    toggleAssistantPanel,
    
    // Data
    publications,
    isSubmitting,
    
    // Handlers
    handleSubmit,
    handleInsertContent,
    
    // Navigation
    goBack: () => navigate(-1)
  };
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

// Local storage hook for persisting data
export function useLocalStorage<T>(key: string, initialValue: T) {
  // State to store our value
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }
    
    try {
      // Get from local storage by key
      const item = window.localStorage.getItem(key);
      // Parse stored json or if none return initialValue
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      // If error also return initialValue
      console.error('Error reading from localStorage', error);
      return initialValue;
    }
  });
  
  // Return a wrapped version of useState's setter function that persists the new value to localStorage
  const setValue = useCallback((value: T | ((val: T) => T)) => {
    try {
      // Allow value to be a function so we have same API as useState
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      
      // Save state
      setStoredValue(valueToStore);
      
      // Save to local storage
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      // A more advanced implementation would handle the error case
      console.error('Error writing to localStorage', error);
    }
  }, [key, storedValue]);
  
  // Remove item from local storage
  const removeValue = useCallback(() => {
    try {
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key);
        setStoredValue(initialValue);
      }
    } catch (error) {
      console.error('Error removing from localStorage', error);
    }
  }, [key, initialValue]);
  
  return [storedValue, setValue, removeValue] as const;
}

// Hook for managing article drafts with auto-save
export function useArticleDraft(
  articleId?: string,
  initialData?: Partial<ArticleCreate>
) {
  // Create a unique key for this draft
  const draftKey = articleId 
    ? `article_draft_${articleId}` 
    : 'article_new_draft';
  
  // Use local storage to persist the draft
  const [draft, setDraft, removeDraft] = useLocalStorage<Partial<ArticleCreate> | null>(
    draftKey,
    initialData || null
  );
  
  // Check if draft has meaningful content to recover
  const hasMeaningfulContent = Boolean(
    draft && 
    (
      (draft.title && draft.title.trim().length > 0) || 
      (draft.content && draft.content.trim().length > 0)
    )
  );
  
  // Only consider it recovered if there's actual content and we're not editing an existing article
  const [isRecovered, setIsRecovered] = useState(hasMeaningfulContent && !articleId);
  
  // Last auto-save timestamp
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  
  // Auto-save function
  const saveDraft = useCallback((data: Partial<ArticleCreate>) => {
    // Don't save completely empty drafts
    if (!data.title?.trim() && !data.content?.trim()) {
      return;
    }
    
    setDraft(data);
    setLastSaved(new Date());
  }, [setDraft]);
  
  // Clear the draft
  const clearDraft = useCallback(() => {
    removeDraft();
    setIsRecovered(false);
    setLastSaved(null);
  }, [removeDraft]);
  
  // Format the last saved time as a string
  const lastSavedFormatted = useMemo(() => {
    if (!lastSaved) return '';
    
    const now = new Date();
    const diffMs = now.getTime() - lastSaved.getTime();
    const diffSec = Math.round(diffMs / 1000);
    const diffMin = Math.round(diffSec / 60);
    
    if (diffSec < 60) {
      return 'just now';
    } else if (diffMin < 60) {
      return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
    } else {
      return lastSaved.toLocaleTimeString();
    }
  }, [lastSaved]);
  
  return {
    draft,
    saveDraft,
    clearDraft,
    isRecovered,
    lastSaved,
    lastSavedFormatted
  };
}

// Hook for managing user preferences
export function useUserPreferences<T extends Record<string, unknown>>(
  defaultPreferences: T
) {
  const [preferences, setPreferences, resetPreferences] = useLocalStorage<T>(
    'user_preferences',
    defaultPreferences
  );
  
  // Update a single preference
  const updatePreference = useCallback(<K extends keyof T>(key: K, value: T[K]) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  }, [setPreferences]);
  
  return {
    preferences,
    setPreferences,
    updatePreference,
    resetPreferences
  };
} 