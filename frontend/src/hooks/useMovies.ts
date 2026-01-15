import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { PaginatedMoviesResponse } from '@/types/movie';

interface UseMoviesState {
  data: PaginatedMoviesResponse | null;
  loading: boolean;
  error: string | null;
  retryCount: number;
}

interface UseMoviesOptions {
  page?: number;
  perPage?: number;
  autoFetch?: boolean;
  maxRetries?: number;
}

export function useMovies(options: UseMoviesOptions = {}) {
  const { page = 1, perPage = 20, autoFetch = true, maxRetries = 3 } = options;
  
  const [state, setState] = useState<UseMoviesState>({
    data: null,
    loading: false,
    error: null,
    retryCount: 0,
  });

  const fetchMovies = useCallback(async (fetchPage: number = page, fetchPerPage: number = perPage) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const data = await apiClient.getMovies(fetchPage, fetchPerPage);
      setState({ data, loading: false, error: null, retryCount: 0 });
    } catch (error) {
      let errorMessage = 'Failed to fetch movies';
      
      if (error instanceof Error) {
        if (error.message.includes('fetch') || error.message.includes('NetworkError')) {
          errorMessage = 'Network connection failed. Please check your internet connection.';
        } else if (error.message.includes('500')) {
          errorMessage = 'Server error occurred. Please try again later.';
        } else if (error.message.includes('404')) {
          errorMessage = 'Movies not found.';
        } else {
          errorMessage = error.message;
        }
      }
      
      setState(prev => ({ 
        data: null, 
        loading: false, 
        error: errorMessage,
        retryCount: prev.retryCount + 1
      }));
    }
  }, [page, perPage]);

  const refetch = useCallback(() => {
    fetchMovies(page, perPage);
  }, [fetchMovies, page, perPage]);

  const canRetry = state.retryCount < maxRetries;

  useEffect(() => {
    if (autoFetch) {
      fetchMovies(page, perPage);
    }
  }, [page, perPage, autoFetch, fetchMovies]);

  return {
    ...state,
    fetchMovies,
    refetch,
    canRetry,
  };
}