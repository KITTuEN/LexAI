import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        keys_str = os.getenv('GEMINI_API_KEY', '')
        self.api_keys = [k.strip() for k in keys_str.split(',') if k.strip()]
        
        if not self.api_keys:
            print("WARNING: GEMINI_API_KEY not found or empty.")
            
        self.clients = [genai.Client(api_key=k) for k in self.api_keys]
        self.current_client_index = 0
        
        # Using gemini-flash-latest as the standard reliable model
        self.model_name = 'gemini-flash-latest'
        self.spatial_cache = {} # Cache for nearby resources

    def _get_client(self):
        if not self.clients:
            print("WARNING: No valid Gemini clients could be initialized.")
            return None
        client = self.clients[self.current_client_index]
        self.current_client_index = (self.current_client_index + 1) % len(self.clients)
        return client

    def get_chat_response(self, chat_history, system_prompt, lang='English'):
        localized_system_prompt = f"{system_prompt}\n\nIMPORTANT: YOU MUST RESPOND ONLY IN {lang}."
        
        # Format history for new SDK
        formatted_history = []
        for msg in chat_history[:-1]:
            role = "user" if msg['role'] == 'user' else "model"
            formatted_history.append(types.Content(role=role, parts=[types.Part(text=msg['content'])]))
        
        last_message = chat_history[-1]['content']
        client = self._get_client()
        chat = client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(system_instruction=localized_system_prompt),
            history=formatted_history
        )
        response = chat.send_message(message=last_message)
        return response.text

    def analyze_case(self, situation, chat_history, system_prompt, lang='English'):
        localized_system_prompt = f"{system_prompt}\n\nIMPORTANT: THE JSON VALUES (descriptions, steps, strategies, etc.) MUST BE IN {lang}."
        
        serializable_history = []
        for msg in chat_history:
            m = msg.copy()
            if 'timestamp' in m and hasattr(m['timestamp'], 'isoformat'):
                m['timestamp'] = m['timestamp'].isoformat()
            serializable_history.append(m)

        prompt = f"""
        User Situation: {situation}
        Chat History: {json.dumps(serializable_history)}
        
        Analyze the case fully based on Indian Law. Use BNS 2023 as primary with IPC references.
        Provide the analysis in the following strict JSON format:
        {{
            "case_summary": "Short 2-3 sentence summary",
            "immediate_steps": ["Step 1", "Step 2", "Step 3"],
            "applicable_sections": [
                {{
                    "section": "Section number",
                    "title": "Title of section",
                    "description": "Description of the offense",
                    "bailable": true or false,
                    "punishment": "Duration/Type of punishment"
                }}
            ],
            "defense_strategies": [
                {{
                    "strategy": "Strategy name",
                    "strength": "High/Medium/Low",
                    "details": "Detailed explanation"
                }}
            ],
            "evidence_to_gather": ["Item 1", "Item 2"]
        }}
        """
        
        client = self._get_client()
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=localized_system_prompt,
                response_mime_type="application/json",
            )
        )
        try:
            return json.loads(response.text)
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            return {"error": "Failed to generate structured analysis", "raw_text": response.text}

    def search_section(self, query, system_prompt, lang='English'):
        try:
            localized_system_prompt = f"{system_prompt}\n\nIMPORTANT: ALL ANALYSIS AND DESCRIPTIONS WITHIN THE JSON MUST BE IN {lang}."
            prompt = f"Analyze legal query: {query}. Respond in STRICT JSON format."
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=localized_system_prompt,
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            import re
            text = response.text
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return json.loads(text)
        except Exception as e:
            print(f"Search Error: {e}")
            return {
                "section": "Error",
                "title": "Search Failed",
                "chapter": "System Issue",
                "description": "The legal intelligence service is currently experiencing heavy load. Please try again in a moment.",
                "bailable": False,
                "cognizable": False,
                "triable_by": "N/A",
                "punishment": "N/A",
                "key_ingredients": ["System Timeout", "Network Congestion"],
                "landmark_cases": ["Retry Required"]
            }

    def generate_complaint(self, details, system_prompt, lang='English'):
        localized_system_prompt = f"{system_prompt}\n\nIMPORTANT: YOU MUST GENERATE THE COMPLAINT TEXT ONLY IN {lang}."
        prompt = f"Complaint Details: {json.dumps(details, default=str)}\n\nGenerate the formal complaint text."
        client = self._get_client()
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=localized_system_prompt)
        )
        return response.text

    def analyze_document(self, image_data, mime_type, system_prompt, lang='English'):
        localized_system_prompt = f"{system_prompt}\n\nIMPORTANT: ALL JSON VALUES MUST BE PROVIDED IN {lang}."
        
        prompt = """
        Analyze this legal document (Contract, Policy, or Notice) and provide a professional breakdown in Indian Legal context.
        Provide the analysis in STRICT JSON format:
        {
            "simplified_summary": "An easy-to-understand explanation for a common person",
            "pros": ["Benefit 1", "Benefit 2"],
            "cons": ["Risk 1", "Risk 2"],
            "beneficiary": {
                "party": "Who does this favor more?",
                "reason": "Why?"
            },
            "key_clauses": [
                {
                    "clause": "Name of clause",
                    "impact": "What does it mean for the user?"
                }
            ],
            "recommendation": "Final professional advice"
        }
        """
        
        client = self._get_client()
        response = client.models.generate_content(
            model=self.model_name,
            contents=[types.Part.from_bytes(data=image_data, mime_type=mime_type), prompt],
            config=types.GenerateContentConfig(
                system_instruction=localized_system_prompt,
                response_mime_type="application/json",
            )
        )
        try:
            return json.loads(response.text)
        except Exception as e:
            print(f"Error parsing Document Analysis: {e}")
            return {
                "simplified_summary": "Failed to parse analysis.",
                "pros": [], "cons": [], "beneficiary": {"party": "N/A", "reason": "N/A"},
                "key_clauses": [], "recommendation": "Error in AI generation.",
                "raw_text": response.text
            }

    def find_nearby_legal_resources(self, lat, lng, lang='English'):
        # Cache key based on rounded coordinates (2 decimal places ~1km accuracy)
        cache_key = f"{round(float(lat), 2)}_{round(float(lng), 2)}_{lang}"
        if cache_key in self.spatial_cache:
            print(f"Returning cached spatial results for {cache_key}")
            return self.spatial_cache[cache_key]

        # Area context is now simplified to strictly rely on India
        prompt = f"""
        Identify 4 real-world legal landmarks (Police, Courts, Legal Aid) near Lat {lat}, Lng {lng} in {lang}. 
        The location is in India.
        
        You MUST return valid JSON in this exact structure:
        [
            {{
                "name": "Official Landmark Name",
                "type": "Police Station | Court | Legal Aid | Lawyer",
                "lat": (exact float), 
                "lng": (exact float),
                "status": "Localized status (e.g. Open 24/7)", 
                "icon": "fa-shield-alt | fa-gavel | fa-hand-holding-heart | fa-user-tie"
            }}
        ]
        """
        
        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            result = json.loads(response.text)
            self.spatial_cache[cache_key] = result
            return result
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "ResourceExhausted" in error_msg:
                print("Gemini API Quota Exceeded.")
                return []
            
            print(f"Error in find_nearby_legal_resources: {e}")
            return []

    def geocode_location(self, query):
        prompt = f"""
        Convert this location name or pincode into Latitude and Longitude coordinates.
        Location: {query}
        Assume India if country is not specified.
        
        Return ONLY a JSON object:
        {{
            "lat": float,
            "lng": float,
            "display_name": "Full official name of the location"
        }}
        """
        
        client = self._get_client()
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0
            )
        )
        try:
            return json.loads(response.text)
        except Exception as e:
            print(f"Geocoding Error: {e}")
            return None

    def generate_rights_guide(self, topic, lang='English'):
        prompt = f"""
        Provide a detailed legal guide on the topic: '{topic}' in the context of Indian Law (BNS 2023 / BNSS / BSA / Constitution of India).
        The response MUST be in {lang}.
        
        Provide the response in STRICT JSON format:
        {{
            "title": "A clear, localized title for the guide",
            "points": ["Short, impactful point 1", "Short, impactful point 2", "Point 3", "Point 4"],
            "tips": "A helpful, localized summary tip for the user"
        }}
        """
        
        client = self._get_client()
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        try:
            return json.loads(response.text)
        except Exception as e:
            print(f"Error parsing rights guide: {e}")
            return {"title": "Error", "points": ["Service unavailable"], "tips": "Please try again later."}

gemini_service = GeminiService()
