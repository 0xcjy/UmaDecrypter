import os
import gc
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import numpy as np
import shutil
from moviepy.editor import ColorClip, ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, VideoFileClip

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# Video parameters
WIDTH, HEIGHT = 1920, 1080
FPS = 30
BACKGROUND_COLOR = (255, 255, 255) # White (used if BACKGROUND_IMAGE is None)
BACKGROUND_IMAGE = "D:\\UmaViewer\\build\\StandaloneWindows64\\Screenshots\\UmaViewer_2026-02-14_20-52-41-614.png" # Set to a path (e.g., './bg.png') to use an image
DEBUG_MODE = False # Set to True to only process the first 10 files for testing

# Font parameters
FONT_PATH = "C:\\Windows\\Fonts\\simhei.ttf" # Path to your font file
FONT_SIZE = 65
FONT_COLOR = "black"
FONT_STROKE_WIDTH = 2 # Add stroke to make transparent text visible
FONT_STROKE_COLOR = "white"

# Directories (DO NOT CHANGE)
exported_sound_dir = './exported_sound/valentine_audios'
names_file = './exported_sound/valentine_audios/names.txt'
output_video_file = './exported_sound/valentine_audios/valentine_video.mp4'

def create_text_image(text, fontsize, color, font_path=FONT_PATH, stroke_width=FONT_STROKE_WIDTH, stroke_color=FONT_STROKE_COLOR):
    try:
        font = PIL.ImageFont.truetype(font_path, fontsize)
    except:
        font = PIL.ImageFont.load_default()
    
    # Measure text size using a dummy RGBA image
    dummy_img = PIL.Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    draw = PIL.ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    
    # Calculate dimensions with padding
    padding = 20
    w = int((bbox[2] - bbox[0]) + padding * 2)
    h = int((bbox[3] - bbox[1]) + padding * 2)
    
    # Create the actual RGBA image (Transparent background)
    img = PIL.Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = PIL.ImageDraw.Draw(img)
    
    # Draw text with stroke (offset by bbox start to ensure it fits)
    draw.text((padding - bbox[0], padding - bbox[1]), text, font=font, fill=color,
              stroke_width=stroke_width, stroke_fill=stroke_color)
    
    return img # Return PIL Image for easier mask extraction

def create_video():
    # 2. Load names from names.txt
    names = []
    if os.path.exists(names_file):
        with open(names_file, 'r', encoding='utf-8') as f:
            names = [line.strip() for line in f if line.strip()]
    else:
        print(f"Error: {names_file} not found.")
        return

    # 3. Collect and sort files
    image_files = sorted([f for f in os.listdir(exported_sound_dir) if f.endswith('.png')])
    audio_files = sorted([f for f in os.listdir(exported_sound_dir) if f.endswith('.wav')])

    if not image_files or not audio_files:
        print(f"Error: No .png or .wav files found in {exported_sound_dir}")
        return

    # Ensure we have matching pairs and enough names
    min_files = min(len(image_files), len(audio_files), len(names))
    
    if DEBUG_MODE:
        print(f"DEBUG MODE ENABLED: Only processing the first 10 files.")
        min_files = min(min_files, 5)
        output_video_file_debug = output_video_file.replace(".mp4", "_debug.mp4")
    else:
        output_video_file_debug = output_video_file

    if min_files < len(image_files) or min_files < len(audio_files) or min_files < len(names):
        print("Warning: Mismatch in number of image files, audio files, or names. Processing up to the minimum count.")
    
    # Pre-create background clip factory
    def get_bg(duration):
        if BACKGROUND_IMAGE and os.path.exists(BACKGROUND_IMAGE):
            return ImageClip(BACKGROUND_IMAGE).set_duration(duration).resize(width=WIDTH, height=HEIGHT)
        else:
            return ColorClip(size=(WIDTH, HEIGHT), color=BACKGROUND_COLOR, duration=duration)

    # 4. Segmented processing (Chunking)
    CHUNK_SIZE = 10 # Adjust this number based on your RAM (lower = less RAM usage)
    temp_dir = os.path.join(os.path.dirname(output_video_file), 'temp_chunks')
    
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_video_files = []

    try:
        print(f"Starting segmented processing (Chunk size: {CHUNK_SIZE})...")
        for chunk_start in range(0, min_files, CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, min_files)
            print(f"\n--- Processing chunk {chunk_start//CHUNK_SIZE + 1}: files {chunk_start} to {chunk_end} ---")
            
            chunk_clips = []
            for i in range(chunk_start, chunk_end):
                img_path = os.path.join(exported_sound_dir, image_files[i])
                audio_path = os.path.join(exported_sound_dir, audio_files[i])
                name_text = names[i]

                # Create clips
                audio_clip = AudioFileClip(audio_path)
                audio_duration = audio_clip.duration
                total_duration = audio_duration + 0.5 # Add 0.5s pause to the clip duration

                img_clip = ImageClip(img_path).set_duration(total_duration)
                img_clip = img_clip.resize(height=HEIGHT * 0.8).set_position(("center", "center"))

                # Create text with transparent background using mask
                text_pil = create_text_image(name_text, fontsize=FONT_SIZE, color=FONT_COLOR)
                text_rgb = np.array(text_pil.convert('RGB'))
                text_mask = np.array(text_pil)[:, :, 3] / 255.0 # Extract alpha channel as mask
                
                text_clip = ImageClip(text_rgb).set_duration(total_duration)
                mask_clip = ImageClip(text_mask, ismask=True).set_duration(total_duration)
                text_clip = text_clip.set_mask(mask_clip).set_position(("center", HEIGHT * 0.1))

                # Composite current segment
                current_clip = CompositeVideoClip([get_bg(total_duration), img_clip, text_clip], size=(WIDTH, HEIGHT))
                current_clip = current_clip.set_audio(audio_clip) # Audio remains its original duration
                
                chunk_clips.append(current_clip)
                print(f"Processed file {i+1}/{min_files}: {name_text} (Duration: {total_duration:.2f}s)")
                # Removed the separate pause_clip addition here

            # Concatenate and export chunk
            print(f"Exporting temporary chunk {chunk_start}...")
            chunk_final = concatenate_videoclips(chunk_clips, method="chain")
            temp_file = os.path.join(temp_dir, f"chunk_{chunk_start}.mp4")
            chunk_final.write_videofile(temp_file, fps=FPS, codec="libx264", audio_codec="aac", threads=4, logger=None)
            
            # Close all clips in this chunk immediately to free RAM
            chunk_final.close()
            for c in chunk_clips:
                c.close()
            
            temp_video_files.append(temp_file)
            gc.collect() # Force garbage collection

        # 5. Final concatenation of all chunks
        print("\n--- All chunks processed. Joining segments into final video... ---")
        final_video_clips = [VideoFileClip(f) for f in temp_video_files]
        final_video = concatenate_videoclips(final_video_clips, method="compose")
        
        print(f"Generating final video: {output_video_file_debug}...")
        final_video.write_videofile(output_video_file_debug, fps=FPS, codec="libx264", audio_codec="aac", threads=4)
        
        # Final cleanup
        final_video.close()
        for c in final_video_clips:
            c.close()
            
        print("\nVideo generation complete!")

    finally:
        # Cleanup temporary files
        if os.path.exists(temp_dir):
            print("Cleaning up temporary chunk files...")
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not delete temp directory: {e}")

if __name__ == "__main__":
    create_video()