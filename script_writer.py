import json
import logging
import requests
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScriptWriter")

class ScriptWriter:
    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.model = config.LLM_MODEL
        self.base_url = config.OPENROUTER_BASE_URL

    def _extract_json(self, text: str) -> dict:
        """Helper to extract a JSON object from text containing conversational noise."""
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            return json.loads(json_str)
        raise ValueError("No valid JSON object found in LLM response.")

    def generate_script(self, topic: str, format_type: str = "short") -> dict:
        """
        Generates a complete YouTube video script and SEO metadata for a given topic
        using the OpenRouter API. Supports 'short' (YouTube Shorts) or 'long' (Long format).
        """
        if not self.api_key:
            logger.error("OpenRouter API key is missing. Please set it in config or settings.json.")
            raise ValueError("OpenRouter API Key not set.")

        if format_type == "long":
            prompt = f"""
Create a highly engaging, relaxing ASMR-style script for a detailed long-form YouTube video (16:9 aspect ratio, 2-3 minutes long) about the following topic: "{topic}".
The script must be optimized for late-night scrolling, relaxation, and deep interest.
It MUST contain exactly 12 to 18 distinct segments to ensure the video has sufficient length (2-3 minutes). Each segment narration text must be relatively short (10-14 words max) to allow fast-paced visual cuts between segments.

Include:
- A soft, whispery, calming hook (first segment).
- Soothing facts structured as a relaxing story (body).
- Gentle calls to action and subscription requests (cta).
- Visual keywords optimized for satisfying, high-contrast landscape clips (e.g. 'satisfying water drop ripple landscape', 'relaxing green forest stream', 'calm clouds sunset').

You MUST respond ONLY with a valid JSON object. Do not include any markdown, triple backticks, or explanation.
The JSON format must match this structure exactly:
{{
  "title": "A soothing, high-CTR long-form video title",
  "segments": [
    {{
      "text": "Calming hook (10-12 words max, e.g., 'Take a deep breath. Let us explore the quiet mystery of gravity.')" ,
      "keywords": "satisfying loop kinetic, relaxing slow motion",
      "type": "hook"
    }},
    {{
      "text": "Detailed soothing fact 1 (12-14 words max, e.g., 'Did you know gravity bends light? Creating giant magnifying glasses in space.')" ,
      "keywords": "nebula space hubble telescope landscape",
      "type": "body"
    }},
    ... (Add 10-15 more segments of body facts here to reach 12-18 total segments)
  ],
  "seo": {{
    "title": "ASMR Physics - Soothing gravity facts",
    "description": "A relaxing long-form ASMR facts video to help you relax and sleep. Subscribe for daily loops.",
    "tags": ["asmr", "satisfying", "relaxing", "calming", "sleep aid", "long form", "nature", "physics"],
    "hashtags": ["#asmr", "#satisfying", "#relaxing", "#longform", "#calm"]
  }}
}}
"""
        else:
            prompt = f"""
Create a highly engaging, relaxing ASMR-style script for a fast-paced YouTube Shorts video about the following topic: "{topic}".
The script must be optimized for late-night scrolling, relaxation, and high viewer retention. It must contain:
- A soft, whispery, calming hook (first 3 seconds). e.g., 'Shhh... take a breath. Let me tell you a secret about...'
- Fascinating, satisfying, and relaxing facts structured as a soothing story.
- Gentle, low-friction call-to-actions.
- Visual keywords optimized for satisfying clips (e.g., 'kinetic sand loop', 'satisfying water waves', 'relaxing forest rain', 'slime cutting').

You MUST respond ONLY with a valid JSON object. Do not include any markdown, triple backticks, or explanation.
The JSON format must match this structure exactly:
{{
  "title": "A calming, intriguing YouTube Shorts title (under 60 characters)",
  "segments": [
    {{
      "text": "Calming, soft whispery hook (keep it short, 10-12 words max, e.g., 'Close your eyes. Relax. Did you know that...')" ,
      "keywords": "satisfying kinetic sand cutting, relaxing loops",
      "type": "hook"
    }},
    {{
      "text": "Soothing fact segment 1 (10-12 words max, e.g., 'Deep in the quietest forest on Earth, you can hear...')" ,
      "keywords": "calm foggy forest, slow motion rain drops",
      "type": "body"
    }},
    {{
      "text": "Soothing fact segment 2 (10-12 words max, e.g., 'It sounds just like soft whispers in the wind.')" ,
      "keywords": "gentle wind blowing leaves, relaxing nature",
      "type": "body"
    }},
    {{
      "text": "Relaxing engagement question (10-12 words max, e.g., 'Tell me in a whisper, have you ever been here?')" ,
      "keywords": "satisfying macro water drops, slow ripple",
      "type": "retention_point"
    }},
    {{
      "text": "Gentle subscription CTA (10-12 words max, e.g., 'Subscribe for more daily moments of calm.')" ,
      "keywords": "soft candle glow, slow flame animation",
      "type": "cta"
    }}
  ],
  "seo": {{
    "title": "ASMR Facts - Soothing title",
    "description": "A relaxing daily ASMR fact video to calm your mind. Subscribe for daily loops.",
    "tags": ["asmr", "satisfying", "relaxing", "calming", "sleep aid", "oddly satisfying", "shorts"],
    "hashtags": ["#asmr", "#satisfying", "#relaxing", "#shorts", "#calm"]
  }}
}}
"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/google/antigravity",
            "X-Title": "Antigravity YouTube Automation"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 3000 if format_type == "long" else 1500
        }

        try:
            logger.info(f"Generating {format_type} script for topic: '{topic}' using model: {self.model}")
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Robust extraction of JSON substring
                script_data = self._extract_json(content)
                logger.info("Script generation completed successfully.")
                return script_data
            else:
                logger.error(f"OpenRouter API call failed: {response.status_code} - {response.text}")
                # Fallback simple script in case of API issues
                return self._get_fallback_script(topic, format_type)
                
        except Exception as e:
            logger.error(f"Error calling OpenRouter or parsing JSON: {e}")
            return self._get_fallback_script(topic, format_type)

    def _get_fallback_script(self, topic: str, format_type: str = "short") -> dict:
        """Returns a static fallback script if the API is offline."""
        logger.warning(f"Generating a fallback script for {format_type} format.")
        if format_type == "long":
            segments = []
            # Generate 12 segments of relaxing facts
            for i in range(12):
                segments.append({
                    "text": f"Soothing fact segment number {i+1} about the deep and calming history of {topic}.",
                    "keywords": "satisfying loop, relaxing visual, oddly satisfying",
                    "type": "body"
                })
            # Set hook and CTA
            segments[0]["type"] = "hook"
            segments[0]["text"] = f"Take a slow breath. Relax. Let us explore the quiet beauty of {topic}."
            segments[-1]["type"] = "cta"
            segments[-1]["text"] = "Thank you for sharing this calm moment. Subscribe for more daily peace."
            
            return {
                "title": f"The Soothing Truth of {topic}",
                "segments": segments,
                "seo": {
                    "title": f"ASMR Study and Sleep Guide: {topic}",
                    "description": f"A relaxing long-form ASMR facts video about {topic}. Subscribe for daily calm loops.",
                    "tags": [topic.lower(), "educational", "asmr", "satisfying", "relaxing", "sleep"],
                    "hashtags": [f"#{topic.replace(' ', '')}", "#asmr", "#relaxing", "#longform"]
                }
            }
        else:
            return {
                "title": f"The Truth About {topic}",
                "segments": [
                    {
                        "text": f"Have you ever wondered about the mystery of {topic}?",
                        "keywords": "mystery, question, thinking",
                        "type": "hook"
                    },
                    {
                        "text": f"It turns out {topic} has a rich history that impacts our daily lives.",
                        "keywords": "history, civilization, earth",
                        "type": "body"
                    },
                    {
                        "text": "Many experts agree that its significance will only grow in the future.",
                        "keywords": "future, technology, growing",
                        "type": "body"
                    },
                    {
                        "text": "Make sure to hit subscribe and tell us your thoughts below!",
                        "keywords": "subscribe, youtube, comment",
                        "type": "cta"
                    }
                ],
                "seo": {
                    "title": f"The Ultimate Guide to {topic}",
                    "description": f"Exploring the incredible details of {topic}. Subscribe for daily videos!",
                    "tags": [topic.lower(), "educational", "shorts", "interesting facts"],
                    "hashtags": [f"#{topic.replace(' ', '')}", "#shorts", "#facts"]
                }
            }

if __name__ == "__main__":
    writer = ScriptWriter()
    script = writer.generate_script("Space Exploration")
    print(json.dumps(script, indent=2))
