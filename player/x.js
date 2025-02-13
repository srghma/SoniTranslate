import React, { useEffect, useRef, useState } from 'react';
import '@media-chrome/react/dist/index.css';
import {
  MediaController,
  MediaProvider,
  MediaControlBar,
  MediaTimeRange,
  MediaTimeDisplay,
  MediaVolumeRange,
  MediaPlayButton,
  MediaMuteButton,
  MediaQualityButton,
  MediaCaptionsButton
} from '@media-chrome/react';

const VideoPlayer = ({ config }) => {
  const videoRef = useRef(null);
  const audioRef = useRef(null);
  const [currentQuality, setCurrentQuality] = useState(config.videos[0]);
  const [isExternalAudioActive, setIsExternalAudioActive] = useState(false);

  useEffect(() => {
    if (!videoRef.current) return;

    // Set up video source
    videoRef.current.src = currentQuality.sources[0];

    // Add subtitle tracks
    config.subtitles.forEach(subtitle => {
      const track = document.createElement('track');
      track.kind = 'subtitles';
      track.label = subtitle.name;
      track.srclang = subtitle.name.toLowerCase();
      track.src = subtitle.src;
      videoRef.current.appendChild(track);
    });

    // Handle external audio sync
    if (audioRef.current) {
      const syncAudioWithVideo = () => {
        if (Math.abs(audioRef.current.currentTime - videoRef.current.currentTime) > 0.1) {
          audioRef.current.currentTime = videoRef.current.currentTime;
        }
      };

      videoRef.current.addEventListener('play', () => {
        if (isExternalAudioActive) {
          audioRef.current.play();
        }
      });

      videoRef.current.addEventListener('pause', () => {
        if (isExternalAudioActive) {
          audioRef.current.pause();
        }
      });

      videoRef.current.addEventListener('timeupdate', syncAudioWithVideo);

      return () => {
        videoRef.current?.removeEventListener('timeupdate', syncAudioWithVideo);
      };
    }
  }, [currentQuality, isExternalAudioActive]);

  const handleQualityChange = (quality) => {
    const currentTime = videoRef.current.currentTime;
    setCurrentQuality(quality);
    // Preserve playback position when changing quality
    requestAnimationFrame(() => {
      videoRef.current.currentTime = currentTime;
    });
  };

  const handleAudioTrackChange = (isExternal) => {
    setIsExternalAudioActive(isExternal);
    if (isExternal) {
      videoRef.current.muted = true;
      audioRef.current.currentTime = videoRef.current.currentTime;
      if (!videoRef.current.paused) {
        audioRef.current.play();
      }
    } else {
      videoRef.current.muted = false;
      audioRef.current.pause();
    }
  };

  return (
    <div className="w-full max-w-4xl">
      <MediaController>
        <MediaProvider>
          <video
            ref={videoRef}
            className="w-full"
            crossOrigin="anonymous"
            playsInline
          />
          {config.additionalAudio && (
            <audio
              ref={audioRef}
              src={config.additionalAudio.src}
              className="hidden"
            />
          )}
        </MediaProvider>

        <MediaControlBar>
          <MediaPlayButton />
          <MediaTimeRange />
          <MediaTimeDisplay />
          <MediaMuteButton />
          <MediaVolumeRange />

          {/* Quality Selection */}
          <MediaQualityButton>
            <select
              className="bg-transparent border-none outline-none"
              value={currentQuality.name}
              onChange={(e) => {
                const quality = config.videos.find(v => v.name === e.target.value);
                if (quality) handleQualityChange(quality);
              }}
            >
              {config.videos.map(video => (
                <option key={video.name} value={video.name}>
                  {video.name}
                </option>
              ))}
            </select>
          </MediaQualityButton>

          {/* Audio Track Selection */}
          {config.additionalAudio && (
            <select
              className="bg-transparent border-none outline-none ml-2"
              value={isExternalAudioActive ? config.additionalAudio.name : 'default'}
              onChange={(e) => handleAudioTrackChange(e.target.value !== 'default')}
            >
              <option value="default">English</option>
              <option value={config.additionalAudio.name}>
                {config.additionalAudio.name}
              </option>
            </select>
          )}

          <MediaCaptionsButton />
        </MediaControlBar>
      </MediaController>
    </div>
  );
};

export default VideoPlayer;
