from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import speech_recognition as sr
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
import os
import time
from threading import Thread, Lock

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24).hex()

# Setting the FFmpeg path for pydub
AudioSegment.converter = r"C:\Users\ASUS\Downloads\ffmpeg-6.1.1-full_build\ffmpeg-6.1.1-full_build\bin\ffmpeg.exe"
AudioSegment.ffmpeg = r"C:\Users\ASUS\Downloads\ffmpeg-6.1.1-full_build\ffmpeg-6.1.1-full_build\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\Users\ASUS\Downloads\ffmpeg-6.1.1-full_build\ffmpeg-6.1.1-full_build\bin\ffprobe.exe"

# Global variables to track progress
progress_data = {'progress': 0, 'estimated_time_left': 0}
progress_lock = Lock()

@app.route('/')
def index():
    return send_from_directory('', 'index.html')

def mp3_to_wav(mp3_file, wav_file):
    audio = AudioSegment.from_mp3(mp3_file)
    audio.export(wav_file, format="wav")

def video_to_wav(video_file, wav_file):
    # Load the video and extract its audio
    video = VideoFileClip(video_file)
    audio = video.audio
    audio.write_audiofile(wav_file, codec='pcm_s16le')  # Export audio as wav format

def speech_to_text(wav_file, chunk_length_ms=30000):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_wav(wav_file)
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

    full_text = ""
    total_chunks = len(chunks)

    def process_chunks():
        nonlocal full_text
        for i, chunk in enumerate(chunks):
            chunk_filename = f"chunk_{i}.wav"
            chunk.export(chunk_filename, format="wav")

            with sr.AudioFile(chunk_filename) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                    full_text += text + " "
                except sr.UnknownValueError:
                    full_text += "[Unintelligible] "
                except sr.RequestError as e:
                    full_text += f"[Error: {e}] "
                except Exception as e:
                    full_text += f"[Error: {str(e)}] "
                    break

            os.remove(chunk_filename)

            with progress_lock:
                progress_data['progress'] = int(((i + 1) / total_chunks) * 100)
                progress_data['estimated_time_left'] = (total_chunks - (i + 1)) * 1  # Assuming 1 second per chunk
            time.sleep(0.5)

        with progress_lock:
            progress_data['progress'] = 100
            progress_data['estimated_time_left'] = 0

    thread = Thread(target=process_chunks)
    thread.start()
    thread.join()

    return full_text.strip()

@app.route('/upload', methods=['POST'])
def upload_file():
    # Reset progress at the beginning of the upload
    with progress_lock:
        progress_data['progress'] = 0
        progress_data['estimated_time_left'] = 0

    if 'audioFile' not in request.files:
        return jsonify({"transcribedText": "No file uploaded."})

    file = request.files['audioFile']
    if file.filename.endswith('.mp3'):
        mp3_path = 'uploaded_audio.mp3'
        wav_path = 'temp_audio.wav'
        file.save(mp3_path)

        mp3_to_wav(mp3_path, wav_path)
        text = speech_to_text(wav_path)

        os.remove(mp3_path)
        os.remove(wav_path)
        return jsonify({"transcribedText": text})

    elif file.filename.endswith(('.mp4', '.avi', '.mov')):
        video_path = 'uploaded_video.mp4'
        wav_path = 'temp_audio.wav'
        file.save(video_path)

        video_to_wav(video_path, wav_path)
        text = speech_to_text(wav_path)

        os.remove(video_path)
        os.remove(wav_path)
        return jsonify({"transcribedText": text})

    return jsonify({"transcribedText": "Invalid file type. Please upload an MP3 or video file."})

@app.route('/progress', methods=['GET'])
def progress():
    with progress_lock:
        return jsonify(progress_data)

if __name__ == "__main__":
    app.run(debug=True)
