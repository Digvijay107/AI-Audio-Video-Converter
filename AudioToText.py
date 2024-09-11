import speech_recognition as sr
from pydub import AudioSegment

# Setting the FFmpeg path for pydub
AudioSegment.converter = r"C:\Users\ASUS\Downloads\ffmpeg-6.1.1-full_build\ffmpeg-6.1.1-full_build\bin\ffmpeg.exe"
AudioSegment.ffmpeg = r"C:\Users\ASUS\Downloads\ffmpeg-6.1.1-full_build\ffmpeg-6.1.1-full_build\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\Users\ASUS\Downloads\ffmpeg-6.1.1-full_build\ffmpeg-6.1.1-full_build\bin\ffprobe.exe"

# Function to convert MP3 file to WAV format
def mp3_to_wav(mp3_file, wav_file):
    audio = AudioSegment.from_mp3(mp3_file)
    audio.export(wav_file, format="wav")

# Function to convert speech in WAV file to text in chunks
def speech_to_text(wav_file, chunk_length_ms=30000):  # Default chunk length is 30 seconds
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_wav(wav_file)
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

    full_text = ""

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

    return full_text.strip()

# Main function
def main(mp3_path):
    wav_path = "temp_audio.wav"  # Temporary file for WAV format
    mp3_to_wav(mp3_path, wav_path)
    text = speech_to_text(wav_path)
    print("Extracted Text:\n", text)

# Example usage with your audio path
main(r"C:\Users\ASUS\Downloads\no.mp3")
