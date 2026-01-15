import { useState, useCallback, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export enum SortCriteria {
  YEAR = 'year',
  RATING = 'rating',
  REVIEW_COUNT = 'review_count',
  TITLE = 'title'
}

export enum SortOrder {
  ASC = 'asc',
  DESC = 'desc'
}

interface Movie {
  id: number;
  title: string;
  year: number;
  genre: string;
  rating: number;
  poster_url?: string;
  average_user_rating?: number;
  review_count: number;
}

interface SearchState {
  query: string;
  results: Movie[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  totalPages: number;
  sortBy: SortCriteria | null;
  sortOrder: SortOrder;
}

interface SearchResponse {
  movies: Movie[];
  total: number;
  page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Debounce utility
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export const useMovieSearch = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [searchState, setSearchState] = useState<SearchState>({
    query: searchParams.get('q') || '',
    results: [],
    loading: false,
    error: null,
    totalCount: 0,
    currentPage: parseInt(searchParams.get('page') || '1'),
    totalPages: 1,
    sortBy: (searchParams.get('sort_by') as SortCriteria) || null,
    sortOrder: (searchParams.get('sort_order') as SortOrder) || SortOrder.DESC
  });

  // Update URL parameters
  const updateURL = useCallback((params: {
    q?: string;
    sort_by?: SortCriteria | null;
    sort_order?: SortOrder;
    page?: number;
  }) => {
    const current = new URLSearchParams(searchParams);
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        current.set(key, value.toString());
      } else {
        current.delete(key);
      }
    });

    // Reset page when search or sort changes
    if (params.q !== undefined || params.sort_by !== undefined || params.sort_order !== undefined) {
      current.set('page', '1');
    }

    router.push(`?${current.toString()}`);
  }, [router, searchParams]);

  // Search movies function
  const searchMovies = useCallback(async (
    query: string,
    sortBy?: SortCriteria | null,
    sortOrder?: SortOrder,
    page?: number
  ) => {
    setSearchState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const params = new URLSearchParams();
      if (query.trim()) {
        params.append('q', query.trim());
      }
      if (sortBy) {
        params.append('sort_by', sortBy);
      }
      if (sortOrder) {
        params.append('sort_order', sortOrder);
      }
      if (page) {
        params.append('page', page.toString());
      }
      params.append('per_page', '20');

      const endpoint = query.trim() ? '/api/movies/search' : '/api/movies';
      const response = await fetch(`${API_BASE_URL}${endpoint}?${params}`);
      
      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }
      
      const data: SearchResponse = await response.json();
      
      setSearchState(prev => ({
        ...prev,
        results: data.movies,
        totalCount: data.total,
        currentPage: data.page,
        totalPages: data.total_pages,
        loading: false
      }));
    } catch (error) {
      setSearchState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Search failed. Please try again.',
        loading: false
      }));
    }
  }, []);

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce((query: string, sortBy?: SortCriteria | null, sortOrder?: SortOrder) => {
      searchMovies(query, sortBy, sortOrder, 1);
    }, 300),
    [searchMovies]
  );

  // Set search query
  const setQuery = useCallback((query: string) => {
    setSearchState(prev => ({ ...prev, query }));
    updateURL({ q: query });
    debouncedSearch(query, searchState.sortBy, searchState.sortOrder);
  }, [debouncedSearch, searchState.sortBy, searchState.sortOrder, updateURL]);

  // Set sort criteria
  const setSortCriteria = useCallback((sortBy: SortCriteria | null, sortOrder: SortOrder) => {
    setSearchState(prev => ({ ...prev, sortBy, sortOrder }));
    updateURL({ sort_by: sortBy, sort_order: sortOrder });
    searchMovies(searchState.query, sortBy, sortOrder, 1);
  }, [searchState.query, searchMovies, updateURL]);

  // Set page
  const setPage = useCallback((page: number) => {
    setSearchState(prev => ({ ...prev, currentPage: page }));
    updateURL({ page });
    searchMovies(searchState.query, searchState.sortBy, searchState.sortOrder, page);
  }, [searchState.query, searchState.sortBy, searchState.sortOrder, searchMovies, updateURL]);

  // Clear search
  const clearSearch = useCallback(() => {
    setSearchState(prev => ({ 
      ...prev, 
      query: '', 
      results: [],
      totalCount: 0,
      currentPage: 1,
      totalPages: 1
    }));
    updateURL({ q: '', page: 1 });
    searchMovies('', searchState.sortBy, searchState.sortOrder, 1);
  }, [searchState.sortBy, searchState.sortOrder, searchMovies, updateURL]);

  // Load initial data on mount
  useEffect(() => {
    const initialQuery = searchParams.get('q') || '';
    const initialSortBy = (searchParams.get('sort_by') as SortCriteria) || null;
    const initialSortOrder = (searchParams.get('sort_order') as SortOrder) || SortOrder.DESC;
    const initialPage = parseInt(searchParams.get('page') || '1');

    searchMovies(initialQuery, initialSortBy, initialSortOrder, initialPage);
  }, []); // Only run on mount

  return {
    searchState,
    setQuery,
    setSortCriteria,
    setPage,
    clearSearch,
    searchMovies
  };
};