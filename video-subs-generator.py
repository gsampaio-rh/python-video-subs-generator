import os
import subprocess
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks


def ms_to_srt_timestamp(ms):
    """Convert milliseconds to SRT timestamp format."""
    s = ms // 1000
    ms = ms % 1000
    m = s // 60
    s = s % 60
    h = m // 60
    m = m % 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcribe_video(video_path):
    # Step 1: Extract audio from the video using ffmpeg
    audio_filename = os.path.splitext(video_path)[0] + ".wav"
    subprocess.run(["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", audio_filename])

    # Step 2: Split the audio into smaller chunks using pydub
    audio = AudioSegment.from_wav(audio_filename)
    chunk_length_ms = 5000
    chunks = make_chunks(audio, chunk_length_ms)

    # Step 3: Transcribe each chunk of audio using SpeechRecognition
    recognizer = sr.Recognizer()
    subtitle_text = ""
    start_time_ms = 0
    for i, chunk in enumerate(chunks):
        audio_chunk_filename = f"chunk{i}.wav"
        chunk.export(audio_chunk_filename, format="wav")
        with sr.AudioFile(audio_chunk_filename) as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio, show_all=False)
                end_time_ms = start_time_ms + len(chunk)
                subtitle_text += f"{i+1}\n{ms_to_srt_timestamp(start_time_ms)} --> {ms_to_srt_timestamp(end_time_ms)}\n{text}\n\n"
            except sr.UnknownValueError:
                pass
        os.remove(audio_chunk_filename)
        start_time_ms = end_time_ms

    # Step 4: Generate subtitles from the transcribed text
    subtitle_filename = os.path.splitext(video_path)[0] + ".srt"
    with open(subtitle_filename, "w") as subtitle_file:
        subtitle_file.write(subtitle_text)

    # Step 5: Embed the subtitles into the video using ffmpeg
    output_filename = os.path.splitext(video_path)[0] + "_subtitled.mp4"
    subprocess.run(["ffmpeg", "-i", video_path, "-vf", f"subtitles={subtitle_filename}", "-c:a", "copy", output_filename])

    # Step 6: Clean up intermediate files
    os.remove(audio_filename)
    # os.remove(subtitle_filename)
    
    return output_filename
    

if __name__ == "__main__":
    import sys
    video_path = sys.argv[1]
    transcribe_video(video_path)
