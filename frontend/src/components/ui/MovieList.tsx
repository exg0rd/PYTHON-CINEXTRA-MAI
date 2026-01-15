'use client';

import { useState } from 'react';
import { useMovies } from '@/hooks/useMovies';
import MovieCard from './MovieCard';
import MovieCardSkeleton from './MovieCardSkeleton';
import ErrorMessage from './ErrorMessage';
import LoadingSpinner from './LoadingSpinner';

interface MovieListProps {
  className?: string;
}

export default function MovieList({ className = '' }: MovieListProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const { data, loading, error, fetchMovies, canRetry } = useMovies({ 
    page: currentPage, 
    perPage: 20 
  });

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    // Scroll to top when page changes
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleRetry = () => {
    fetchMovies(currentPage, 20);
  };

  if (error) {
    return (
      <div className={className}>
        <ErrorMessage 
          message={error} 
          onRetry={canRetry ? handleRetry : undefined}
          className="max-w-md mx-auto"
        />
        {!canRetry && (
          <div className="text-center mt-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Maximum retry attempts reached. Please refresh the page.
            </p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Movie Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6 mb-8">
        {loading && !data ? (
          // Show skeletons on initial load
          Array.from({ length: 20 }).map((_, index) => (
            <MovieCardSkeleton key={index} />
          ))
        ) : (
          data?.movies.map((movie, index) => (
            <div 
              key={movie.id} 
              className="animate-fade-in"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <MovieCard movie={movie} />
            </div>
          ))
        )}
      </div>

      {/* Loading indicator for page changes */}
      {loading && data && (
        <div className="flex justify-center py-8">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex justify-center items-center space-x-2 py-8">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1 || loading}
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 focus-ring"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Previous
          </button>

          <div className="flex space-x-1">
            {Array.from({ length: Math.min(5, data.total_pages) }, (_, i) => {
              let pageNum;
              if (data.total_pages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= data.total_pages - 2) {
                pageNum = data.total_pages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  disabled={loading}
                  className={`px-4 py-2 text-sm font-medium rounded-lg disabled:cursor-not-allowed transition-all duration-200 focus-ring ${
                    pageNum === currentPage
                      ? 'text-white bg-blue-600 border border-blue-600 shadow-md'
                      : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === data.total_pages || loading}
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 focus-ring"
          >
            Next
            <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      )}

      {/* Results info */}
      {data && (
        <div className="text-center text-sm text-gray-600 dark:text-gray-400 mt-4">
          Showing {((currentPage - 1) * data.per_page) + 1} to {Math.min(currentPage * data.per_page, data.total)} of {data.total} movies
        </div>
      )}
    </div>
  );
}