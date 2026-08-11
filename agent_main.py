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
