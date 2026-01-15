import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { MovieDetail } from '@/types/movie';

interface UseMovieState {
  data: MovieDetail | null;
  loading: boolean;
  error: string | null;
  retryCount: number;
}

interface UseMovieOptions {
  id: number;
  autoFetch?: boolean;
  maxRetries?: number;
}

export function useMovie(options: UseMovieOptions) {
  const { id, autoFetch = true, maxRetries = 3 } = options;
  
  const [state, setState] = useState<UseMovieState>({
    data: null,
    loading: false,
    error: null,
    retryCount: 0,
  });

  const fetchMovie = useCallback(async (movieId: number = id) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const data = await apiClient.getMovieById(movieId);
      setState({ data, loading: false, error: null, retryCount: 0 });
    } catch (error) {
      let errorMessage = 'Failed to fetch movie';
      
      if (error instanceof Error) {
        if (error.message.includes('fetch') || error.message.includes('NetworkError')) {
          errorMessage = 'Network connection failed. Please check your internet connection.';
        } else if (error.message.includes('500')) {
          errorMessage = 'Server error occurred. Please try again later.';
        } else if (error.message.includes('404')) {
          errorMessage = 'Movie not found.';
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
  }, [id]);

  const refetch = useCallback(() => {
    fetchMovie(id);
  }, [fetchMovie, id]);

  const canRetry = state.retryCount < maxRetries;

  useEffect(() => {
    if (autoFetch && id) {
      fetchMovie(id);
    }
  }, [id, autoFetch, fetchMovie]);

  return {
    ...state,
    fetchMovie,
    refetch,
    canRetry,
  };
}