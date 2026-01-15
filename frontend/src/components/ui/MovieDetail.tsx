'use client';

import { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { AlertCircle, Film } from 'lucide-react';
import { MovieDetail as MovieDetailType } from '@/types/movie';
import { Review, ReviewCreate, ReviewUpdate } from '@/types/review';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';
import StarRating from './StarRating';
import ReviewList from './ReviewList';
import ReviewForm from './ReviewForm';
import MovieCast from './MovieCast';
import MovieFrames from './MovieFrames';
import VideoPlayer from '../video/VideoPlayer';
import { useAuthState } from '@/hooks/useAuthState';
import { useReviews } from '@/hooks/useReviews';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface MovieDetailProps {
  movie: MovieDetailType;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  canRetry?: boolean;
}

export default function MovieDetail({ movie, loading, error, onRetry, canRetry = true }: MovieDetailProps) {
  const { user } = useAuthState();
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [editingReview, setEditingReview] = useState<Review | null>(null);
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);

  const {
    reviews,
    totalReviews,
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    isLoading: reviewsLoading,
    error: reviewsError,
    userReview,
    createReview,
    updateReview,
    deleteReview,
    loadPage,
    refresh: refreshReviews,
  } = useReviews({ movieId: movie?.id || 0 });

  const handleReviewSubmit = async (reviewData: ReviewCreate | ReviewUpdate) => {
    if (editingReview) {
      await handleUpdateReview(reviewData as ReviewUpdate);
    } else {
      await handleCreateReview(reviewData as ReviewCreate);
    }
  };

  const handleCreateReview = async (reviewData: ReviewCreate) => {
    setIsSubmittingReview(true);
    try {
      await createReview(reviewData);
      setShowReviewForm(false);
    } catch (error) {
      throw error; // Let ReviewForm handle the error display
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleUpdateReview = async (reviewData: ReviewUpdate) => {
    if (!editingReview) return;
    
    setIsSubmittingReview(true);
    try {
      await updateReview(editingReview.id, reviewData);
      setEditingReview(null);
    } catch (error) {
      throw error; // Let ReviewForm handle the error display
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleDeleteReview = async (reviewId: number) => {
    await deleteReview(reviewId);
  };

  const handleEditReview = (review: Review) => {
    setEditingReview(review);
    setShowReviewForm(false);
  };

  const handleCancelEdit = () => {
    setEditingReview(null);
  };
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="flex flex-col lg:flex-row gap-8">
            <div className="lg:w-1/3">
              <div className="aspect-[2/3] bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            </div>
            <div className="lg:w-2/3 space-y-4">
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ErrorMessage 
          message={error} 
          onRetry={canRetry ? onRetry : undefined}
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
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Navigation */}
      <div className="mb-8">
        <Link 
          href="/"
          className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors duration-200 font-medium focus-ring rounded-lg px-3 py-2"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Назад к фильмам
        </Link>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col lg:flex-row">
          {/* Movie Poster */}
          <div className="lg:w-1/3 p-6 lg:p-8">
            <div className="aspect-[2/3] relative bg-gray-100 dark:bg-gray-700 rounded-xl overflow-hidden shadow-lg">
              {movie.poster_url ? (
                <Image
                  src={movie.poster_url}
                  alt={`${movie.title} poster`}
                  fill
                  className="object-cover"
                  sizes="(max-width: 1024px) 100vw, 33vw"
                  priority
                />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500">
                  <svg className="w-20 h-20" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </div>
          </div>

          {/* Movie Information */}
          <div className="lg:w-2/3 p-6 lg:p-8">
            <div className="space-y-8">
              {/* Title and Basic Info */}
              <div>
                <h1 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-white mb-4 leading-tight">
                  {movie.title}
                </h1>
                <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                  <span className="flex items-center bg-yellow-50 dark:bg-yellow-900/20 px-3 py-1 rounded-full">
                    <svg className="w-4 h-4 text-yellow-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    <span className="text-yellow-700 dark:text-yellow-400 font-semibold">
                      {movie.rating.toFixed(1)}
                    </span>
                  </span>
                  {movie.average_user_rating && (
                    <span className="flex items-center bg-blue-50 dark:bg-blue-900/20 px-3 py-1 rounded-full">
                      <svg className="w-4 h-4 text-blue-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span className="text-blue-700 dark:text-blue-400 font-semibold">
                        {movie.average_user_rating.toFixed(1)} ({movie.review_count} отзывов)
                      </span>
                    </span>
                  )}
                  <span className="bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded-full font-medium">
                    {movie.year}
                  </span>
                  <span className="bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 px-3 py-1 rounded-full font-medium">
                    {movie.genre}
                  </span>
                  <span className="bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded-full font-medium">
                    {movie.duration} min
                  </span>
                </div>
              </div>

              {/* Director */}
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 uppercase tracking-wide">
                  Режиссёр
                </h3>
                <p className="text-gray-700 dark:text-gray-300 font-medium">{movie.director}</p>
              </div>

              {/* Cast */}
              {movie.cast && movie.cast.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 uppercase tracking-wide">
                    Актёры
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {movie.cast.map((actor, index) => (
                      <span 
                        key={index}
                        className="px-4 py-2 bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-600 text-gray-700 dark:text-gray-300 rounded-full text-sm font-medium hover:from-blue-100 hover:to-blue-200 dark:hover:from-blue-900/30 dark:hover:to-blue-800/30 transition-all duration-200"
                      >
                        {actor}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Release Date */}
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 uppercase tracking-wide">
                  Дата выхода
                </h3>
                <p className="text-gray-700 dark:text-gray-300 font-medium">
                  {new Date(movie.release_date).toLocaleDateString('ru-RU', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              </div>

              {/* Description */}
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 uppercase tracking-wide">
                  Описание
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed text-base">
                  {movie.description}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Video Player Section */}
      {movie.video_file_id && (
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden border border-gray-100 dark:border-gray-700">
          <div className="p-6 lg:p-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              Смотреть фильм
            </h2>
            
            {movie.processing_status === 'completed' && movie.hls_manifest_url ? (
              <div className="aspect-video bg-black rounded-xl overflow-hidden">
                <VideoPlayer
                  src={`${API_BASE_URL}/api/stream/${movie.id}/playlist.m3u8`}
                  poster={movie.poster_url}
                  subtitles={movie.subtitles || []}
                  audioTracks={movie.audio_tracks || []}
                  onTimeUpdate={(currentTime, duration) => {
                    // Track viewing progress for analytics
                    console.log(`Watching ${movie.title}: ${currentTime}/${duration}`);
                  }}
                  onQualityChange={(quality) => {
                    console.log(`Quality changed to: ${quality}`);
                  }}
                  className="w-full h-full"
                />
              </div>
            ) : movie.processing_status === 'processing' || movie.processing_status === 'queued' ? (
              <div className="aspect-video bg-gray-100 dark:bg-gray-900 rounded-xl flex items-center justify-center">
                <div className="text-center p-8">
                  <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    Видео обрабатывается
                  </p>
                  <p className="text-gray-600 dark:text-gray-400">
                    Это может занять несколько минут. Пожалуйста, зайдите позже.
                  </p>
                </div>
              </div>
            ) : movie.processing_status === 'failed' ? (
              <div className="aspect-video bg-red-50 dark:bg-red-900/20 rounded-xl flex items-center justify-center border-2 border-red-200 dark:border-red-800">
                <div className="text-center p-8">
                  <AlertCircle className="w-16 h-16 text-red-600 dark:text-red-400 mx-auto mb-4" />
                  <p className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
                    Ошибка обработки видео
                  </p>
                  <p className="text-red-600 dark:text-red-400">
                    Пожалуйста, свяжитесь с поддержкой или попробуйте загрузить видео снова.
                  </p>
                </div>
              </div>
            ) : (
              <div className="aspect-video bg-gray-100 dark:bg-gray-900 rounded-xl flex items-center justify-center">
                <div className="text-center p-8">
                  <Film className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    Видео недоступно
                  </p>
                  <p className="text-gray-600 dark:text-gray-400">
                    У этого фильма пока нет видеофайла.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Movie Frames Section */}
      {movie.video_file_id && movie.processing_status === 'completed' && movie.duration_seconds && (
        <div className="mt-8">
          <MovieFrames 
            movieId={movie.id} 
            movieTitle={movie.title}
            durationSeconds={movie.duration_seconds}
          />
        </div>
      )}

      {/* Cast & Crew Section */}
      <div className="mt-8 bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden border border-gray-100 dark:border-gray-700">
        <div className="p-6 lg:p-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Актёры и съёмочная группа
          </h2>
          <MovieCast movieId={movie.id} />
        </div>
      </div>

      {/* Reviews Section */}
      <div className="mt-8 bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden border border-gray-100 dark:border-gray-700">
        <div className="p-6 lg:p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Отзывы {totalReviews > 0 && `(${totalReviews})`}
            </h2>
            
            {user && !userReview && !showReviewForm && !editingReview && (
              <button
                onClick={() => setShowReviewForm(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-colors"
              >
                Написать отзыв
              </button>
            )}
          </div>

          {/* Authentication prompt for non-logged in users */}
          {!user && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
              <p className="text-blue-800 dark:text-blue-200">
                <Link href="/auth" className="font-medium hover:underline">
                  Войдите
                </Link>
                {' '}чтобы написать отзыв и поделиться своим мнением об этом фильме.
              </p>
            </div>
          )}

          {/* Review Form */}
          {user && (showReviewForm || editingReview) && (
            <div className="mb-8 p-6 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                {editingReview ? 'Редактировать отзыв' : 'Написать отзыв'}
              </h3>
              <ReviewForm
                movieId={movie.id}
                existingReview={editingReview ? {
                  id: editingReview.id,
                  rating: editingReview.rating,
                  review_text: editingReview.review_text
                } : undefined}
                onSubmit={handleReviewSubmit}
                onCancel={editingReview ? handleCancelEdit : () => setShowReviewForm(false)}
                isLoading={isSubmittingReview}
              />
            </div>
          )}

          {/* User's existing review */}
          {user && userReview && !editingReview && (
            <div className="mb-8 p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-green-800 dark:text-green-200">
                  Ваш отзыв
                </h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleEditReview(userReview)}
                    className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                  >
                    Редактировать
                  </button>
                  <button
                    onClick={() => handleDeleteReview(userReview.id)}
                    className="text-sm text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 font-medium"
                  >
                    Удалить
                  </button>
                </div>
              </div>
              <div className="flex items-center space-x-2 mb-3">
                <StarRating rating={userReview.rating} size="sm" />
                <span className="text-sm font-medium text-green-700 dark:text-green-300">
                  {userReview.rating}/10
                </span>
              </div>
              {userReview.review_text && (
                <p className="text-green-700 dark:text-green-300 leading-relaxed">
                  {userReview.review_text}
                </p>
              )}
            </div>
          )}

          {/* Reviews Error */}
          {reviewsError && (
            <div className="mb-6">
              <ErrorMessage 
                message={reviewsError} 
                onRetry={refreshReviews}
                className="max-w-md"
              />
            </div>
          )}

          {/* Reviews List - Only show if not loading and no error */}
          {!reviewsLoading && !reviewsError && (
            <ReviewList
              reviews={reviews.filter(review => review.user_id !== user?.id)} // Exclude user's own review
              isLoading={reviewsLoading}
              onEditReview={handleEditReview}
              onDeleteReview={handleDeleteReview}
            />
          )}

          {/* Loading state for reviews */}
          {reviewsLoading && (
            <ReviewList
              reviews={[]}
              isLoading={true}
              onEditReview={handleEditReview}
              onDeleteReview={handleDeleteReview}
            />
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Страница {currentPage} из {totalPages}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => loadPage(currentPage - 1)}
                  disabled={!hasPrev || reviewsLoading}
                  className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Назад
                </button>
                <button
                  onClick={() => loadPage(currentPage + 1)}
                  disabled={!hasNext || reviewsLoading}
                  className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Вперёд
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}