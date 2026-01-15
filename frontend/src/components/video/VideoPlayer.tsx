'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, Settings, SkipBack, SkipForward } from 'lucide-react';

// Динамический импорт HLS.js для избежания проблем с SSR
let Hls: any = null;
if (typeof window !== 'undefined') {
  import('hls.js').then((module) => {
    Hls = module.default;
  });
}

interface Subtitle {
  language: string;
  label: string;
  url: string;
}

interface AudioTrack {
  language: string;
  label: string;
  default?: boolean;
}

interface VideoPlayerProps {
  src: string;
  poster?: string;
  subtitles?: Subtitle[];
  audioTracks?: AudioTrack[];
  onTimeUpdate?: (currentTime: number, duration: number) => void;
  onQualityChange?: (quality: string) => void;
  className?: string;
}

export default function VideoPlayer({
  src,
  poster,
  subtitles = [],
  audioTracks = [],
  onTimeUpdate,
  onQualityChange,
  className = ''
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [availableQualities, setAvailableQualities] = useState<string[]>([]);
  const [currentQuality, setCurrentQuality] = useState<string>('auto');
  const [currentSubtitle, setCurrentSubtitle] = useState<string>('off');
  const [currentAudioTrack, setCurrentAudioTrack] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Hide controls after inactivity
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const resetControlsTimeout = useCallback(() => {
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    setShowControls(true);
    controlsTimeoutRef.current = setTimeout(() => {
      if (isPlaying) {
        setShowControls(false);
      }
    }, 3000);
  }, [isPlaying]);

  // Initialize HLS player
  useEffect(() => {
    if (!videoRef.current || !src) return;

    const video = videoRef.current;
    
    // Ждем загрузки HLS.js если еще не загружен
    const initializePlayer = async () => {
      if (!Hls) {
        try {
          const hlsModule = await import('hls.js');
          Hls = hlsModule.default;
        } catch (error) {
          console.error('Failed to load HLS.js:', error);
          setError('HLS player not available');
          setIsLoading(false);
          return;
        }
      }

      if (Hls && Hls.isSupported()) {
        const hls = new Hls({
          enableWorker: true,
          lowLatencyMode: true,
          backBufferLength: 90
        });
        
        hlsRef.current = hls;
        
        hls.loadSource(src);
        hls.attachMedia(video);
        
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          setIsLoading(false);
          
          // Get available quality levels
          const levels = hls.levels.map((level: any, index: number) => {
            const height = level.height;
            if (height >= 2160) return '4K';
            if (height >= 1080) return '1080p';
            if (height >= 720) return '720p';
            if (height >= 480) return '480p';
            return `${height}p`;
          });
          
          setAvailableQualities(['auto', ...levels]);
        });
        
        hls.on(Hls.Events.ERROR, (event: any, data: any) => {
          // Only handle fatal errors
          if (data.fatal) {
            console.error('HLS fatal error:', data);
            
            switch (data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                console.error('Fatal network error encountered');
                setError('Network error loading video');
                setIsLoading(false);
                break;
              case Hls.ErrorTypes.MEDIA_ERROR:
                console.error('Fatal media error encountered, trying to recover');
                hls.recoverMediaError();
                break;
              default:
                console.error('Fatal error, cannot recover');
                setError('Failed to load video');
                setIsLoading(false);
                break;
            }
          }
          // Silently ignore non-fatal errors (they are handled internally by HLS.js)
        });
        
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // Native HLS support (Safari)
        video.src = src;
        setIsLoading(false);
      } else {
        setError('HLS not supported in this browser');
        setIsLoading(false);
      }
    };

    initializePlayer();

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
  }, [src]);

  // Video event handlers
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      const current = video.currentTime;
      const total = video.duration;
      setCurrentTime(current);
      setDuration(total);
      onTimeUpdate?.(current, total);
    };

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleVolumeChange = () => {
      setVolume(video.volume);
      setIsMuted(video.muted);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('volumechange', handleVolumeChange);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('volumechange', handleVolumeChange);
    };
  }, [onTimeUpdate]);

  // Fullscreen handling
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!videoRef.current) return;

      switch (e.code) {
        case 'Space':
          e.preventDefault();
          togglePlay();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          seek(currentTime - 10);
          break;
        case 'ArrowRight':
          e.preventDefault();
          seek(currentTime + 10);
          break;
        case 'ArrowUp':
          e.preventDefault();
          setVolumeLevel(Math.min(1, volume + 0.1));
          break;
        case 'ArrowDown':
          e.preventDefault();
          setVolumeLevel(Math.max(0, volume - 0.1));
          break;
        case 'KeyM':
          e.preventDefault();
          toggleMute();
          break;
        case 'KeyF':
          e.preventDefault();
          toggleFullscreen();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [currentTime, volume]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !videoRef.current.muted;
  };

  const setVolumeLevel = (newVolume: number) => {
    if (!videoRef.current) return;
    videoRef.current.volume = newVolume;
  };

  const seek = (time: number) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = Math.max(0, Math.min(duration, time));
  };

  const toggleFullscreen = async () => {
    if (!containerRef.current) return;

    try {
      if (isFullscreen) {
        await document.exitFullscreen();
      } else {
        await containerRef.current.requestFullscreen();
      }
    } catch (error) {
      console.error('Fullscreen error:', error);
    }
  };

  const changeQuality = (quality: string) => {
    if (!hlsRef.current || !Hls) return;

    if (quality === 'auto') {
      hlsRef.current.currentLevel = -1;
    } else {
      const levelIndex = hlsRef.current.levels.findIndex((level: any) => {
        const height = level.height;
        const qualityHeight = quality === '4K' ? 2160 : parseInt(quality);
        return height === qualityHeight;
      });
      
      if (levelIndex !== -1) {
        hlsRef.current.currentLevel = levelIndex;
      }
    }
    
    setCurrentQuality(quality);
    onQualityChange?.(quality);
    setShowSettings(false);
  };

  const changeSubtitle = (subtitleLang: string) => {
    setCurrentSubtitle(subtitleLang);
    
    // Remove existing subtitle tracks
    const tracks = videoRef.current?.textTracks;
    if (tracks) {
      for (let i = 0; i < tracks.length; i++) {
        tracks[i].mode = 'disabled';
      }
    }
    
    if (subtitleLang !== 'off') {
      // Add new subtitle track
      const subtitle = subtitles.find(sub => sub.language === subtitleLang);
      if (subtitle && videoRef.current) {
        const track = videoRef.current.addTextTrack('subtitles', subtitle.label, subtitle.language);
        track.mode = 'showing';
        
        // Load subtitle file (WebVTT format)
        fetch(subtitle.url)
          .then(response => response.text())
          .then(vttContent => {
            // Parse and add cues (simplified implementation)
            // In production, use a proper WebVTT parser
            console.log('Loaded subtitles:', vttContent);
          })
          .catch(error => console.error('Failed to load subtitles:', error));
      }
    }
    
    setShowSettings(false);
  };

  const formatTime = (time: number) => {
    const hours = Math.floor(time / 3600);
    const minutes = Math.floor((time % 3600) / 60);
    const seconds = Math.floor(time % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (error) {
    return (
      <div className={`bg-black flex items-center justify-center text-white ${className}`}>
        <div className="text-center">
          <p className="text-lg mb-2">Error loading video</p>
          <p className="text-sm text-gray-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={`relative bg-black group ${className}`}
      onMouseMove={resetControlsTimeout}
      onMouseLeave={() => setShowControls(false)}
    >
      <video
        ref={videoRef}
        className="w-full h-full"
        poster={poster}
        onClick={togglePlay}
        playsInline
      />
      
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
        </div>
      )}

      {/* Controls overlay */}
      <div className={`absolute inset-0 transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0'}`}>
        {/* Play/Pause button in center */}
        <div className="absolute inset-0 flex items-center justify-center">
          <button
            onClick={togglePlay}
            className="bg-black bg-opacity-50 rounded-full p-4 text-white hover:bg-opacity-70 transition-all"
          >
            {isPlaying ? <Pause size={32} /> : <Play size={32} />}
          </button>
        </div>

        {/* Bottom controls */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4">
          {/* Progress bar */}
          <div className="mb-4">
            <input
              type="range"
              min="0"
              max={duration || 0}
              value={currentTime}
              onChange={(e) => seek(parseFloat(e.target.value))}
              className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
            />
          </div>

          {/* Control buttons */}
          <div className="flex items-center justify-between text-white">
            <div className="flex items-center space-x-4">
              <button onClick={togglePlay} className="hover:text-gray-300">
                {isPlaying ? <Pause size={20} /> : <Play size={20} />}
              </button>
              
              <button onClick={() => seek(currentTime - 10)} className="hover:text-gray-300">
                <SkipBack size={20} />
              </button>
              
              <button onClick={() => seek(currentTime + 10)} className="hover:text-gray-300">
                <SkipForward size={20} />
              </button>

              <div className="flex items-center space-x-2">
                <button onClick={toggleMute} className="hover:text-gray-300">
                  {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
                </button>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={isMuted ? 0 : volume}
                  onChange={(e) => setVolumeLevel(parseFloat(e.target.value))}
                  className="w-20 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              <span className="text-sm">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>

            <div className="flex items-center space-x-4">
              <div className="relative">
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="hover:text-gray-300"
                >
                  <Settings size={20} />
                </button>

                {showSettings && (
                  <div className="absolute bottom-8 right-0 bg-black bg-opacity-90 rounded-lg p-4 min-w-48">
                    {/* Quality settings */}
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold mb-2">Quality</h4>
                      {availableQualities.map((quality) => (
                        <button
                          key={quality}
                          onClick={() => changeQuality(quality)}
                          className={`block w-full text-left px-2 py-1 text-sm hover:bg-gray-700 rounded ${
                            currentQuality === quality ? 'text-blue-400' : ''
                          }`}
                        >
                          {quality}
                        </button>
                      ))}
                    </div>

                    {/* Subtitles */}
                    {subtitles.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-sm font-semibold mb-2">Subtitles</h4>
                        <button
                          onClick={() => changeSubtitle('off')}
                          className={`block w-full text-left px-2 py-1 text-sm hover:bg-gray-700 rounded ${
                            currentSubtitle === 'off' ? 'text-blue-400' : ''
                          }`}
                        >
                          Off
                        </button>
                        {subtitles.map((subtitle) => (
                          <button
                            key={subtitle.language}
                            onClick={() => changeSubtitle(subtitle.language)}
                            className={`block w-full text-left px-2 py-1 text-sm hover:bg-gray-700 rounded ${
                              currentSubtitle === subtitle.language ? 'text-blue-400' : ''
                            }`}
                          >
                            {subtitle.label}
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Audio tracks */}
                    {audioTracks.length > 1 && (
                      <div>
                        <h4 className="text-sm font-semibold mb-2">Audio</h4>
                        {audioTracks.map((track) => (
                          <button
                            key={track.language}
                            onClick={() => setCurrentAudioTrack(track.language)}
                            className={`block w-full text-left px-2 py-1 text-sm hover:bg-gray-700 rounded ${
                              currentAudioTrack === track.language ? 'text-blue-400' : ''
                            }`}
                          >
                            {track.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <button onClick={toggleFullscreen} className="hover:text-gray-300">
                <Maximize size={20} />
              </button>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          height: 12px;
          width: 12px;
          border-radius: 50%;
          background: #ffffff;
          cursor: pointer;
        }
        
        .slider::-moz-range-thumb {
          height: 12px;
          width: 12px;
          border-radius: 50%;
          background: #ffffff;
          cursor: pointer;
          border: none;
        }
      `}</style>
    </div>
  );
}