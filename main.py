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


def parse_srt_file(srt_filename):
    """Parse an SRT file and return a list of segments."""
    segments = []
    with open(srt_filename, "r") as srt_file:
        content = srt_file.read()
        entries = content.strip().split("\n\n")
        for entry in entries:
            lines = entry.split("\n")
            if len(lines) >= 3:
                times = lines[1]
                text = " ".join(lines[2:])
                start_str, end_str = times.split(" --> ")
                start = parse_srt_time(start_str) * 100
                end = parse_srt_time(end_str) * 100
                segments.append(Segment(start, end, text))
    return segments


def parse_srt_time(time_str):
    """Convert SRT time format to seconds."""
    hours, minutes, seconds_milliseconds = time_str.split(":")
    seconds, milliseconds = seconds_milliseconds.split(",")
    return (
        int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
    )


def create_cue_file(chapters, cue_filename):
    """Create a CUE file from chapter information."""
    with open(cue_filename, "w") as cue_file:
        cue_file.write(f'FILE "{os.path.basename(args.input)}" WAVE\n')
        for i, (start, _, chapter_name) in enumerate(chapters):
            cue_file.write(f"  TRACK {i + 1:02d} AUDIO\n")
            cue_file.write(f'    TITLE "{chapter_name}"\n')
            cue_file.write(f"    INDEX 01 {format_time((start) / 1000)}\n")


def split_audio_file(file, chapters, output_dir):
    for i, (start, end, chapter_name) in enumerate(chapters):
        # Calculate the duration in seconds
        duration = (end / 1000) - (start / 1000)

        # Create a temporary file to store the audio segment
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        ) as temp_audio_file:
            temp_audio_path = temp_audio_file.name

        # Extract the audio segment and save it to the temporary file
        ffmpeg.input(file, ss=(start / 1000), t=duration).output(
            temp_audio_path, format="wav"
        ).run(overwrite_output=True)

        # Ensure valid file name
        chapter_name = re.sub(
            r"[^\w\-_\. ]", "_", chapter_name
        )  # Replace invalid characters with '_'
        chapter_name = chapter_name[:45]  # Limit the chapter name to 100 characters
        if args.chapter_index:
            output_file = os.path.join(
                output_dir, f"{(i + args.chapter_index):02d}_{chapter_name}.mp3"
            )
        else:
            output_file = os.path.join(output_dir, f"{i:02d}_{chapter_name}.mp3")

        # Save the audio segment as an MP3 file
        (
            ffmpeg.input(temp_audio_path)
            .output(output_file, acodec="libmp3lame", audio_bitrate="128k")
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

number_pattern = re.Pattern(r"\bChapter\s+(?:" + "|".join(number_words) + r"|\d+)\b")


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
    return re.search(number_pattern, text, re.IGNORECASE)


class Segment:
    def __init__(self, t0, t1, text):
        self.t0 = t0
        self.t1 = t1
        self.text = text


def create_markdown_file(chapters, segments, markdown_filename):
    """Create a markdown file with chapters and text."""
    with open(markdown_filename, "w") as md_file:
        for start, end, chapter_name in chapters:
            md_file.write(f"# {chapter_name}\n\n")
            chapter_text = " ".join(
                segment.text for segment in segments if start <= (segment.t0 * 10) < end
            )
            md_file.write(f"{chapter_text}\n\n")


def create_raw_file_with_timestamps(segments, raw_filename):
    """Create a raw file with segments including t0 and t1 timestamps."""
    with open(raw_filename, "w") as raw_file:
        for segment in segments:
            raw_file.write(f"t0: {(segment.t0 * 10)}, t1: {segment.t1 * 10}\n")
            raw_file.write(f"{segment.text}\n\n")


def create_output_structure(file, chapters, segments):
    """Create a structured output folder for the given file."""
    # Extract the file name without extension
    file_name = os.path.splitext(os.path.basename(file))[0]

    # Create a directory for the file
    output_dir = os.path.join("Output", file_name)
    os.makedirs(output_dir, exist_ok=True)

    # Create SRT file
    srt_filename = os.path.join(output_dir, f"{file_name}.srt")
    create_srt_file(segments, srt_filename)

    # Create CUE file
    cue_filename = os.path.join(output_dir, f"{file_name}.cue")
    create_cue_file(chapters, cue_filename)

    # Split audio file using chapters
    split_audio_file(file, chapters, output_dir)

    # Create markdown file
    markdown_filename = os.path.join(output_dir, f"{file_name}.md")
    create_markdown_file(chapters, segments, markdown_filename)

    # Create raw file with timestamps
    raw_filename = os.path.join(output_dir, f"{file_name}_timestamps.txt")
    create_raw_file_with_timestamps(segments, raw_filename)


# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", required=True, help="Defines file to read from")
parser.add_argument("--model", default="base", help="Model to use")
parser.add_argument("--threads", type=int, default=6, help="Number of threads to use")
parser.add_argument(
    "--chapter_index",
    type=int,
    default=0,
    help="Number at which chapter file names will start",
)
parser.add_argument("--no_intro", help="Do not name first output file 'Intro'")

args = parser.parse_args()

model_name = args.model
n_threads = args.threads

srt_filename = os.path.splitext(args.input)[0] + ".srt"

if os.path.exists(srt_filename):
    print(f"Using existing SRT file: {srt_filename}")
    segments = parse_srt_file(srt_filename)
else:
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
if args.no_intro:
    current_chapter_name = "Chapter {args.chapter_index}"
else:
    current_chapter_name = "Intro"  # Default name for the first segment


# Identify chapters based on the keyword "Chapter" followed by a number
for segment in segments:
    if is_chapter(segment.text):
        if current_start is not None:
            chapters.append((current_start, (segment.t0 * 10), current_chapter_name))
        current_start = segment.t0 * 10
        current_chapter_name = segment.text

# Add the last chapter if it exists
if current_start is not None:
    chapters.append((current_start, segments[-1].t1 * 10, current_chapter_name))

# Create structured output
create_output_structure(args.input, chapters, segments)
