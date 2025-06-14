import whisper
import openai
import os
from moviepy.editor import *
import tempfile
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Set your OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")  # or hardcode 'sk-...'

# Step 1: Extract audio if input is a .mp4 file
def get_audio_from_input(input_path):
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".mp3":
        return input_path
    elif ext == ".mp4":
        print("Extracting audio from video...")
        temp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        video = VideoFileClip(input_path)
        video.audio.write_audiofile(temp_audio)
        return temp_audio
    else:
        raise ValueError("Unsupported file format. Please provide an .mp3 or .mp4 file.")

# Step 2: Transcribe Sanskrit audio
def transcribe_audio(audio_path):
    model = whisper.load_model("medium")
    result = model.transcribe(audio_path, language="sa")
    return result['segments']

# Step 3: Translate Sanskrit lines to English
def translate_to_english(texts):
    translations = []
    for text in texts:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Sanskrit expert translating ancient Sanskrit into fluent English."},
                    {"role": "user", "content": f"Translate this Sanskrit verse to English:\n{text}"}
                ]
            )
            translated = response['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Translation failed for: {text}. Error: {e}")
            translated = "Translation unavailable"
        translations.append(translated)
    return translations

# Step 4: Create lyric video
def create_lyric_clip(lines, audio_path, output_path, resolution=(720, 480), fontsize=30):
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    def make_txt_clip(txt, duration):
        return TextClip(txt, fontsize=fontsize, color='white', font='Devanagari Sangam MN',
                        size=resolution, method='caption').set_duration(duration)

    subtitle_clips = []
    for line in lines:
        start, end = line["start"], line["end"]
        text = f"{line['sanskrit']}\n{line['english']}"
        clip = make_txt_clip(text, end - start).set_start(start).set_position('center')
        subtitle_clips.append(clip)

    background = ColorClip(size=resolution, color=(0, 0, 0), duration=duration)
    final = CompositeVideoClip([background, *subtitle_clips]).set_audio(audio)
    final.write_videofile(output_path, fps=24)

# Main Function
def generate_lyric_video(input_media_path, output_path):
    print(f"Processing input file: {input_media_path}")
    audio_path = get_audio_from_input(input_media_path)

    print("Transcribing audio...")
    segments = transcribe_audio(audio_path)
    sanskrit_texts = [seg['text'] for seg in segments]

    print("Translating Sanskrit to English...")
    english_texts = translate_to_english(sanskrit_texts)

    print("Aligning subtitles...")
    aligned_lines = []
    for i, seg in enumerate(segments):
        aligned_lines.append({
            "sanskrit": seg['text'],
            "english": english_texts[i],
            "start": seg['start'],
            "end": seg['end']
        })

    print("Creating lyric video...")
    create_lyric_clip(aligned_lines, audio_path, output_path)
    print("✅ Lyric video saved to:", output_path)

# Example Usage
input_media_path = "chant.mp4"  # Can also be "chant.mp3"
output_path = "lyric_video.mp4"
generate_lyric_video(input_media_path, output_path)
