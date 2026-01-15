'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Upload, X, CheckCircle, AlertCircle, Clock, Film, Search, ChevronLeft, ChevronRight } from 'lucide-react';

interface Movie {
  id: number;
  title: string;
  year: number;
  video_file_id?: string;
  processing_status?: 'pending' | 'processing' | 'completed' | 'failed';
  available_qualities?: string[];
  duration_seconds?: number;
  hls_manifest_url?: string;
}

interface UploadTask {
  id: string;
  movieId: number;
  movieTitle: string;
  file: File;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  error?: string;
}

interface VideoUploadPanelProps {
  movies: Movie[];
  onMoviesUpdate: () => void;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const ITEMS_PER_PAGE = 10;

export default function VideoUploadPanel({ movies, onMoviesUpdate }: VideoUploadPanelProps) {
  const [uploadTasks, setUploadTasks] = useState<UploadTask[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [moviesData, setMoviesData] = useState<{
    movies: Movie[];
    total: number;
    loading: boolean;
  }>({
    movies: [],
    total: 0,
    loading: false
  });
  const fileInputRefs = useRef<{ [key: number]: HTMLInputElement | null }>({});

  // Fetch movies with search and pagination
  const fetchMovies = async (search: string = '', page: number = 1) => {
    setMoviesData(prev => ({ ...prev, loading: true }));
    
    try {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('No token found');

      const params = new URLSearchParams({
        page: page.toString(),
        limit: ITEMS_PER_PAGE.toString()
      });
      
      // Always show all movies, allow overwriting
      if (search.trim()) {
        params.append('search', search.trim());
      }

      const response = await fetch(`${API_BASE_URL}/api/admin/movies/video-status?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch movies: ${response.status}`);
      }

      const data = await response.json();
      setMoviesData({
        movies: data.movies,
        total: data.total,
        loading: false
      });
    } catch (error) {
      console.error('Error fetching movies:', error);
      setMoviesData(prev => ({ ...prev, loading: false }));
    }
  };

  // Fetch movies when component mounts or search/page changes
  useEffect(() => {
    fetchMovies(searchQuery, currentPage);
  }, [searchQuery, currentPage]);

  // Reset page when search changes
  useEffect(() => {
    if (currentPage !== 1) {
      setCurrentPage(1);
    }
  }, [searchQuery]);

  // Use API data for all movies (can overwrite existing videos)
  const allMovies = moviesData.movies;
  const totalPages = Math.ceil(moviesData.total / ITEMS_PER_PAGE);

  const handleFileSelect = (files: FileList | null, movie: Movie) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    
    // Validate file type
    if (!file.type.startsWith('video/')) {
      alert('Please select a video file');
      return;
    }

    // Validate file size (max 10GB)
    const maxSize = 10 * 1024 * 1024 * 1024;
    if (file.size > maxSize) {
      alert('File size must be less than 10GB');
      return;
    }

    uploadVideo(movie, file);
  };

  const uploadVideo = async (movie: Movie, file: File) => {
    const taskId = `${movie.id}-${Date.now()}`;
    const newTask: UploadTask = {
      id: taskId,
      movieId: movie.id,
      movieTitle: movie.title,
      file,
      status: 'uploading',
      progress: 0
    };

    setUploadTasks(prev => [...prev, newTask]);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/api/admin/movies/${movie.id}/upload-video`, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Upload failed: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      
      // Update task status
      setUploadTasks(prev => prev.map(task => 
        task.id === taskId 
          ? { ...task, status: 'processing', progress: 100 }
          : task
      ));

      // Poll for processing status
      if (result.task_id) {
        pollProcessingStatus(taskId, result.task_id);
      }

    } catch (error) {
      console.error('Upload error:', error);
      setUploadTasks(prev => prev.map(task => 
        task.id === taskId 
          ? { ...task, status: 'failed', error: error instanceof Error ? error.message : 'Upload failed' }
          : task
      ));
    }
  };

  const pollProcessingStatus = async (taskId: string, processingTaskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/admin/upload/status/${processingTaskId}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to get status');
        }

        const status = await response.json();

        if (status.status === 'completed') {
          setUploadTasks(prev => prev.map(task => 
            task.id === taskId 
              ? { ...task, status: 'completed' }
              : task
          ));
          clearInterval(pollInterval);
          onMoviesUpdate();
          // Refresh the current movies list
          fetchMovies(searchQuery, currentPage);
        } else if (status.status === 'failed') {
          setUploadTasks(prev => prev.map(task => 
            task.id === taskId 
              ? { ...task, status: 'failed', error: status.error || 'Processing failed' }
              : task
          ));
          clearInterval(pollInterval);
        } else if (status.status === 'processing') {
          setUploadTasks(prev => prev.map(task => 
            task.id === taskId 
              ? { 
                  ...task, 
                  progress: status.progress || 0,
                  error: status.message || `Processing... ${status.progress || 0}%`
                }
              : task
          ));
        }
      } catch (error) {
        console.error('Status polling error:', error);
        clearInterval(pollInterval);
      }
    }, 2000);

    // Stop polling after 30 minutes
    setTimeout(() => clearInterval(pollInterval), 30 * 60 * 1000);
  };

  const removeTask = (taskId: string) => {
    setUploadTasks(prev => prev.filter(task => task.id !== taskId));
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-yellow-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['Байт', 'КБ', 'МБ', 'ГБ'];
    if (bytes === 0) return '0 Байт';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const triggerFileInput = (movieId: number) => {
    const input = fileInputRefs.current[movieId];
    if (input) {
      input.click();
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Tasks */}
      {uploadTasks.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Прогресс загрузки
          </h3>
          <div className="space-y-4">
            {uploadTasks.map((task) => (
              <div key={task.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(task.status)}
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {task.movieTitle}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {task.file.name} ({formatFileSize(task.file.size)})
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeTask(task.id)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                
                {task.status === 'uploading' || task.status === 'processing' ? (
                  <>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${task.progress}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">
                        {task.error || `${task.status === 'uploading' ? 'Загрузка' : 'Обработка'}...`}
                      </span>
                      <span className="font-semibold text-blue-600 dark:text-blue-400">
                        {task.progress}%
                      </span>
                    </div>
                  </>
                ) : task.status === 'failed' && task.error ? (
                  <p className="text-sm text-red-600 dark:text-red-400">{task.error}</p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Movies - Upload/Replace Video */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Все фильмы ({moviesData.total})
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Загрузите или замените видеофайлы
              </p>
            </div>
            
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск фильмов..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full sm:w-64"
              />
            </div>
          </div>
        </div>
        
        <div className="p-6">
          {moviesData.loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-3 text-gray-600">Загрузка фильмов...</span>
            </div>
          ) : allMovies.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">
              {searchQuery ? 'Фильмы не найдены' : 'Нет доступных фильмов'}
            </p>
          ) : (
            <>
              <div className="space-y-4">
                {allMovies.map((movie) => (
                  <div 
                    key={movie.id}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <Film className="w-8 h-8 text-gray-400" />
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white">
                            {movie.title} ({movie.year})
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            ID: {movie.id} • {movie.video_file_id ? `Видео: ${movie.processing_status || 'загружено'}` : 'Видео не загружено'}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {/* Hidden file input for each movie */}
                        <input
                          ref={(el) => { fileInputRefs.current[movie.id] = el; }}
                          type="file"
                          accept="video/*"
                          onChange={(e) => handleFileSelect(e.target.files, movie)}
                          className="hidden"
                        />
                        <button
                          onClick={() => triggerFileInput(movie.id)}
                          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          <Upload className="w-4 h-4" />
                          <span>{movie.video_file_id ? 'Заменить видео' : 'Загрузить видео'}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Показано {((currentPage - 1) * ITEMS_PER_PAGE) + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, moviesData.total)} из {moviesData.total} фильмов
                  </p>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Страница {currentPage} из {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
