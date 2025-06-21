#! /usr/bin/env nix-shell
#! nix-shell -i bash -p parallel '(sox.override { enableLame = true; })'

input_dir="/home/srghma/projects/SoniTranslate/.translation-cache/edge-tts-audio-output"
output_dir="/home/srghma/projects/SoniTranslate/.translation-cache/edge-tts-audio-fixed-output"

sudo rm -rdf "$output_dir"

mkdir -p "$output_dir"

export input_dir output_dir

find "$input_dir" -type f -name '*.mp3' | parallel --halt now,fail=1 --jobs 4 '
  filename=$(basename "{}")
  outfile="$output_dir/$filename"

  if [ -f "$outfile" ]; then
    echo "Skipping $filename (already exists)"
  else
    echo "Processing $filename"
    ffmpeg -i in.mp3 -af "silenceremove=start_periods=1:start_threshold=-60dB:start_silence=1:stop_periods=1:stop_silence=1:detection=peak"

    ffmpeg -i "{}" \
      -af "silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB:stop_periods=1:stop_silence=0.1:stop_threshold=-50dB" \
      -y "$outfile"
  fi
'
