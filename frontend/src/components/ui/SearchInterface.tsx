'use client';

import React, { useState } from 'react';
import { Search, X, User, Film } from 'lucide-react';
import { SortCriteria, SortOrder } from '@/hooks/useMovieSearch';
import ActorSearch from './ActorSearch';

interface SearchInterfaceProps {
  query: string;
  onQueryChange: (query: string) => void;
  onClearSearch: () => void;
  sortBy: SortCriteria | null;
  sortOrder: SortOrder;
  onSortChange: (sortBy: SortCriteria | null, sortOrder: SortOrder) => void;
  loading?: boolean;
}

type SearchTab = 'movies' | 'actors';

const sortOptions = [
  { value: SortCriteria.YEAR, label: 'Год' },
  { value: SortCriteria.RATING, label: 'Рейтинг' },
  { value: SortCriteria.REVIEW_COUNT, label: 'Отзывы' },
  { value: SortCriteria.TITLE, label: 'Название' }
];

export const SearchInterface: React.FC<SearchInterfaceProps> = ({
  query,
  onQueryChange,
  onClearSearch,
  sortBy,
  sortOrder,
  onSortChange,
  loading = false
}) => {
  const [localQuery, setLocalQuery] = useState(query);
  const [activeTab, setActiveTab] = useState<SearchTab>('movies');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setLocalQuery(value);
  };

  const handleSearch = () => {
    onQueryChange(localQuery);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleClear = () => {
    setLocalQuery('');
    onClearSearch();
  };

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (value === '') {
      onSortChange(null, sortOrder);
    } else {
      onSortChange(value as SortCriteria, sortOrder);
    }
  };

  const handleSortOrderToggle = () => {
    if (sortBy) {
      const newOrder = sortOrder === SortOrder.ASC ? SortOrder.DESC : SortOrder.ASC;
      onSortChange(sortBy, newOrder);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto mb-8">
      {/* Search Tabs */}
      <div className="flex border-b border-gray-200 mb-4">
        <button
          onClick={() => setActiveTab('movies')}
          className={`flex items-center px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'movies'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <Film className="w-4 h-4 mr-2" />
          Фильмы
        </button>
        <button
          onClick={() => setActiveTab('actors')}
          className={`flex items-center px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'actors'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <User className="w-4 h-4 mr-2" />
          Актёры
        </button>
      </div>

      {activeTab === 'movies' ? (
        <>
          {/* Movie Search Input */}
          <div className="relative mb-4 flex gap-2">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Поиск фильмов по названию, описанию, жанру, режиссёру или актёрам..."
                value={localQuery}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                className="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
                disabled={loading}
              />
              {localQuery && (
                <button
                  onClick={handleClear}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center hover:text-gray-600"
                  disabled={loading}
                >
                  <X className="h-5 w-5 text-gray-400" />
                </button>
              )}
            </div>
            <button
              onClick={handleSearch}
              disabled={loading || !localQuery}
              className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Поиск"
            >
              <Search className="h-5 w-5" />
            </button>
          </div>

          {/* Sort Controls */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label htmlFor="sort-select" className="text-sm font-medium text-gray-700">
                Сортировка:
              </label>
              <select
                id="sort-select"
                value={sortBy || ''}
                onChange={handleSortChange}
                className="block px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                disabled={loading}
              >
                <option value="">По умолчанию</option>
                {sortOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {sortBy && (
              <button
                onClick={handleSortOrderToggle}
                className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                disabled={loading}
                title={`Сортировка ${sortOrder === SortOrder.ASC ? 'по возрастанию' : 'по убыванию'}`}
              >
                <span>{sortOrder === SortOrder.ASC ? '↑' : '↓'}</span>
                <span>{sortOrder === SortOrder.ASC ? 'По возрастанию' : 'По убыванию'}</span>
              </button>
            )}

            {/* Active Search Indicator */}
            {query && (
              <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 text-blue-700 rounded-md text-sm">
                <span>Поиск: "{query}"</span>
                <button
                  onClick={handleClear}
                  className="text-blue-500 hover:text-blue-700"
                  title="Очистить поиск"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
                <span>Поиск...</span>
              </div>
            )}
          </div>
        </>
      ) : (
        /* Actor Search */
        <div className="mb-4">
          <ActorSearch 
            placeholder="Поиск актёров по имени..."
            className="w-full"
          />
          <p className="text-sm text-gray-500 mt-2">
            Найдите актёров и посмотрите их фильмографию
          </p>
        </div>
      )}
    </div>
  );
};