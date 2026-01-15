'use client';

import React from 'react';
import MovieCard from './MovieCard';

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

interface SearchResultsProps {
  results: Movie[];
  totalCount: number;
  currentPage: number;
  totalPages: number;
  query?: string;
  loading?: boolean;
  error?: string | null;
  onPageChange: (page: number) => void;
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  totalCount,
  currentPage,
  totalPages,
  query,
  loading = false,
  error = null,
  onPageChange
}) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Загрузка фильмов...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">
          <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Ошибка поиска</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 mb-4">
          <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Фильмы не найдены</h3>
        <p className="text-gray-600 mb-4">
          {query 
            ? `Не найдено фильмов по запросу "${query}". Попробуйте другие ключевые слова или проверьте правописание.`
            : 'На данный момент фильмы недоступны.'
          }
        </p>
        {query && (
          <div className="text-sm text-gray-500">
            <p>Советы по поиску:</p>
            <ul className="mt-2 space-y-1">
              <li>• Попробуйте другие ключевые слова</li>
              <li>• Проверьте правописание</li>
              <li>• Используйте более общие термины</li>
              <li>• Ищите по жанру, режиссёру или году</li>
            </ul>
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      {/* Results Summary */}
      <div className="mb-6">
        <p className="text-sm text-gray-600">
          {query 
            ? `Найдено ${totalCount} ${totalCount === 1 ? 'фильм' : totalCount < 5 ? 'фильма' : 'фильмов'} по запросу "${query}"`
            : `Показано ${totalCount} ${totalCount === 1 ? 'фильм' : totalCount < 5 ? 'фильма' : 'фильмов'}`
          }
          {totalPages > 1 && (
            <span> (Страница {currentPage} из {totalPages})</span>
          )}
        </p>
      </div>

      {/* Movie Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6 mb-8">
        {results.map((movie) => (
          <MovieCard key={movie.id} movie={movie} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Назад
          </button>
          
          {/* Page Numbers */}
          <div className="flex space-x-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => onPageChange(pageNum)}
                  className={`px-3 py-2 text-sm font-medium rounded-md ${
                    currentPage === pageNum
                      ? 'text-white bg-blue-600 border border-blue-600'
                      : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Вперёд
          </button>
        </div>
      )}
    </div>
  );
};