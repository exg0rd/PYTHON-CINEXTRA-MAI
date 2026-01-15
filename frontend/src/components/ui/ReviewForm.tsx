'use client';

import React, { useState } from 'react';
import StarRating from './StarRating';
import { ReviewCreate, ReviewUpdate } from '@/types/review';

interface ReviewFormProps {
  movieId: number;
  existingReview?: {
    id: number;
    rating: number;
    review_text?: string;
  };
  onSubmit: (reviewData: ReviewCreate | ReviewUpdate) => Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
  className?: string;
}

export default function ReviewForm({
  movieId,
  existingReview,
  onSubmit,
  onCancel,
  isLoading = false,
  className = ''
}: ReviewFormProps) {
  const [rating, setRating] = useState(existingReview?.rating || 0);
  const [reviewText, setReviewText] = useState(existingReview?.review_text || '');
  const [error, setError] = useState<string | null>(null);

  const isEditing = !!existingReview;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (rating === 0) {
      setError('Пожалуйста, выберите оценку');
      return;
    }

    try {
      const reviewData = {
        rating,
        review_text: reviewText.trim() || undefined
      };

      await onSubmit(reviewData);
      
      // Reset form if creating new review
      if (!isEditing) {
        setRating(0);
        setReviewText('');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить отзыв');
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`space-y-4 ${className}`}>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Ваша оценка
        </label>
        <StarRating
          rating={rating}
          interactive={true}
          onRatingChange={setRating}
          size="lg"
        />
      </div>

      <div>
        <label htmlFor="review-text" className="block text-sm font-medium text-gray-700 mb-2">
          Ваш отзыв (необязательно)
        </label>
        <textarea
          id="review-text"
          value={reviewText}
          onChange={(e) => setReviewText(e.target.value)}
          placeholder="Поделитесь своими мыслями об этом фильме..."
          rows={4}
          maxLength={2000}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-vertical"
        />
        <div className="text-right text-xs text-gray-500 mt-1">
          {reviewText.length}/2000 символов
        </div>
      </div>

      {error && (
        <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
          {error}
        </div>
      )}

      <div className="flex space-x-3">
        <button
          type="submit"
          disabled={isLoading || rating === 0}
          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {isEditing ? 'Обновление...' : 'Отправка...'}
            </span>
          ) : (
            isEditing ? 'Обновить отзыв' : 'Отправить отзыв'
          )}
        </button>
        
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Отмена
          </button>
        )}
      </div>
    </form>
  );
}