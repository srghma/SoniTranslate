import numpy as np
import os
import logging
import soundfile as sf

# Set up a basic logger to avoid errors if the functions use it
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTS_OperationError(Exception):
    """Custom exception for TTS operations."""
    def __init__(self, message="The operation did not complete successfully."):
        self.message = message
        super().__init__(self.message)

def verify_saved_file_and_size(filename):
    """Checks if a file was saved and is not empty."""
    if not os.path.exists(filename):
        raise TTS_OperationError(f"File '{filename}' was not saved.")
    if os.path.getsize(filename) == 0:
        raise TTS_OperationError(
            f"File '{filename}' has a zero size. "
            "This can happen with incorrect TTS settings."
        )

def pad_array(array, sr):
    """
    Trims silence from the beginning and end of a NumPy audio array.
    A small padding of 0.1 seconds is kept.
    """
    if not isinstance(array, np.ndarray):
        array = np.array(array)

    if array.ndim > 1:
        # If stereo, convert to mono by averaging channels for silence detection
        mono_array = np.mean(array, axis=1)
    else:
        mono_array = array

    if not mono_array.shape[0]:
        raise ValueError("The generated audio does not contain any data")

    # Find indices where the audio is not silent (absolute amplitude > 0.001)
    valid_indices = np.where(np.abs(mono_array) > 0.001)[0]

    if len(valid_indices) == 0:
        logger.debug("Audio appears to be completely silent.")
        return array # Return the original array if it's all silence

    try:
        # Determine padding amount (e.g., 0.1 seconds)
        pad_indice = int(0.1 * sr)

        # Calculate start and end points with padding
        start_pad = max(0, valid_indices[0] - pad_indice)
        end_pad = min(len(array), valid_indices[-1] + 1 + pad_indice)

        # Slice the original array to get the trimmed audio
        padded_array = array[start_pad:end_pad]
        return padded_array
    except Exception as error:
        logger.error(f"Error during padding: {error}")
        return array # Return original array on error
