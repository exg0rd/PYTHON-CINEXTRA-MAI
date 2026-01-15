'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Actor, CrewDepartment } from '@/types/actor';
import { apiClient } from '@/lib/api';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';

interface MovieCastProps {
  movieId: number;
  className?: string;
}

export default function MovieCast({ movieId, className = "" }: MovieCastProps) {
  const [cast, setCast] = useState<Actor[]>([]);
  const [crew, setCrew] = useState<CrewDepartment>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'cast' | 'crew'>('cast');

  useEffect(() => {
    const fetchCastAndCrew = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const [castData, crewData] = await Promise.all([
          apiClient.getMovieCast(movieId),
          apiClient.getMovieCrew(movieId)
        ]);
        
        setCast(castData);
        setCrew(crewData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Не удалось загрузить актёров и съёмочную группу');
      } finally {
        setIsLoading(false);
      }
    };

    if (movieId) {
      fetchCastAndCrew();
    }
  }, [movieId]);

  if (isLoading) {
    return (
      <div className={`${className}`}>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className}`}>
        <ErrorMessage 
          message={error} 
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  const mainCast = cast.slice(0, 12); // Show first 12 cast members
  const crewDepartments = Object.keys(crew);

  return (
    <div className={`${className}`}>
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
        <button
          onClick={() => setActiveTab('cast')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'cast'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
          }`}
        >
          Актёры ({cast.length})
        </button>
        <button
          onClick={() => setActiveTab('crew')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'crew'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
          }`}
        >
          Съёмочная группа ({Object.values(crew).reduce((total, dept) => total + dept.length, 0)})
        </button>
      </div>

      {/* Cast Tab */}
      {activeTab === 'cast' && (
        <div>
          {cast.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">
              Информация об актёрах недоступна
            </p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {mainCast.map((actor) => (
                <Link
                  key={actor.person_id}
                  href={`/actors/${actor.person_id}`}
                  className="group block bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden border border-gray-200 dark:border-gray-700"
                >
                  <div className="aspect-[2/3] relative bg-gray-100 dark:bg-gray-700">
                    {actor.profile_path ? (
                      <Image
                        src={`https://image.tmdb.org/t/p/w185${actor.profile_path}`}
                        alt={actor.name}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-200"
                        sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, (max-width: 1024px) 25vw, 16vw"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500">
                        <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="p-3">
                    <h4 className="font-semibold text-sm text-gray-900 dark:text-white truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {actor.name}
                    </h4>
                    {actor.character && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-1">
                        {actor.character}
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
          
          {cast.length > 12 && (
            <div className="text-center mt-6">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Показано {mainCast.length} из {cast.length} актёров
              </p>
            </div>
          )}
        </div>
      )}

      {/* Crew Tab */}
      {activeTab === 'crew' && (
        <div>
          {crewDepartments.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">
              Информация о съёмочной группе недоступна
            </p>
          ) : (
            <div className="space-y-6">
              {crewDepartments.map((department) => (
                <div key={department} className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                  <h4 className="font-semibold text-lg text-gray-900 dark:text-white mb-3">
                    {department}
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {crew[department].slice(0, 6).map((member, index) => (
                      <Link
                        key={`${member.person_id}-${index}`}
                        href={`/actors/${member.person_id}`}
                        className="flex items-center space-x-3 p-2 rounded-lg hover:bg-white dark:hover:bg-gray-700 transition-colors group"
                      >
                        <div className="flex-shrink-0">
                          {member.profile_path ? (
                            <img
                              src={`https://image.tmdb.org/t/p/w92${member.profile_path}`}
                              alt={member.name}
                              className="w-10 h-10 rounded-full object-cover"
                            />
                          ) : (
                            <div className="w-10 h-10 bg-gray-200 dark:bg-gray-600 rounded-full flex items-center justify-center">
                              <svg className="w-6 h-6 text-gray-400 dark:text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                              </svg>
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                            {member.name}
                          </p>
                          {member.job && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                              {member.job}
                            </p>
                          )}
                        </div>
                      </Link>
                    ))}
                  </div>
                  {crew[department].length > 6 && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      Ещё +{crew[department].length - 6}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}