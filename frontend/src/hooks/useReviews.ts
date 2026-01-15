'use client';

import { useState, useEffect } from 'react';
import { Review, ReviewCreate, ReviewUpdate, PaginatedReviewsResponse } from '@/types/review';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';

interface UseReviewsOptions {
  movieId: number;
  page?: number;
  perPage?: number;
}

interface UseReviewsReturn {
  reviews: Review[];
  totalReviews: number;
  currentPage: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
  isLoading: boolean;
  error: string | null;
  userReview: Review | null;
  createReview: (reviewData: ReviewCreate) => Promise<Review>;
  updateReview: (reviewId: number, reviewData: ReviewUpdate) => Promise<Review>;
  deleteReview: (reviewId: number) => Promise<void>;
  loadPage: (page: number) => Promise<void>;
  refresh: () => Promise<void>;
}

export function useReviews({ movieId, page = 1, perPage = 20 }: UseReviewsOptions): UseReviewsReturn {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [totalReviews, setTotalReviews] = useState(0);
  const [currentPage, setCurrentPage] = useState(page);
  const [totalPages, setTotalPages] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userReview, setUserReview] = useState<Review | null>(null);

  const { user, token, isLoading: authLoading } = useAuth();

  const fetchReviews = async (pageNum: number = currentPage) => {
    setIsLoading(true);
    setError(null);

    try {
      const data: PaginatedReviewsResponse = await apiClient.getMovieReviews(movieId, pageNum, perPage);
      
      setReviews(data.reviews || []);
      setTotalReviews(data.total || 0);
      setCurrentPage(data.page || 1);
      setTotalPages(data.total_pages || 1);
      setHasNext(data.has_next || false);
      setHasPrev(data.has_prev || false);

      // Find user's review if authenticated and reviews exist
      if (user && data.reviews && Array.isArray(data.reviews)) {
        const userReviewFound = data.reviews.find(review => review.user_id === user.id);
        setUserReview(userReviewFound || null);
      } else {
        setUserReview(null);
      }
    } catch (err) {
      console.error('Error fetching reviews:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch reviews');
    } finally {
      setIsLoading(false);
    }
  };

  const createReview = async (reviewData: ReviewCreate): Promise<Review> => {
    if (!token) {
      throw new Error('Authentication required');
    }

    try {
      const newReview: Review = await apiClient.createReview(movieId, reviewData);
      
      // Add the new review to the beginning of the list
      setReviews(prev => [newReview, ...prev]);
      setTotalReviews(prev => prev + 1);
      setUserReview(newReview);

      return newReview;
    } catch (error) {
      throw error;
    }
  };

  const updateReview = async (reviewId: number, reviewData: ReviewUpdate): Promise<Review> => {
    if (!token) {
      throw new Error('Authentication required');
    }

    try {
      const updatedReview: Review = await apiClient.updateReview(reviewId, reviewData);
      
      // Update the review in the list
      setReviews(prev => prev.map(review => 
        review.id === reviewId ? updatedReview : review
      ));
      
      if (userReview?.id === reviewId) {
        setUserReview(updatedReview);
      }

      return updatedReview;
    } catch (error) {
      throw error;
    }
  };

  const deleteReview = async (reviewId: number): Promise<void> => {
    if (!token) {
      throw new Error('Authentication required');
    }

    try {
      await apiClient.deleteReview(reviewId);

      // Remove the review from the list
      setReviews(prev => prev.filter(review => review.id !== reviewId));
      setTotalReviews(prev => prev - 1);
      
      if (userReview?.id === reviewId) {
        setUserReview(null);
      }
    } catch (error) {
      throw error;
    }
  };

  const loadPage = async (pageNum: number) => {
    await fetchReviews(pageNum);
  };

  const refresh = async () => {
    await fetchReviews(currentPage);
  };

  useEffect(() => {
    // Only fetch reviews if movieId is valid and auth context is not loading
    if (movieId && movieId > 0 && !authLoading) {
      fetchReviews(page);
    }
  }, [movieId, page, perPage, authLoading]);

  return {
    reviews,
    totalReviews,
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    isLoading,
    error,
    userReview,
    createReview,
    updateReview,
    deleteReview,
    loadPage,
    refresh,
  };
}