# Whisper Audiobook Chapterizer

This script is designed to split an audiobook into chapters based on detected chapter headings in the audio. It uses the extremely fast `whisper.cpp` model for transcription and `ffmpeg` for audio processing on Apple silion.

## System requirements

- Tested only on Mac os
- Procesor Apple silicon (M1/M2/M3)

## Setup & Usage

- `git clone https://github.com/WillDaSilva/whisper-audiobook-splitter.git`
- `cd whisper-audiobook-splitter`
- `uv run main.py -i path/to/book.m4b`

## Acknowledgments

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) for the transcription model.
- [FFmpeg](https://ffmpeg.org/) for audio processing.
