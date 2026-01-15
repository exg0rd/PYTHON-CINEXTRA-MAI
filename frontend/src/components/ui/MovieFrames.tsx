'use client';

import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Film } from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Thumbnail {
  timestamp: number;
  url: string;
}

interface MovieFramesProps {
  movieId: number;
  movieTitle: string;
  durationSeconds?: number;
}

export default function MovieFrames({ movieId, movieTitle, durationSeconds }: MovieFramesProps) {
  const [thumbnails, setThumbnails] = useState<Thumbnail[]>([]);
  const [selectedFrames, setSelectedFrames] = useState<Thumbnail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scrollPosition, setScrollPosition] = useState(0);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  useEffect(() => {
    fetchThumbnails();
  }, [movieId]);

  const fetchThumbnails = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/stream/${movieId}/thumbnails`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch thumbnails');
      }

      const data = await response.json();
      setThumbnails(data.thumbnails || []);
      
      if (data.thumbnails && data.thumbnails.length > 0) {
        const frames = selectEvenlyDistributedFrames(data.thumbnails, 6);
        setSelectedFrames(frames);
      }
    } catch (err) {
      console.error('Error fetching thumbnails:', err);
      setError('Не удалось загрузить кадры');
    } finally {
      setLoading(false);
    }
  };

  const selectEvenlyDistributedFrames = (allThumbnails: Thumbnail[], count: number): Thumbnail[] => {
    if (allThumbnails.length === 0) return [];
    
    const filteredThumbnails = allThumbnails.filter(t => t.timestamp > 0);
    
    if (filteredThumbnails.length === 0) return [];
    if (filteredThumbnails.length <= count) return filteredThumbnails;

    const frames: Thumbnail[] = [];
    const step = Math.floor(filteredThumbnails.length / count);
    
    for (let i = 0; i < count; i++) {
      const index = Math.min(i * step, filteredThumbnails.length - 1);
      frames.push(filteredThumbnails[index]);
    }
    
    return frames;
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const scroll = (direction: 'left' | 'right') => {
    const container = document.getElementById('frames-container');
    if (!container) return;

    const scrollAmount = 300;
    const newPosition = direction === 'left' 
      ? Math.max(0, scrollPosition - scrollAmount)
      : Math.min(container.scrollWidth - container.clientWidth, scrollPosition + scrollAmount);

    container.scrollTo({ left: newPosition, behavior: 'smooth' });
    setScrollPosition(newPosition);
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden border border-gray-100 dark:border-gray-700 p-6">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-gray-600 dark:text-gray-400">Загрузка кадров...</span>
        </div>
      </div>
    );
  }

  if (error || selectedFrames.length === 0) {
    return null;
  }

  return (
    <>
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden border border-gray-100 dark:border-gray-700">
        <div className="p-6 lg:p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
              <Film className="w-6 h-6 mr-2 text-blue-600" />
              Кадры из фильма
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => scroll('left')}
                disabled={scrollPosition === 0}
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                aria-label="Прокрутить влево"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={() => scroll('right')}
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                aria-label="Прокрутить вправо"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div 
            id="frames-container"
            className="flex gap-4 overflow-x-auto scrollbar-hide scroll-smooth"
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            {selectedFrames.map((frame, index) => (
              <div
                key={frame.timestamp}
                className="flex-shrink-0 group cursor-pointer"
                onClick={() => setSelectedImage(`${API_BASE_URL}${frame.url}`)}
              >
                <div className="relative w-64 h-36 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden shadow-md hover:shadow-xl transition-all duration-300 transform hover:scale-105">
                  <img
                    src={`${API_BASE_URL}${frame.url}`}
                    alt={`Кадр из ${movieTitle} в ${formatTime(frame.timestamp)}`}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="absolute bottom-2 left-2 right-2">
                      <div className="bg-black/80 backdrop-blur-sm rounded px-2 py-1 text-xs text-white font-medium">
                        {formatTime(frame.timestamp)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Модальное окно для просмотра кадра в полном размере */}
      {selectedImage && (
        <div
          className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-0"
          onClick={() => setSelectedImage(null)}
        >
          <button
            onClick={() => setSelectedImage(null)}
            className="absolute top-4 right-4 z-10 p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors backdrop-blur-sm"
            aria-label="Закрыть"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <img
            src={selectedImage}
            alt="Кадр из фильма"
            className="w-full h-full object-contain"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}

      <style jsx>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </>
  );
}
