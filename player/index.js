const sources = {
  "[360p]": [
    "https://femeretes.org/2a0c3a92f845dc700dced4dc9b8e6442:2025021012:NGZZQVU2ZnMydUJTbitwbExIT1hML09xaERvTzZobmNJckhmdkFqM2pnN1FXRUtTU0VseXhLODVoZ2hkYVNjWndqMWthbXpydFdzb29CUWtONDU1MTJLRDc3VFJIbHJjWWQ0QmRNUVQ0WVU9/7/2/8/4/8/l9rny.mp4:hls:manifest.m3u8",
    "https://stream.voidboost.cc/2a0c3a92f845dc700dced4dc9b8e6442:2025021012:NGZZQVU2ZnMydUJTbitwbExIT1hML09xaERvTzZobmNJckhmdkFqM2pnN1FXRUtTU0VseXhLODVoZ2hkYVNjWndqMWthbXpydFdzb29CUWtONDU1MTJLRDc3VFJIbHJjWWQ0QmRNUVQ0WVU9/7/2/8/4/8/l9rny.mp4:hls:manifest.m3u8"
  ],
  "[480p]": [
    "https://femeretes.org/6260d7e0440660f6686671782116574f:2025021012:NGZZQVU2ZnMydUJTbitwbExIT1hML09xaERvTzZobmNJckhmdkFqM2pnN1FXRUtTU0VseXhLODVoZ2hkYVNjWndqMWthbXpydFdzb29CUWtONDU1MTJLRDc3VFJIbHJjWWQ0QmRNUVQ0WVU9/7/2/8/4/8/67335.mp4:hls:manifest.m3u8",
    "https://stream.voidboost.cc/6260d7e0440660f6686671782116574f:2025021012:NGZZQVU2ZnMydUJTbitwbExIT1hML09xaERvTzZobmNJckhmdkFqM2pnN1FXRUtTU0VseXhLODVoZ2hkYVNjWndqMWthbXpydFdzb29CUWtONDU1MTJLRDc3VFJIbHJjWWQ0QmRNUVQ0WVU9/7/2/8/4/8/67335.mp4:hls:manifest.m3u8"
  ],
  "[720p]": [
    "https://femeretes.org/f13bc1849fb6348c48c12c6bf329b4e4:2025021012:NGZZQVU2ZnMydUJTbitwbExIT1hML09xaERvTzZobmNJckhmdkFqM2pnN1FXRUtTU0VseXhLODVoZ2hkYVNjWndqMWthbXpydFdzb29CUWtONDU1MTJLRDc3VFJIbHJjWWQ0QmRNUVQ0WVU9/7/2/8/4/8/ilqwo.mp4:hls:manifest.m3u8",
    "https://stream.voidboost.cc/f13bc1849fb6348c48c12c6bf329b4e4:2025021012:NGZZQVU2ZnMydUJTbitwbExIT1hML09xaERvTzZobmNJckhmdkFqM2pnN1FXRUtTU0VseXhLODVoZ2hkYVNjWndqMWthbXpydFdzb29CUWtONDU1MTJLRDc3VFJIbHJjWWQ0QmRNUVQ0WVU9/7/2/8/4/8/ilqwo.mp4:hls:manifest.m3u8"
  ],
  "[1080p]": [
    "https://femeretes.org/0680b60a7c94377b48e01b992c00246f:2025021012:NGZZQVU2ZnMydUJTbitwbExIT1hML09xaERvTzZobmNJckhmdkFqM2pnN1FXRUtTU0VseXhLODVoZ2hkYVNjWndqMWthbXpydFdzb29CUWtONDU1MTJLRDc3VFJIbHJjWWQ0QmRNUVQ0WVU9/7/2/8/4/8/h63bf.mp4:hls:manifest.m3u8",
    "https://stream.voidboost.cc/0680b60a7c94377b48e01b992c00246f:2025021012:NGZZQVU2ZnMydUJTbitwbExIT1hML09xaERvTzZobmNJckhmdkFqM2pnN1FXRUtTU0VseXhLODVoZ2hkYVNjWndqMWthbXpydFdzb29CUWtONDU1MTJLRDc3VFJIbHJjWWQ0QmRNUVQ0WVU9/7/2/8/4/8/h63bf.mp4:hls:manifest.m3u8"
  ],
  "[1080p Ultra]": [
    "https://femeretes.org/0680b60a7c94377b48e01b992c00246f:2025021012:NGZZQVU2ZnMydUJTbitwbExIT1hML09xaERvTzZobmNJckhmdkFqM2pnN1FXRUtTU0VseXhLODVoZ2hkYVNjWndqMWthbXpydFdzb29CUWtONDU1MTJLRDc3VFJIbHJjWWQ0QmRNUVQ0WVU9/7/2/8/4/8/h63bf.mp4:hls:manifest.m3u8",
    "https://stream.voidboost.cc/0680b60a7c94377b48e01b992c00246f:2025021012:NGZZQVU2ZnMydUJTbitwbExIT1hML09xaERvTzZobmNJckhmdkFqM2pnN1FXRUtTU0VseXhLODVoZ2hkYVNjWndqMWthbXpydFdzb29CUWtONDU1MTJLRDc3VFJIbHJjWWQ0QmRNUVQ0WVU9/7/2/8/4/8/h63bf.mp4:hls:manifest.m3u8"
  ]
}

const config = {
  "videos": [
    {
      "name": "240p",
      "sources": [
        "https://notmywebsite.org/some-video-240.m3u8", // has 1 default audio track - English
        "https://notmywebsite-alternative-if-first-doesnt-work.org/some-video-240.m3u8", // has 1 default audio track - English too
      ],
    },
    {
      "name": "340p",
      "sources": [
        "https://notmywebsite.org/some-video-360.m3u8", // has 1 default audio track - English too
        "https://notmywebsite-alternative-if-first-doesnt-work.org/some-video-360.m3u8", // has 1 default audio track - English too
      ],
    }
  ],
  "additionalAudio": { // should use timingsrc
    "name": "German",
    "src": "https://mywebsite.com/some-video/german-audio.mp3"
  },
  "subtitles": [
    {
      "name": "English",
      "src": "https://notmywebsite.org/some-video/english.vtt",
    },
    {
      "name": "German",
      "src": "https://mywebsite.com/some-video/german.vtt",
    }
  ]
}

document.addEventListener("DOMContentLoaded", () => {
  const videoSource =
    "https://femeretes.org/e70971c0f9de08494a8df11edaa4a866:2025021008:eUFQTUNpVFlKcDdLdXdRdkZLcWJ3YVZiU3VJc3NPeE9ZeVY0aVl1V0xveHNGNHJlUmUzSDAya2JGLzlQcytvSHdFS0U3N25oU2UvUDN2OFJ3OWdWa1FSa3Q1ZUxNU3lxcmRScWF5SW0yVXc9/1/1/7/6/1/5/6/qje74.mp4:hls:manifest.m3u8"; // Video URL
  const audioSource = "./external-audio.mp3"; // External audio URL

  // Initialize Video.js player
  const player = videojs("cdnplayer", {
    autoplay: true,
    controls: true,
    fluid: true,
    html5: {
      // vhs: {
      //   overrideNative: true,
      //   withCredentials: true, // Enables CORS
      // },
      // nativeAudioTracks: false,
      // nativeVideoTracks: false
    },
  });

  // Set HLS source dynamically
  player.src({
    src: videoSource,
    type: "application/x-mpegURL",
  });
});
