import os
import base64
from io import BytesIO
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

class ImageGenerator:
    
    @classmethod
    def _get_client(cls):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("No Google API key found. Set GOOGLE_API_KEY in your .env file")
        
        return genai.Client(api_key=api_key)

    @classmethod
    def generate_story_image(cls, story_title: str, story_content: str, theme: str = "fantasy") -> str:
        """
        Generate an image based on the story content and return as base64 string
        """
        try:
            client = cls._get_client()
            
            # Create a descriptive prompt for the image
            image_prompt = f"""
            Create a detailed, atmospheric image for a {theme} choose-your-own-adventure story.
            
            Story Title: {story_title}
            Story Opening: {story_content[:200]}...
            
            Style: Cinematic, detailed, immersive, suitable for a book cover or game illustration.
            Mood: Mysterious, adventurous, engaging.
            """
            
            response = client.models.generate_images(
                model='imagen-4.0-generate-001',
                prompt=image_prompt.strip(),
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                )
            )
            
            if response.generated_images:
                # Get the first generated image
                generated_image = response.generated_images[0]
                
                # Convert to base64 for storage/transmission
                img_buffer = BytesIO()
                generated_image.image.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Convert to base64 string
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                return f"data:image/png;base64,{img_base64}"
            
            return None
            
        except Exception as e:
            print(f"Error generating image: {e}")
            return None

    @classmethod
    def generate_node_image(cls, node_content: str, theme: str = "fantasy") -> str:
        """
        Generate an image for a specific story node
        """
        try:
            client = cls._get_client()
            
            image_prompt = f"""
            Create a detailed, atmospheric image for a {theme} story scene.
            
            Scene: {node_content[:150]}...
            
            Style: Cinematic, detailed, immersive, suitable for a story illustration.
            Mood: Engaging, atmospheric, matches the story tone.
            """
            
            response = client.models.generate_images(
                model='imagen-4.0-generate-001',
                prompt=image_prompt.strip(),
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                )
            )
            
            if response.generated_images:
                generated_image = response.generated_images[0]
                
                img_buffer = BytesIO()
                generated_image.image.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                return f"data:image/png;base64,{img_base64}"
            
            return None
            
        except Exception as e:
            print(f"Error generating node image: {e}")
            return None 