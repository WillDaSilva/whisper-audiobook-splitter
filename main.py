from pywhispercpp.model import Model
import ffmpeg
import argparse
import re
import tempfile
import os


def format_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,ms)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{remaining_seconds:02},{milliseconds:03}"


def parse_srt_time(time_str):
    """Convert SRT time format to seconds."""
    hours, minutes, seconds_milliseconds = time_str.split(":")
    seconds, milliseconds = seconds_milliseconds.split(",")
    return (
        int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
    )


def split_audio_file(file, chapters, output_dir, initial_chapter_index):
    for chapter_index, (start, end, _) in enumerate(chapters, initial_chapter_index):
        # Calculate the duration in seconds
        duration = (end / 1000) - (start / 1000)

        # Create a temporary file to store the audio segment
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as temp_audio_file:
            temp_audio_path = temp_audio_file.name

        # Extract the audio segment and save it to the temporary file
        ffmpeg.input(file, ss=(start / 1000), t=duration).output(
            temp_audio_path,
            format="wav",
        ).run(overwrite_output=True)

        output_file = os.path.join(output_dir, f"Chapter {chapter_index:02d}.m4b")

        # Save the audio segment as an M4B file
        (
            ffmpeg.input(temp_audio_path)
            .output(output_file, acodec="aac", audio_bitrate="128k", format="mp4")
            .run(overwrite_output=True)
        )

        print(f"Created chapter file: {output_file}")

        # Clean up the temporary file
        os.remove(temp_audio_path)


def create_srt_file(segments, srt_filename):
    with open(srt_filename, "w") as srt_file:
        for i, segment in enumerate(segments):
            start_time = format_time(segment.t0 / 100)  # Convert decaseconds to seconds
            end_time = format_time(segment.t1 / 100)  # Convert decaseconds to seconds
            srt_file.write(f"{i + 1}\n{start_time} --> {end_time}\n{segment.text}\n\n")


number_words = [
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
    "twenty-one",
    "twenty-two",
    "twenty-three",
    "twenty-four",
    "twenty-five",
    "twenty-six",
    "twenty-seven",
    "twenty-eight",
    "twenty-nine",
    "thirty",
    "thirty-one",
    "thirty-two",
    "thirty-three",
    "thirty-four",
    "thirty-five",
    "thirty-six",
    "thirty-seven",
    "thirty-eight",
    "thirty-nine",
    "forty",
    "forty-one",
    "forty-two",
    "forty-three",
    "forty-four",
    "forty-five",
    "forty-six",
    "forty-seven",
    "forty-eight",
    "forty-nine",
    "fifty",
]

number_pattern = re.compile(
    r"(?i)\bChapter\s+(?:" + "|".join(number_words) + r"|\d+)\b"
)


skip_phrases = [
    "in chapter",
    "next chapter",
    "end of chapter",
    "chapter summary",
    "chapter review",
    "chapter discussion",
    "chapter analysis",
    "chapter conclusion",
    "chapter notes",
    "chapter highlights",
    "previous chapter",
    "earlier chapter",
    "in the last chapter",
    "as mentioned in chapter",
    "discussed in \\w+ chapter",
]


def is_chapter(text):
    """Check if the text contains a chapter heading."""
    for phrase in skip_phrases:
        if phrase.lower() in text.lower():
            return False
    return re.search(number_pattern, text)


class Segment:
    def __init__(self, t0, t1, text):
        self.t0 = t0
        self.t1 = t1
        self.text = text


def create_raw_file_with_timestamps(segments, raw_filename):
    """Create a raw file with segments including t0 and t1 timestamps."""
    with open(raw_filename, "w") as raw_file:
        for segment in segments:
            raw_file.write(f"t0: {(segment.t0 * 10)}, t1: {segment.t1 * 10}\n")
            raw_file.write(f"{segment.text}\n\n")


def create_output_structure(file, chapters, segments, initial_chapter_index: int):
    """Create a structured output folder for the given file."""
    # Extract the file name without extension
    file_name = os.path.splitext(os.path.basename(file))[0]

    # Create a directory for the file
    output_dir = os.path.join("output", file_name)
    os.makedirs(output_dir, exist_ok=True)

    # Create SRT file
    srt_filename = os.path.join(output_dir, f"{file_name}.srt")
    create_srt_file(segments, srt_filename)

    # Split audio file using chapters
    split_audio_file(file, chapters, output_dir, initial_chapter_index)

    # Create raw file with timestamps
    raw_filename = os.path.join(output_dir, f"{file_name}_timestamps.txt")
    create_raw_file_with_timestamps(segments, raw_filename)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="The audiobook file to split",
    )
    parser.add_argument(
        "--model",
        default="base",
        help="Model to use",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=8,
        help="Number of threads to use",
    )
    parser.add_argument(
        "--initial_chapter_name",
        default="Chapter 1",
        help="Name of the first chapter in the input file",
    )
    parser.add_argument(
        "--initial_chapter_index",
        type=int,
        default=1,
        help="Name of the first chapter in the input file",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    model_name = args.model
    n_threads = args.threads

    srt_filename = os.path.splitext(args.input)[0] + ".srt"

    print(f"Transcribing {args.input} with model {model_name}")
    # Load the whisper.cpp model
    model = Model(
        model_name,
        n_threads=n_threads,
        print_realtime=False,
        print_progress=True,
        max_len=16,
    )
    # Transcribe the audio
    segments = model.transcribe(args.input)
    # Create SRT file
    create_srt_file(segments, srt_filename)
    print(f"Created SRT file: {srt_filename}")

    chapters = []
    current_start = 0  # Start from the beginning of the file
    current_chapter_name = args.initial_chapter_name

    # Identify chapters based on the keyword "Chapter" followed by a number
    for segment in segments:
        if is_chapter(segment.text):
            if current_start is not None:
                chapters.append(
                    (current_start, (segment.t0 * 10), current_chapter_name)
                )
            current_start = segment.t0 * 10
            current_chapter_name = segment.text

    # Add the last chapter if it exists
    if current_start is not None:
        chapters.append((current_start, segments[-1].t1 * 10, current_chapter_name))

    # Create structured output
    create_output_structure(args.input, chapters, segments, args.initial_chapter_index)


if __name__ == "__main__":
    main()
