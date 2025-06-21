import os
import concurrent.futures
from pathlib import Path
import numpy as np
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from tqdm import tqdm
import logging

# --- Configuration (Tweak these values) ---
AUDIO_DIRECTORY = "/app/.translation-cache/edge-tts-audio-output"
OUTPUT_DIRECTORY = "/app/.translation-cache/edge-tts-audio-fixed-output"
# Set how many files to process in parallel. Adjust based on your CPU cores.
NUM_WORKERS = os.cpu_count() or 1
# The threshold for what is considered 'silence'. Lower is more sensitive.
SILENCE_THRESHOLD = 0.001
# The amount of padding to leave at the start and end of the audio, in seconds.
PADDING_DURATION_S = 0.1

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def pad_array(array: np.ndarray, sample_rate: int) -> np.ndarray:
    """
    Trims silence from the beginning and end of a NumPy audio array.
    This function is adapted from the soni_translate script.
    """
    if not array.shape[0]:
        logging.warning("Received an empty audio array.")
        return array

    # Find all indices where the audio is not silent
    valid_indices = np.where(np.abs(array) > SILENCE_THRESHOLD)[0]

    if len(valid_indices) == 0:
        logging.debug(f"Audio array is completely silent.")
        return array  # Return the empty/silent array

    # Determine start and end points with padding
    pad_samples = int(PADDING_DURATION_S * sample_rate)
    start_pad = max(0, valid_indices[0] - pad_samples)
    end_pad = min(len(array), valid_indices[-1] + 1 + pad_samples)

    return array[start_pad:end_pad]


def process_file(input_path: Path):
    """
    Loads an audio file, removes silence, and saves it to the output directory.
    """
    output_path = Path(OUTPUT_DIRECTORY) / input_path.name

    # Skip if the file already exists in the output directory
    if output_path.exists():
        return f"Skipped (already exists): {input_path.name}"

    try:
        # 1. Load the audio file using pydub
        audio_segment = AudioSegment.from_mp3(input_path)

        # 2. Convert pydub segment to a NumPy array for processing
        # Samples are converted to floating point, normalized to [-1.0, 1.0]
        samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
        samples /= (2**(audio_segment.sample_width * 8 - 1)) # Normalize

        # 3. Use the pad_array function to trim silence
        trimmed_samples = pad_array(samples, audio_segment.frame_rate)

        # 4. Convert the processed NumPy array back to a pydub segment
        # Denormalize back to the original integer range
        denormalized_samples = (trimmed_samples * (2**(audio_segment.sample_width * 8 - 1))).astype(np.int16)

        # Create a new AudioSegment from the raw byte data
        new_audio_segment = AudioSegment(
            data=denormalized_samples.tobytes(),
            sample_width=audio_segment.sample_width,
            frame_rate=audio_segment.frame_rate,
            channels=audio_segment.channels
        )

        # 5. Export the trimmed audio to the output directory
        new_audio_segment.export(output_path, format="mp3")

        return f"Processed: {input_path.name}"

    except CouldntDecodeError:
        return f"Error (Could not decode): {input_path.name}"
    except Exception as e:
        return f"Error (on {input_path.name}): {e}"


def main():
    """
    Main function to find MP3 files and process them in parallel.
    """
    input_path = Path(AUDIO_DIRECTORY)
    output_path = Path(OUTPUT_DIRECTORY)

    logging.info(f"Input Directory: {input_path}")
    logging.info(f"Output Directory: {output_path}")

    # Create the output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all .mp3 files in the input directory
    mp3_files = list(input_path.glob("*.mp3"))

    if not mp3_files:
        logging.warning("No .mp3 files found in the input directory. Exiting.")
        return

    logging.info(f"Found {len(mp3_files)} MP3 files to process.")

    # Process files in parallel using a process pool
    with concurrent.futures.ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Use tqdm to create a progress bar
        results = list(tqdm(executor.map(process_file, mp3_files), total=len(mp3_files), desc="Fixing Audio Files"))

    # Optionally, print any errors that occurred
    error_count = 0
    for res in results:
        if "Error" in res:
            logging.error(res)
            error_count += 1

    logging.info("Processing complete.")
    if error_count > 0:
        logging.warning(f"{error_count} files encountered errors.")


if __name__ == "__main__":
    main()
