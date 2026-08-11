import os
import json
import requests
import asyncio
import edge_tts
import PIL.Image

# Fix for MoviePy Pillow compatibility
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = getattr(PIL.Image, 'LANCZOS', getattr(PIL.Image, 'BICUBIC', None))

from groq import Groq
from moviepy.editor import VideoFileClip, AudioFileClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. Groq AI Script & Metadata Generator (Dynamic Daily Topics)
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_content():
    prompt = """
    Generate content for an educational 30-second English YouTube Short about an inspiring Islamic history fact, moral story, or Islamic architecture fact.
    
    Return strictly a JSON object with these 3 keys:
    1. "title": A catchy YouTube Short title with hashtags (e.g. "Amazing Islamic History Fact! 🕌 #Shorts #Islam #History")
    2. "script": Plain text English narration only (30 seconds long, no stage directions or sound descriptions).
    3. "search_query": 1 or 2 keywords for background video search (e.g. "mosque", "desert", "arabic architecture", "stars night").
    """
    
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        response_format={"type": "json_object"}
    )
    
    data = json.loads(response.choices[0].message.content)
    return data

# 2. Text to Speech (English Narration)
async def generate_audio(text):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save("audio.mp3")

# 3. Dynamic Background Video (Pexels API)
def fetch_background(query):
    headers = {"Authorization": os.environ.get("PEXELS_API_KEY")}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=5"
    response = requests.get(url, headers=headers).json()
    
    if "videos" not in response or not response["videos"]:
        # Fallback query if AI search has no results
        url = "https://api.pexels.com/videos/search?query=mosque&per_page=5"
        response = requests.get(url, headers=headers).json()
        
    video_url = response['videos'][0]['video_files'][0]['link']
    
    with open("bg.mp4", "wb") as f:
        f.write(requests.get(video_url).content)

# 4. Video Assembly (Shorts 9:16 Vertical Format)
def create_video():
    audio = AudioFileClip("audio.mp3")
    bg = VideoFileClip("bg.mp4").subclip(0, audio.duration)
    
    bg_resized = bg.resize(height=1920)
    bg_cropped = bg_resized.crop(x1=bg_resized.w/2 - 540, width=1080, height=1920)
    
    final_clip = bg_cropped.set_audio(audio)
    final_clip.write_videofile("final_short.mp4", fps=30)

# 5. YouTube Auto-Upload
def upload_to_youtube(title, script_summary):
    client_secret_json = os.environ.get("YOUTUBE_CLIENT_SECRET")
    if not client_secret_json:
        print("YouTube client secret missing, skipping upload.")
        return

    with open("client_secret.json", "w") as f:
        f.write(client_secret_json)

    try:
        creds = Credentials.from_authorized_user_file("client_secret.json", ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)

        request_body = {
            "snippet": {
                "title": title,
                "description": f"{script_summary}\n\nAutomated daily Islamic educational short.",
                "tags": ["islam", "islamichistory", "shorts", "facts", "education"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload("final_short.mp4", chunksize=-1, resumable=True)
        response = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        ).execute()
        print(f"Video Uploaded Successfully! Video ID: {response.get('id')}")
    except Exception as e:
        print(f"YouTube Upload Note/Error: {e}")

# Main Execution Flow
print("1. Generating Daily Islamic Content...")
content = generate_content()
print("Generated Title:", content["title"])
print("Generated Script:", content["script"])

print("2. Generating Audio...")
asyncio.run(generate_audio(content["script"]))

print("3. Downloading Background Video...")
fetch_background(content["search_query"])

print("4. Rendering Shorts Video...")
create_video()
print("Video Render Complete!")

print("5. Uploading to YouTube...")
upload_to_youtube(content["title"], content["script"])
