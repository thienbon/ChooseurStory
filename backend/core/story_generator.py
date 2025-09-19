from sqlalchemy.orm import Session
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

from models.story import Story, StoryNode
from core.models import StoryLLMResponse, StoryNodeLLM
from core.freepik_image_generator import FreepikImageGenerator

load_dotenv()

class StoryGenerator:

    @classmethod
    def _get_client(cls):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("No Google API key found. Set GOOGLE_API_KEY or OPENAI_API_KEY in your .env file")
        
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.0-flash-exp")

    @classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy") -> Story:
        model = cls._get_client()
        
        # Create the prompt for story generation
        prompt = f"""
        You are a creative story writer that creates engaging choose-your-own-adventure stories.
        Generate a complete branching story with multiple paths and endings in the JSON format I'll specify.

        The story should have:
        1. A compelling title
        2. A starting situation (root node) with 2-3 options
        3. Each option should lead to another node with its own options
        4. Some paths should lead to endings (both winning and losing)
        5. At least one path should lead to a winning ending

        Story structure requirements:
        - Each node should have 2-3 options except for ending nodes
        - The story should be 3-4 levels deep (including root node)
        - Add variety in the path lengths (some end earlier, some later)
        - Make sure there's at least one winning path

        Create the story with this theme: {theme}

        Output your story in this exact JSON structure:
        {{
            "title": "Story Title",
            "rootNode": {{
                "content": "The starting situation of the story",
                "isEnding": false,
                "isWinningEnding": false,
                "options": [
                    {{
                        "text": "Option 1 text",
                        "nextNode": {{
                            "content": "What happens for option 1",
                            "isEnding": false,
                            "isWinningEnding": false,
                            "options": [
                                // More nested options
                            ]
                        }}
                    }},
                    // More options for root node
                ]
            }}
        }}

        Don't simplify or omit any part of the story structure. 
        Don't add any text outside of the JSON structure.
        """

        try:
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Clean up the response to extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            # Parse the JSON response
            story_data = json.loads(response_text.strip())
            story_structure = StoryLLMResponse.model_validate(story_data)

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response from Gemini: {e}")
        except Exception as e:
            raise ValueError(f"Failed to generate story: {e}")

        # Create story in database
        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()

        # Generate main story image using Freepik
        try:
            main_image = FreepikImageGenerator.generate_story_image(
                story_structure.title, 
                story_structure.rootNode.content, 
                theme
            )
            if main_image:
                story_db.main_image = main_image
        except Exception as e:
            print(f"Failed to generate main image with Freepik: {e}")

        root_node_data = story_structure.rootNode
        if isinstance(root_node_data, dict):
            root_node_data = StoryNodeLLM.model_validate(root_node_data)

        cls._process_story_node(db, story_db.id, root_node_data, is_root=True, theme=theme)

        db.commit()
        return story_db

    @classmethod
    def _process_story_node(cls, db: Session, story_id: int, node_data: StoryNodeLLM, is_root: bool = False, theme: str = "fantasy") -> StoryNode:
        node = StoryNode(
            story_id=story_id,
            content=node_data.content if hasattr(node_data, "content") else node_data["content"],
            is_root=is_root,
            is_ending=node_data.isEnding if hasattr(node_data, "isEnding") else node_data["isEnding"],
            is_winning_ending=node_data.isWinningEnding if hasattr(node_data, "isWinningEnding") else node_data["isWinningEnding"],
            options=[]
        )
        db.add(node)
        db.flush()

        # Generate image for this node using Freepik (with rate limiting)
        try:
            node_image = FreepikImageGenerator.generate_node_image(node.content, theme)
            if node_image:
                node.image = node_image
        except Exception as e:
            print(f"Failed to generate node image with Freepik: {e}")
            # Continue without image if generation fails

        if not node.is_ending and (hasattr(node_data, "options") and node_data.options):
            options_list = []
            for option_data in node_data.options:
                next_node = option_data.nextNode

                if isinstance(next_node, dict):
                    next_node = StoryNodeLLM.model_validate(next_node)

                child_node = cls._process_story_node(db, story_id, next_node, False, theme)

                options_list.append({
                    "text": option_data.text,
                    "node_id": child_node.id
                })

            node.options = options_list

        db.flush()
        return node