'use client';

import React from 'react';
import { useMovie } from '@/hooks/useMovie';
import MovieDetail from '@/components/ui/MovieDetail';

interface MovieDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function MovieDetailPage({ params }: MovieDetailPageProps) {
  // We need to unwrap the params Promise in a client component
  const [movieId, setMovieId] = React.useState<number | null>(null);
  
  React.useEffect(() => {
    params.then(({ id }) => {
      const numericId = parseInt(id, 10);
      if (!isNaN(numericId)) {
        setMovieId(numericId);
      }
    });
  }, [params]);

  const { data: movie, loading, error, refetch, canRetry } = useMovie({ 
    id: movieId || 0, 
    autoFetch: movieId !== null 
  });

  if (movieId === null) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-blue-600"></div>
        </div>
      </div>
    );
  }

  if (!movie && !loading && !error) {
    return null;
  }

  return (
    <MovieDetail 
      movie={movie!} 
      loading={loading} 
      error={error} 
      onRetry={canRetry ? refetch : undefined}
      canRetry={canRetry}
    />
  );
}