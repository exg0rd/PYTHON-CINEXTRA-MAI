'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Actor } from '@/types/actor';
import { apiClient } from '@/lib/api';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';

interface ActorSearchProps {
  onActorSelect?: (actor: Actor) => void;
  placeholder?: string;
  className?: string;
}

export default function ActorSearch({ 
  onActorSelect, 
  placeholder = "Search for actors...",
  className = ""
}: ActorSearchProps) {
  const [query, setQuery] = useState('');
  const [actors, setActors] = useState<Actor[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const searchActors = async () => {
      if (query.trim().length < 2) {
        setActors([]);
        setShowResults(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await apiClient.searchActors(query.trim(), 1, 10);
        setActors(response.actors);
        setShowResults(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to search actors');
        setActors([]);
      } finally {
        setIsLoading(false);
      }
    };

    const debounceTimer = setTimeout(searchActors, 300);
    return () => clearTimeout(debounceTimer);
  }, [query]);

  const handleActorClick = (actor: Actor) => {
    if (onActorSelect) {
      onActorSelect(actor);
    } else {
      router.push(`/actors/${actor.person_id}`);
    }
    setShowResults(false);
    setQuery('');
  };

  const handleInputBlur = () => {
    // Delay hiding results to allow for clicks
    setTimeout(() => setShowResults(false), 200);
  };

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.trim().length >= 2 && setShowResults(true)}
          onBlur={handleInputBlur}
          placeholder={placeholder}
          className="w-full px-4 py-2 pl-10 pr-4 text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <div className="absolute inset-y-0 left-0 flex items-center pl-3">
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        {isLoading && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            <LoadingSpinner size="sm" />
          </div>
        )}
      </div>

      {showResults && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-96 overflow-y-auto">
          {error && (
            <div className="p-4">
              <ErrorMessage message={error} />
            </div>
          )}
          
          {!error && actors.length === 0 && query.trim().length >= 2 && !isLoading && (
            <div className="p-4 text-gray-500 text-center">
              No actors found for "{query}"
            </div>
          )}
          
          {!error && actors.length > 0 && (
            <div className="py-2">
              {actors.map((actor) => (
                <button
                  key={actor.person_id}
                  onClick={() => handleActorClick(actor)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      {actor.profile_path ? (
                        <img
                          src={`https://image.tmdb.org/t/p/w92${actor.profile_path}`}
                          alt={actor.name}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                          <svg className="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                          </svg>
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {actor.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {actor.movie_count} movie{actor.movie_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}