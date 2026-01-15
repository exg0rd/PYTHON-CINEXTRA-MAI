'use client';

import React, { useState } from 'react';
import { Review } from '@/types/review';
import StarRating from './StarRating';
import { useAuthState } from '@/hooks/useAuthState';

interface ReviewListProps {
  reviews?: Review[]; // Make optional with default
  isLoading?: boolean;
  onEditReview?: (review: Review) => void;
  onDeleteReview?: (reviewId: number) => Promise<void>;
  className?: string;
}

export default function ReviewList({
  reviews = [], // Default to empty array
  isLoading = false,
  onEditReview,
  onDeleteReview,
  className = ''
}: ReviewListProps) {
  const { user } = useAuthState();
  const [deletingReviewId, setDeletingReviewId] = useState<number | null>(null);

  const handleDeleteReview = async (reviewId: number) => {
    if (!onDeleteReview) return;
    
    if (window.confirm('Вы уверены, что хотите удалить этот отзыв?')) {
      try {
        setDeletingReviewId(reviewId);
        await onDeleteReview(reviewId);
      } catch (error) {
        console.error('Failed to delete review:', error);
      } finally {
        setDeletingReviewId(null);
      }
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch (error) {
      console.error('Error formatting date:', error);
      return 'Неизвестная дата';
    }
  };

  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        {Array.from({ length: 3 }, (_, index) => (
          <div key={index} className="animate-pulse">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
                  <div className="h-4 bg-gray-300 rounded w-24"></div>
                </div>
                <div className="h-4 bg-gray-300 rounded w-20"></div>
              </div>
              <div className="flex items-center space-x-2 mb-3">
                <div className="flex space-x-1">
                  {Array.from({ length: 5 }, (_, i) => (
                    <div key={i} className="w-4 h-4 bg-gray-300 rounded"></div>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-300 rounded w-full"></div>
                <div className="h-4 bg-gray-300 rounded w-3/4"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!Array.isArray(reviews) || reviews.length === 0) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <div className="text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10m0 0V6a2 2 0 00-2-2H9a2 2 0 00-2 2v2m0 0v10a2 2 0 002 2h6a2 2 0 002-2V8M9 12h6" />
          </svg>
          <p className="text-lg font-medium text-gray-900 mb-2">Пока нет отзывов</p>
          <p className="text-gray-500">Будьте первым, кто поделится своим мнением об этом фильме!</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {reviews.map((review) => {
        try {
          const isOwnReview = user?.id === review.user_id;
          const isDeleting = deletingReviewId === review.id;

          return (
            <div key={review.id} className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-blue-600">
                      {review.user?.username?.charAt(0)?.toUpperCase() || '?'}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{review.user?.username || 'Неизвестный пользователь'}</p>
                    <p className="text-sm text-gray-500">{formatDate(review.created_at)}</p>
                  </div>
                </div>
                
                {isOwnReview && (onEditReview || onDeleteReview) && (
                  <div className="flex space-x-2">
                    {onEditReview && (
                      <button
                        onClick={() => onEditReview(review)}
                        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Редактировать
                      </button>
                    )}
                    {onDeleteReview && (
                      <button
                        onClick={() => handleDeleteReview(review.id)}
                        disabled={isDeleting}
                        className="text-sm text-red-600 hover:text-red-800 font-medium disabled:opacity-50"
                      >
                        {isDeleting ? 'Удаление...' : 'Удалить'}
                      </button>
                    )}
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2 mb-3">
                <StarRating rating={review.rating || 0} size="sm" />
                <span className="text-sm font-medium text-gray-700">
                  {review.rating || 0}/10
                </span>
              </div>

              {review.review_text && (
                <div className="text-gray-700 leading-relaxed">
                  <p>{review.review_text}</p>
                </div>
              )}

              {review.updated_at !== review.created_at && (
                <p className="text-xs text-gray-400 mt-3">
                  Отредактировано {formatDate(review.updated_at)}
                </p>
              )}
            </div>
          );
        } catch (error) {
          console.error('Error rendering review:', error, review);
          return (
            <div key={review.id || Math.random()} className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600 text-sm">Ошибка отображения отзыва</p>
            </div>
          );
        }
      })}
    </div>
  );
}