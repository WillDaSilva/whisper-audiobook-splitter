# Whisper Audiobook Chapterizer

This script is designed to split an audiobook into chapters based on detected chapter headings in the audio. It uses the extremely fast `whisper.cpp` model for transcription and `ffmpeg` for audio processing on Apple silion.

![Project Logo](logo.jpg)

## Features

- Transcribes audio files to text using the `whisper.cpp` model (default `large-v3-turbo`)
- Detects chapter headings in the transcribed text.
- Splits the audio file into separate chapters.
- Generates output files including SRT, CUE, Markdown, and raw text with timestamps.

## System requirements

- Tested only on Mac os
- Procesor Apple silicon (M1/M2/M3)

## Setup & Usage

- `git clone https://github.com/WillDaSilva/whisper-audiobook-splitter.git`
- `cd whisper-audiobook-splitter`
- `uv run main.py`

## Customization

- **Skip Phrases**: You can customize the phrases to skip when detecting chapters by editing the `skip_phrases.json` file.

- **Chapter Phrase**: You can change what phrase to look for as the seperator between chapters using the '--chapter_phrase' option

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) for the transcription model.
- [FFmpeg](https://ffmpeg.org/) for audio processing.
