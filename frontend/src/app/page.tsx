'use client';

import { SearchInterface } from '@/components/ui/SearchInterface';
import { SearchResults } from '@/components/ui/SearchResults';
import { useMovieSearch } from '@/hooks/useMovieSearch';

export default function Home() {
  const {
    searchState,
    setQuery,
    setSortCriteria,
    setPage,
    clearSearch
  } = useMovieSearch();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-12 text-center">
        <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-4 leading-tight">
          Фильмы на любой вкус и цвет
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          Полная коллекция фильмов со всего света. Найди свой любимый. 
        </p>
      </div>
      
      {/* Search Interface */}
      <SearchInterface
        query={searchState.query}
        onQueryChange={setQuery}
        onClearSearch={clearSearch}
        sortBy={searchState.sortBy}
        sortOrder={searchState.sortOrder}
        onSortChange={setSortCriteria}
        loading={searchState.loading}
      />

      {/* Search Results */}
      <SearchResults
        results={searchState.results}
        totalCount={searchState.totalCount}
        currentPage={searchState.currentPage}
        totalPages={searchState.totalPages}
        query={searchState.query}
        loading={searchState.loading}
        error={searchState.error}
        onPageChange={setPage}
      />
    </div>
  );
}
