import os
import subprocess
import json
import math
import re
from typing import Dict, List, Tuple, Optional, Callable
from pathlib import Path
import uuid

from app.core.logging import logger
from app.services.minio_service import MinIOService


class VideoProcessingService:
    """Сервис для обработки видеофайлов с помощью FFmpeg"""
    
    def __init__(self, minio_service: MinIOService):
        self.minio_service = minio_service
        
        # Настройки качества для транскодирования
        self.quality_settings = {
            "240p": {
                "resolution": "426x240",
                "bitrate": "400k",
                "audio_bitrate": "64k",
                "preset": "medium",
                "crf": "23"
            },
            "360p": {
                "resolution": "640x360",
                "bitrate": "700k",
                "audio_bitrate": "96k",
                "preset": "medium",
                "crf": "23"
            },
            "480p": {
                "resolution": "854x480",
                "bitrate": "1000k",
                "audio_bitrate": "128k",
                "preset": "medium",
                "crf": "23"
            },
            "720p": {
                "resolution": "1280x720", 
                "bitrate": "2500k",
                "audio_bitrate": "128k",
                "preset": "medium",
                "crf": "23"
            },
            "1080p": {
                "resolution": "1920x1080",
                "bitrate": "5000k", 
                "audio_bitrate": "192k",
                "preset": "medium",
                "crf": "23"
            }
        }
    
    def get_video_info(self, video_path: str) -> Dict:
        """Получает информацию о видеофайле с помощью ffprobe"""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            # Извлекаем основную информацию
            video_stream = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
            audio_stream = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
            
            if not video_stream:
                raise ValueError("No video stream found in file")
            
            return {
                "duration": float(info["format"]["duration"]),
                "size": int(info["format"]["size"]),
                "bitrate": int(info["format"]["bit_rate"]),
                "width": int(video_stream["width"]),
                "height": int(video_stream["height"]),
                "fps": eval(video_stream["r_frame_rate"]),  # Конвертируем дробь в число
                "video_codec": video_stream["codec_name"],
                "audio_codec": audio_stream["codec_name"] if audio_stream else None,
                "format": info["format"]["format_name"]
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error: {e.stderr}")
            raise ValueError(f"Failed to get video info: {e.stderr}")
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            raise e
    
    def parse_ffmpeg_progress(self, line: str, total_duration: float) -> Optional[float]:
        """
        Parse FFmpeg progress from output line
        Returns progress as percentage (0-100)
        """
        # Look for time= output from FFmpeg
        time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})', line)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = int(time_match.group(3))
            centiseconds = int(time_match.group(4))
            
            current_time = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
            progress = (current_time / total_duration) * 100
            return min(progress, 100)
        
        return None

    def run_ffmpeg_with_progress(self, cmd: List[str], total_duration: float, progress_callback: Callable[[float], None]) -> bool:
        """
        Run FFmpeg command with real-time progress monitoring
        """
        try:
            logger.info(f"Running FFmpeg with progress monitoring: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            last_progress = 0
            for line in iter(process.stdout.readline, ''):
                # Parse progress from FFmpeg output
                progress = self.parse_ffmpeg_progress(line, total_duration)
                if progress is not None and progress > last_progress + 1:  # Update every 1%
                    progress_callback(progress)
                    last_progress = progress
                    logger.debug(f"FFmpeg progress: {progress:.1f}%")
            
            process.wait()
            
            if process.returncode == 0:
                progress_callback(100)  # Ensure we reach 100%
                logger.info("FFmpeg completed successfully")
                return True
            else:
                logger.error(f"FFmpeg failed with return code: {process.returncode}")
                return False
                
        except Exception as e:
            logger.error(f"Error running FFmpeg with progress: {str(e)}")
            return False
        """Определяет какие качества нужно создать на основе исходного разрешения"""
        input_height = video_info["height"]
        available_qualities = []
        
        # Добавляем качества не превышающие исходное разрешение
        if input_height >= 480:
            available_qualities.append("480p")
        if input_height >= 720:
            available_qualities.append("720p") 
        if input_height >= 1080:
            available_qualities.append("1080p")
        if input_height >= 2160:
            available_qualities.append("4k")
        
        # Всегда включаем хотя бы одно качество
        if not available_qualities:
            available_qualities.append("480p")
        
        logger.info(f"Input resolution: {video_info['width']}x{input_height}, output qualities: {available_qualities}")
        return available_qualities
    
    def determine_output_qualities(self, video_info: Dict) -> List[str]:
        """Определяет какие качества нужно создать на основе исходного разрешения"""
        input_height = video_info["height"]
        available_qualities = []
        
        # Добавляем качества от исходного разрешения и ниже
        # Порядок: от самого высокого к самому низкому
        if input_height >= 1080:
            available_qualities.extend(["1080p", "720p", "480p", "360p", "240p"])
        elif input_height >= 720:
            available_qualities.extend(["720p", "480p", "360p", "240p"])
        elif input_height >= 480:
            available_qualities.extend(["480p", "360p", "240p"])
        elif input_height >= 360:
            available_qualities.extend(["360p", "240p"])
        else:
            # Для очень низкого разрешения создаем только 240p
            available_qualities.append("240p")
        
        logger.info(f"Input resolution: {video_info['width']}x{input_height}, output qualities: {available_qualities}")
        return available_qualities
    
    def transcode_video(self, input_path: str, output_path: str, quality: str, 
                       video_duration: float = None, progress_callback: Callable[[float], None] = None) -> str:
        """Транскодирует видео в указанное качество с мониторингом прогресса"""
        try:
            settings = self.quality_settings[quality]
            
            # Парсим разрешение
            width, height = settings["resolution"].split("x")
            
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-c:v", "libx264",
                "-preset", settings["preset"],
                "-crf", settings["crf"],
                "-maxrate", settings["bitrate"],
                "-bufsize", str(int(settings["bitrate"].replace("k", "")) * 2) + "k",
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-c:a", "aac",
                "-b:a", settings["audio_bitrate"],
                "-profile:v", "high",  # H.264 High Profile для лучшей совместимости
                "-level", "4.0",  # H.264 Level 4.0
                "-pix_fmt", "yuv420p",  # Pixel format для совместимости
                "-movflags", "+faststart",
                "-progress", "pipe:1",  # Enable progress output
                "-y",  # Перезаписать выходной файл
                output_path
            ]
            
            logger.info(f"Starting transcoding to {quality}: {' '.join(cmd)}")
            
            # Use progress monitoring if callback provided and duration known
            if progress_callback and video_duration:
                success = self.run_ffmpeg_with_progress(cmd, video_duration, progress_callback)
                if not success:
                    raise ValueError("FFmpeg transcoding failed")
            else:
                # Fallback to original method
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if not os.path.exists(output_path):
                raise ValueError(f"Transcoded file not created: {output_path}")
            
            # Проверяем выходной файл
            output_info = self.get_video_info(output_path)
            logger.info(f"Transcoded file info: codec={output_info.get('video_codec')}, resolution={output_info.get('width')}x{output_info.get('height')}")
            
            logger.info(f"Successfully transcoded video to {quality}: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg transcoding error: {e.stderr}")
            raise ValueError(f"Transcoding failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Error transcoding video: {str(e)}")
            raise e
    
    def create_hls_segments(self, input_path: str, output_dir: str, quality: str) -> str:
        """Создает HLS сегменты из видеофайла"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            playlist_path = os.path.join(output_dir, "playlist.m3u8")
            segment_pattern = os.path.join(output_dir, "segment_%03d.ts")
            
            # Проверяем входной файл перед созданием сегментов
            logger.info(f"Checking input file before HLS segmentation: {input_path}")
            input_info = self.get_video_info(input_path)
            logger.info(f"Input file info: codec={input_info.get('video_codec')}, resolution={input_info.get('width')}x{input_info.get('height')}")
            
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-c:v", "copy",  # Копируем видео без перекодирования
                "-c:a", "copy",  # Копируем аудио без перекодирования
                "-bsf:v", "h264_mp4toannexb",  # Конвертируем H.264 в формат Annex B для TS
                "-start_number", "0",  # Начинаем нумерацию с 0
                "-hls_time", "10",  # 10-секундные сегменты
                "-hls_list_size", "0",  # Включить все сегменты в playlist
                "-hls_segment_filename", segment_pattern,
                "-hls_flags", "independent_segments",  # Каждый сегмент независим
                "-avoid_negative_ts", "make_zero",  # Исправляем отрицательные timestamps
                "-f", "hls",
                "-y",
                playlist_path
            ]
            
            logger.info(f"Creating HLS segments for {quality}: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if not os.path.exists(playlist_path):
                raise ValueError(f"HLS playlist not created: {playlist_path}")
            
            # Проверяем созданные сегменты
            segments = [f for f in os.listdir(output_dir) if f.endswith('.ts')]
            logger.info(f"Successfully created HLS segments for {quality}: {len(segments)} segments")
            
            # Проверяем первый сегмент на наличие видео и аудио дорожек
            if segments:
                first_segment = os.path.join(output_dir, segments[0])
                try:
                    segment_info = self.get_video_info(first_segment)
                    logger.info(f"First segment info: video_codec={segment_info.get('video_codec')}, audio_codec={segment_info.get('audio_codec')}")
                    if not segment_info.get('video_codec'):
                        logger.error(f"WARNING: First segment has no video track!")
                except Exception as e:
                    logger.warning(f"Could not verify segment info: {e}")
            
            return playlist_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg HLS error: {e.stderr}")
            raise ValueError(f"HLS creation failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Error creating HLS segments: {str(e)}")
            raise e
    
    async def upload_hls_files(self, hls_dir: str, video_file_id: str, quality: str, minio_service: MinIOService) -> Dict:
        """Загружает HLS файлы в MinIO"""
        try:
            uploaded_files = {}
            
            # Загружаем playlist
            playlist_path = os.path.join(hls_dir, "playlist.m3u8")
            if os.path.exists(playlist_path):
                object_name = f"processed-videos/{video_file_id}/{quality}/playlist.m3u8"
                await minio_service.upload_file("videos", object_name, playlist_path)
                uploaded_files["playlist"] = object_name
            
            # Загружаем сегменты
            segments = []
            for file in os.listdir(hls_dir):
                if file.endswith(".ts"):
                    segment_path = os.path.join(hls_dir, file)
                    object_name = f"processed-videos/{video_file_id}/{quality}/{file}"
                    await minio_service.upload_file("videos", object_name, segment_path)
                    segments.append(object_name)
            
            uploaded_files["segments"] = segments
            
            logger.info(f"Uploaded {len(segments)} HLS segments for {quality}")
            return uploaded_files
            
        except Exception as e:
            logger.error(f"Error uploading HLS files: {str(e)}")
            raise e
    
    def generate_thumbnails(self, video_path: str, duration: float, interval: int = 10, 
                          progress_callback: Callable[[float], None] = None) -> List[str]:
        """Генерирует превью изображения из видео с мониторингом прогресса"""
        try:
            thumbnails = []
            temp_dir = os.path.dirname(video_path)
            
            # Генерируем превью каждые interval секунд
            timestamps = list(range(0, int(duration), interval))
            total_thumbnails = len(timestamps)
            
            for i, timestamp in enumerate(timestamps):
                thumbnail_path = os.path.join(temp_dir, f"thumbnail_{timestamp}.jpg")
                
                cmd = [
                    "ffmpeg",
                    "-i", video_path,
                    "-ss", str(timestamp),
                    "-vframes", "1",
                    "-vf", "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2",
                    "-q:v", "2",  # Высокое качество JPEG
                    "-y",
                    thumbnail_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                if os.path.exists(thumbnail_path):
                    thumbnails.append(thumbnail_path)
                
                # Update progress if callback provided
                if progress_callback:
                    progress = ((i + 1) / total_thumbnails) * 100
                    progress_callback(progress)
            
            logger.info(f"Generated {len(thumbnails)} thumbnails")
            return thumbnails
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg thumbnail error: {e.stderr}")
            raise ValueError(f"Thumbnail generation failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Error generating thumbnails: {str(e)}")
            raise e
    
    def create_master_playlist(self, processed_files: Dict) -> str:
        """Создает master HLS playlist для всех качеств"""
        try:
            playlist_lines = ["#EXTM3U", "#EXT-X-VERSION:3", ""]
            
            # Настройки для каждого качества
            quality_info = {
                "240p": {"bandwidth": 400000, "resolution": "426x240"},
                "360p": {"bandwidth": 700000, "resolution": "640x360"},
                "480p": {"bandwidth": 1000000, "resolution": "854x480"},
                "720p": {"bandwidth": 2500000, "resolution": "1280x720"},
                "1080p": {"bandwidth": 5000000, "resolution": "1920x1080"}
            }
            
            # Сортируем качества по битрейту (от низкого к высокому)
            sorted_qualities = sorted(processed_files.keys(), 
                                    key=lambda q: quality_info.get(q, {}).get("bandwidth", 0))
            
            for quality in sorted_qualities:
                if quality in quality_info:
                    info = quality_info[quality]
                    playlist_lines.extend([
                        f"#EXT-X-STREAM-INF:BANDWIDTH={info['bandwidth']},RESOLUTION={info['resolution']}",
                        f"{quality}/playlist.m3u8",
                        ""
                    ])
            
            master_playlist = "\n".join(playlist_lines)
            logger.info(f"Created master playlist with qualities: {sorted_qualities}")
            
            return master_playlist
            
        except Exception as e:
            logger.error(f"Error creating master playlist: {str(e)}")
            raise e
    
    def validate_video_file(self, file_path: str) -> bool:
        """Валидирует видеофайл"""
        try:
            # Проверяем что файл существует
            if not os.path.exists(file_path):
                return False
            
            # Проверяем что можем получить информацию о видео
            video_info = self.get_video_info(file_path)
            
            # Базовые проверки
            if video_info["duration"] <= 0:
                logger.error("Video duration is zero or negative")
                return False
            
            if video_info["width"] <= 0 or video_info["height"] <= 0:
                logger.error("Invalid video dimensions")
                return False
            
            # Проверяем максимальную длительность (например, 4 часа)
            if video_info["duration"] > 14400:  # 4 часа в секундах
                logger.error("Video is too long (max 4 hours)")
                return False
            
            # Проверяем минимальное разрешение
            if video_info["width"] < 320 or video_info["height"] < 240:
                logger.error("Video resolution is too low (min 320x240)")
                return False
            
            logger.info(f"Video validation passed: {video_info}")
            return True
            
        except Exception as e:
            logger.error(f"Video validation failed: {str(e)}")
            return False