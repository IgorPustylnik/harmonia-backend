import os
import random
import uuid
import tempfile
from moviepy import AudioFileClip, ImageClip


def convert_audio_to_video(audio_bytes: bytes) -> bytes:
    image_number = random.randint(1, 7)
    with tempfile.NamedTemporaryFile(suffix='.wav') as audio_temp:
        audio_temp.write(audio_bytes)
        audio_temp.seek(0)

        audio_clip = AudioFileClip(audio_temp.name)
        image_clip = ImageClip(f"./app/resources/images/{image_number}.jpg")
        video_clip = image_clip
        video_clip.audio = audio_clip
        video_clip.duration = audio_clip.duration
        video_clip.fps = 1

        temp_name = f'temp{uuid.uuid4().hex}.mp4'
        video_clip.write_videofile(
            filename=temp_name,
            remove_temp=True,
            fps=1,
            codec="libx264",
            audio_codec='aac'
        )
        audio_clip.close()
        image_clip.close()
        video_clip.close()

        with open(temp_name, 'rb') as video:
            output = video.read()
            os.remove(temp_name)
            return output
