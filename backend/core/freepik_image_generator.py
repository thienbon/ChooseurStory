import os
import requests
import time
import base64
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

class FreepikImageGenerator:
    
    @classmethod
    def _get_api_key(cls):
        api_key = os.getenv("FREEPIK_API_KEY")
        
        if not api_key:
            raise ValueError("No Freepik API key found. Set FREEPIK_API_KEY in your .env file")
        
        return api_key

    @classmethod
    def _create_prompt(cls, story_title: str, story_content: str, theme: str = "fantasy") -> str:
        """Create a descriptive prompt for Freepik image generation"""
        return f"Create a detailed, cinematic illustration for a {theme} adventure story titled '{story_title}'. Scene: {story_content[:200]}. Style: Book cover quality, atmospheric, mysterious, adventurous. High detail, rich colors, fantasy art style."

    @classmethod
    def _post_generation_request(cls, payload: dict) -> dict:
        """Helper to POST the generation request and return initial response"""
        api_key = cls._get_api_key()
        url = "https://api.freepik.com/v1/ai/mystic"
        
        headers = {
            "x-freepik-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        # Handle rate limiting specifically
        if response.status_code == 429:
            print(f"Rate limited by Freepik API. Waiting 30 seconds before retry...")
            time.sleep(30)
            response = requests.post(url, json=payload, headers=headers)
        
        response.raise_for_status()  # Raise exception for HTTP errors
        
        result = response.json()
        if "data" not in result or "task_id" not in result["data"]:
            raise ValueError(f"Invalid response from Freepik API: {result}")
        
        return result["data"]

    @classmethod
    def _poll_for_completion(cls, task_id: str, max_wait_seconds: int = 600, poll_interval: int = 10) -> dict:
        """Poll the generation status until complete or timeout"""
        api_key = cls._get_api_key()
        url = f"https://api.freepik.com/v1/ai/mystic/{task_id}"
        
        headers = {
            "x-freepik-api-key": api_key
        }
        
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise ValueError(f"Failed to check status: {response.status_code} - {response.text}")
            
            result = response.json()
            data = result.get("data", {})
            status = data.get("status")
            print(f"Polling status for task {task_id}: {status}")
            
            if status == "COMPLETED":
                generated = data.get("generated", [])
                if not generated:
                    raise ValueError(f"Generation completed but no images generated: {result}")
                
                # Skip if any NSFW flagged
                has_nsfw = data.get("has_nsfw", [])
                if has_nsfw and any(has_nsfw):
                    raise ValueError("NSFW content detected in generated image(s)")
                
                return data
            elif status in ["CREATED", "IN_PROGRESS"]:
                time.sleep(poll_interval)
            else:
                raise ValueError(f"Generation failed with unexpected status '{status}': {result}")
        
        raise TimeoutError(f"Generation timed out after {max_wait_seconds} seconds for task {task_id}")

    @classmethod
    def _download_and_encode_image(cls, image_url: str) -> str:
        """Download image from URL and return as base64 string with detected MIME type"""
        response = requests.get(image_url)
        response.raise_for_status()
    
        content_type = response.headers.get('content-type', 'image/png').split(';')[0].strip()  # e.g., 'image/jpeg'
        if not content_type.startswith('image/'):
            content_type = 'image/png'  # Fallback
    
        image_data = BytesIO(response.content)
        base64_image = base64.b64encode(image_data.read()).decode("utf-8")
        return f"{content_type};base64,{base64_image}"

    @classmethod
    def generate_story_image(cls, story_title: str, story_content: str, theme: str = "fantasy") -> str:
        """
        Generate an image using Freepik API and return as base64 string
        """
        try:
            # Add delay to prevent rate limiting
            time.sleep(2)
            
            prompt = cls._create_prompt(story_title, story_content, theme)
            
            payload = {
                "prompt": prompt.strip(),
                # Removed webhook_url since we're polling
                "structure_reference": "",
                "structure_strength": 50,
                "style_reference": "",
                "adherence": 50,
                "hdr": 50,
                "resolution": "2k",
                "aspect_ratio": "square_1_1",
                "model": "realism",
                "creative_detailing": 33,
                "engine": "automatic",
                "fixed_generation": False,
                "filter_nsfw": True,
                "styling": {
                    "styles": [],
                    "characters": [],
                    "colors": [
                        {
                            "color": "#4A90E2",
                            "weight": 0.5
                        }
                    ]
                }
            }
            
            # Start generation
            initial_data = cls._post_generation_request(payload)
            task_id = initial_data["task_id"]
            print(f"Started story image generation: task_id={task_id}")
            
            # Poll for completion
            completed_data = cls._poll_for_completion(task_id)
            
            # Download and encode the first generated image
            image_url = completed_data["generated"][0]
            base64_str = cls._download_and_encode_image(image_url)
            
            print(f"Successfully generated story image for '{story_title}'")
            return base64_str
                
        except Exception as e:
            print(f"Error generating story image: {e}")
            return None

    @classmethod
    def generate_node_image(cls, node_content: str, theme: str = "fantasy") -> str:
        """
        Generate an image for a specific story node using Freepik API
        """
        try:
            # Add delay to prevent rate limiting
            time.sleep(3)
            
            prompt = f"Create a detailed, cinematic illustration for a {theme} story scene. Scene: {node_content[:200]}. Style: Story illustration, atmospheric, engaging, immersive. High detail, rich colors, fantasy art style."
            
            payload = {
                "prompt": prompt.strip(),
                # Removed webhook_url since we're polling
                "structure_reference": "",
                "structure_strength": 50,
                "style_reference": "",
                "adherence": 50,
                "hdr": 50,
                "resolution": "2k",
                "aspect_ratio": "square_1_1",
                "model": "realism",
                "creative_detailing": 33,
                "engine": "automatic",
                "fixed_generation": False,
                "filter_nsfw": True,
                "styling": {
                    "styles": [],
                    "characters": [],
                    "colors": [
                        {
                            "color": "#4A90E2",
                            "weight": 0.5
                        }
                    ]
                }
            }
            
            # Start generation
            initial_data = cls._post_generation_request(payload)
            task_id = initial_data["task_id"]
            print(f"Started node image generation: task_id={task_id}")
            
            # Poll for completion
            completed_data = cls._poll_for_completion(task_id)
            
            # Download and encode the first generated image
            image_url = completed_data["generated"][0]
            base64_str = cls._download_and_encode_image(image_url)
            
            print(f"Successfully generated node image")
            return base64_str
                
        except Exception as e:
            print(f"Error generating node image: {e}")
            return None

    @classmethod
    def check_generation_status(cls, task_id: str) -> dict:
        """
        Check the status of a generation (manual check)
        """
        try:
            api_key = cls._get_api_key()
            url = f"https://api.freepik.com/v1/ai/mystic/{task_id}"
            
            headers = {
                "x-freepik-api-key": api_key
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
                
        except Exception as e:
            print(f"Error checking generation status: {e}")
            return None