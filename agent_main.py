import os
import requests
import asyncio
import edge_tts
from groq import Groq
from moviepy.editor import VideoFileClip, AudioFileClip

# 1. Groq AI Script Writing
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_script():
    prompt = "Write a 30-second fascinating space fact script for YouTube Shorts. Plain text narration only."
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )
    return response.choices[0].message.content

# 2. Text to Speech (Edge-TTS)
async def generate_audio(text):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save("audio.mp3")

# 3. Background Video (Pexels API)
def fetch_background():
    headers = {"Authorization": os.environ.get("PEXELS_API_KEY")}
    url = "https://api.pexels.com/videos/search?query=space&per_page=5"
    response = requests.get(url, headers=headers).json()
    video_url = response['videos'][0]['video_files'][0]['link']
    
    with open("bg.mp4", "wb") as f:
        f.write(requests.get(video_url).content)

# 4. Video Assembly (Shorts 9:16 Format)
def create_video():
    audio = AudioFileClip("audio.mp3")
    bg = VideoFileClip("bg.mp4").subclip(0, audio.duration)
    
    bg_resized = bg.resize(height=1920)
    bg_cropped = bg_resized.crop(x1=bg_resized.w/2 - 540, width=1080, height=1920)
    
    final_clip = bg_cropped.set_audio(audio)
    final_clip.write_videofile("final_short.mp4", fps=30)

if name == "main":
    print("Generating Script...")
    script = generate_script()
    print("Script:", script)
    
    asyncio.run(generate_audio(script))
    fetch_background()
    create_video()
    print("Video Render Complete!")
