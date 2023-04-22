import os
import subprocess
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks


def extract_audio(video_path, audio_filename):
    """Extract audio from the video using ffmpeg."""
    subprocess.run(["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", audio_filename])


def split_audio(audio_filename, chunk_length_ms):
    """Split the audio into smaller chunks using pydub."""
    audio = AudioSegment.from_wav(audio_filename)
    chunks = make_chunks(audio, chunk_length_ms)
    return chunks


def transcribe_audio(audio_chunk_filename):
    """Transcribe an audio chunk using SpeechRecognition."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_chunk_filename) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, show_all=False)
        except sr.UnknownValueError:
            text = ""
    return text


def generate_subtitle(subtitle_text, subtitle_filename):
    """Generate subtitles from the transcribed text."""
    with open(subtitle_filename, "w") as subtitle_file:
        subtitle_file.write(subtitle_text)


def embed_subtitles(video_path, subtitle_filename, output_filename):
    """Embed the subtitles into the video using ffmpeg."""
    subprocess.run(["ffmpeg", "-i", video_path, "-vf", f"subtitles={subtitle_filename}", "-c:a", "copy", output_filename])


def cleanup_files(*filenames):
    """Clean up intermediate files."""
    for filename in filenames:
        os.remove(filename)


def transcribe_video(video_path, chunk_length_ms=5000):
    # Step 1: Extract audio from the video using ffmpeg
    audio_filename = os.path.splitext(video_path)[0] + ".wav"
    extract_audio(video_path, audio_filename)

    # Step 2: Split the audio into smaller chunks using pydub
    chunks = split_audio(audio_filename, chunk_length_ms)

    # Step 3: Transcribe each chunk of audio using SpeechRecognition
    subtitle_text = ""
    start_time_ms = 0
    for i, chunk in enumerate(chunks):
        audio_chunk_filename = f"chunk{i}.wav"
        chunk.export(audio_chunk_filename, format="wav")
        text = transcribe_audio(audio_chunk_filename)
        end_time_ms = start_time_ms + len(chunk)
        subtitle_text += f"{i+1}\n{ms_to_srt_timestamp(start_time_ms)} --> {ms_to_srt_timestamp(end_time_ms)}\n{text}\n\n"
        os.remove(audio_chunk_filename)
        start_time_ms = end_time_ms

    # Step 4: Generate subtitles from the transcribed text
    subtitle_filename = os.path.splitext(video_path)[0] + ".srt"
    generate_subtitle(subtitle_text, subtitle_filename)

    # Step 5: Embed the subtitles into the video using ffmpeg
    output_filename = os.path.splitext(video_path)[0] + "_subtitled.mp4"
    embed_subtitles(video_path, subtitle_filename, output_filename)

    # Step 6: Clean up intermediate files
    cleanup_files(audio_filename, subtitle_filename)
    
    return output_filename

def ms_to_srt_timestamp(ms):
    """Convert milliseconds to SRT timestamp format."""
    s = ms // 1000
    ms = ms % 1000
    m = s // 60
    s = s % 60
    h = m // 60
    m = m % 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

if __name__ == "__main__":
    import sys
    video_path = sys.argv[1]
    transcribe_video(video_path)