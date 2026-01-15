'use client';

import React from 'react';
import { Film, Star, TrendingUp } from 'lucide-react';

interface MovieAnalyticsData {
  most_reviewed_movies: Array<{
    id: number;
    title: string;
    review_count: number;
    average_rating: number | null;
  }>;
  highest_rated_movies: Array<{
    id: number;
    title: string;
    original_rating: number;
    user_rating: number | null;
    review_count: number;
  }>;
  genre_popularity: Array<{
    genre: string;
    movie_count: number;
    total_reviews: number;
  }>;
}

interface MovieAnalyticsChartProps {
  data?: MovieAnalyticsData;
  detailed?: boolean;
}

export const MovieAnalyticsChart: React.FC<MovieAnalyticsChartProps> = ({ 
  data, 
  detailed = false 
}) => {
  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Аналитика фильмов</h3>
        <div className="text-center py-8">
          <div className="text-gray-400">Нет данных о фильмах</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-6">Аналитика фильмов</h3>
      
      <div className="space-y-6">
        {/* Most Reviewed Movies */}
        <div>
          <div className="flex items-center mb-4">
            <TrendingUp className="h-5 w-5 text-blue-600 mr-2" />
            <h4 className="text-md font-medium text-gray-900">Самые обсуждаемые фильмы</h4>
          </div>
          <div className="space-y-2">
            {data.most_reviewed_movies.slice(0, detailed ? 10 : 5).map((movie, index) => (
              <div key={movie.id} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <span className="text-sm font-medium text-gray-500 w-6">#{index + 1}</span>
                  <span className="text-sm font-medium text-gray-900 ml-2 truncate">
                    {movie.title}
                  </span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-600">{movie.review_count} отзывов</span>
                  {movie.average_rating && (
                    <div className="flex items-center">
                      <Star className="h-4 w-4 text-yellow-400 mr-1" />
                      <span className="text-sm font-medium text-gray-900">
                        {movie.average_rating.toFixed(1)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Highest Rated Movies */}
        <div>
          <div className="flex items-center mb-4">
            <Star className="h-5 w-5 text-yellow-600 mr-2" />
            <h4 className="text-md font-medium text-gray-900">Самые высоко оцененные фильмы</h4>
          </div>
          <div className="space-y-2">
            {data.highest_rated_movies.slice(0, detailed ? 10 : 5).map((movie, index) => (
              <div key={movie.id} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <span className="text-sm font-medium text-gray-500 w-6">#{index + 1}</span>
                  <span className="text-sm font-medium text-gray-900 ml-2 truncate">
                    {movie.title}
                  </span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-600">{movie.review_count} отзывов</span>
                  <div className="flex items-center">
                    <Star className="h-4 w-4 text-yellow-400 mr-1" />
                    <span className="text-sm font-medium text-gray-900">
                      {movie.user_rating?.toFixed(1) || movie.original_rating.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Genre Popularity */}
        {detailed && (
          <div>
            <div className="flex items-center mb-4">
              <Film className="h-5 w-5 text-green-600 mr-2" />
              <h4 className="text-md font-medium text-gray-900">Популярность жанров</h4>
            </div>
            <div className="space-y-2">
              {data.genre_popularity.slice(0, 8).map((genre, index) => (
                <div key={genre.genre} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-500 w-6">#{index + 1}</span>
                    <span className="text-sm font-medium text-gray-900 ml-2">
                      {genre.genre}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-gray-600">{genre.movie_count} фильмов</span>
                    <span className="text-sm text-gray-600">{genre.total_reviews} отзывов</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {!detailed && data.genre_popularity.length > 0 && (
          <div>
            <div className="flex items-center mb-4">
              <Film className="h-5 w-5 text-green-600 mr-2" />
              <h4 className="text-md font-medium text-gray-900">Топ жанров</h4>
            </div>
            <div className="flex flex-wrap gap-2">
              {data.genre_popularity.slice(0, 6).map((genre) => (
                <span
                  key={genre.genre}
                  className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
                >
                  {genre.genre} ({genre.total_reviews})
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};