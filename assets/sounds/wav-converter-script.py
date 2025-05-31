#!/usr/bin/env python3
"""
WAV File Format Converter
Converts WAV files to: 16-bit PCM, 22050 Hz, Stereo (or keeps mono if source is mono)
"""

import os
import sys
import argparse
from pathlib import Path

# Version 1: Using pydub (recommended - easier to use)
def convert_with_pydub(input_path, output_path=None):
    """Convert WAV file using pydub library"""
    try:
        from pydub import AudioSegment
    except ImportError:
        print("Error: pydub not installed. Install with: pip install pydub")
        return False
    
    try:
        # Load the audio file
        audio = AudioSegment.from_wav(input_path)
        
        # Convert to stereo if mono (preferred according to spec)
        if audio.channels == 1:
            audio = audio.set_channels(2)
        
        # Set parameters
        audio = audio.set_frame_rate(22050)  # Set sample rate
        audio = audio.set_sample_width(2)    # 16-bit = 2 bytes
        
        # Determine output path
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_converted.wav"
        
        # Export with specified format
        audio.export(
            output_path,
            format="wav",
            parameters=["-acodec", "pcm_s16le"]  # Ensure 16-bit PCM
        )
        
        print(f"✓ Converted: {input_path.name} -> {output_path.name}")
        return True
        
    except Exception as e:
        print(f"✗ Error converting {input_path.name}: {str(e)}")
        return False


# Version 2: Using scipy and wave (standard libraries)
def convert_with_scipy(input_path, output_path=None):
    """Convert WAV file using scipy and wave libraries"""
    try:
        import wave
        import numpy as np
        from scipy.io import wavfile
        from scipy import signal
    except ImportError:
        print("Error: scipy not installed. Install with: pip install scipy")
        return False
    
    try:
        # Read the WAV file
        sample_rate, data = wavfile.read(input_path)
        
        # Convert to float for processing
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
        elif data.dtype == np.uint8:
            data = (data.astype(np.float32) - 128) / 128.0
        
        # Resample if necessary
        if sample_rate != 22050:
            # Calculate the number of samples after resampling
            num_samples = int(len(data) * 22050 / sample_rate)
            
            # Handle mono and stereo differently
            if len(data.shape) == 1:  # Mono
                data = signal.resample(data, num_samples)
            else:  # Stereo or multi-channel
                resampled = np.zeros((num_samples, data.shape[1]))
                for channel in range(data.shape[1]):
                    resampled[:, channel] = signal.resample(data[:, channel], num_samples)
                data = resampled
        
        # Convert mono to stereo if needed
        if len(data.shape) == 1:
            data = np.column_stack((data, data))
        
        # Ensure we have exactly 2 channels (stereo)
        if data.shape[1] > 2:
            data = data[:, :2]  # Keep only first 2 channels
        elif data.shape[1] == 1:
            data = np.column_stack((data[:, 0], data[:, 0]))  # Duplicate mono to stereo
        
        # Convert back to 16-bit PCM
        data = np.clip(data, -1.0, 1.0)  # Ensure values are in valid range
        data = (data * 32767).astype(np.int16)
        
        # Determine output path
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_converted.wav"
        
        # Write the output file
        wavfile.write(output_path, 22050, data)
        
        print(f"✓ Converted: {input_path.name} -> {output_path.name}")
        return True
        
    except Exception as e:
        print(f"✗ Error converting {input_path.name}: {str(e)}")
        return False


def process_folder(folder_path, method='pydub', in_place=False):
    """Process all WAV files in a folder"""
    folder = Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        print(f"Error: {folder_path} is not a valid directory")
        return
    
    # Find all WAV files
    wav_files = list(folder.glob("*.wav")) + list(folder.glob("*.WAV"))
    
    if not wav_files:
        print(f"No WAV files found in {folder_path}")
        return
    
    print(f"Found {len(wav_files)} WAV file(s) to process")
    print(f"Target format: 16-bit PCM, 22050 Hz, Stereo\n")
    
    # Choose conversion function
    convert_func = convert_with_pydub if method == 'pydub' else convert_with_scipy
    
    # Process each file
    success_count = 0
    for wav_file in wav_files:
        output_path = wav_file if in_place else None
        if convert_func(wav_file, output_path):
            success_count += 1
    
    print(f"\nProcessing complete: {success_count}/{len(wav_files)} files converted successfully")


def main():
    parser = argparse.ArgumentParser(
        description="Convert WAV files to 16-bit PCM, 22050 Hz, Stereo format"
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Folder containing WAV files (default: current directory)"
    )
    parser.add_argument(
        "--method",
        choices=["pydub", "scipy"],
        default="pydub",
        help="Conversion method to use (default: pydub)"
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite original files (default: create new files with _converted suffix)"
    )
    
    args = parser.parse_args()
    
    # Warning for in-place conversion
    if args.in_place:
        response = input("WARNING: This will overwrite original files. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return
    
    process_folder(args.folder, args.method, args.in_place)


if __name__ == "__main__":
    main()
