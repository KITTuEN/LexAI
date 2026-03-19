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
        
        # Using gemini-flash-latest as the standard reliable model for this project
        self.model_name = 'gemini-flash-latest'
        self.embed_model = 'models/gemini-embedding-001'
        self.types = types
        self.spatial_cache = {} # Cache for nearby resources

    def _call_with_retry(self, api_func, *args, **kwargs):
        """Executes a Gemini API call with automatic key rotation on 429 Resource Exhausted errors."""
        if not self.clients:
            raise Exception("No Gemini clients available.")
        
        max_attempts = len(self.clients)
        last_error = None

        for _ in range(max_attempts):
            client = self.clients[self.current_client_index]
            try:
                return api_func(client, *args, **kwargs)
            except Exception as e:
                err_str = str(e).upper()
                if "429" in err_str or "EXHAUSTED" in err_str or "QUOTA" in err_str:
                    print(f"Gemini Key {self.current_client_index} exhausted. Rotating...")
                    self.current_client_index = (self.current_client_index + 1) % len(self.clients)
                    last_error = e
                    continue
                raise e
        
        raise last_error or Exception("All Gemini API keys failed.")

    def _get_client(self):
        # Deprecated in favor of _call_with_retry, but kept for compatibility
        if not self.clients:
            return None
        return self.clients[self.current_client_index]

    def get_chat_response(self, chat_history, system_prompt, lang='English'):
        def _execute(client):
            localized_system_prompt = f"{system_prompt}\n\nIMPORTANT: YOU MUST RESPOND ONLY IN {lang}."
            formatted_history = []
            for msg in chat_history[:-1]:
                role = "user" if msg['role'] == 'user' else "model"
                formatted_history.append(types.Content(role=role, parts=[types.Part(text=msg['content'])]))
            
            last_message = chat_history[-1]['content']
            chat = client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(system_instruction=localized_system_prompt),
                history=formatted_history
            )
            return chat.send_message(message=last_message)

        response = self._call_with_retry(_execute)
        return response.text

    def embed_content(self, text, task_type="RETRIEVAL_DOCUMENT", title=None):
        """Generates embeddings using Gemini's text-embedding model. Supports batching."""
        def _execute(client):
            return client.models.embed_content(
                model=self.embed_model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    title=title
                )
            )
        
        response = self._call_with_retry(_execute)
        
        # If it's a list (batch), return list of embeddings
        if isinstance(text, list):
            return [e.values for e in response.embeddings]
        
        # Otherwise return single embedding
        return response.embeddings[0].values

    def analyze_case(self, situation, chat_history, system_prompt, lang='English'):
        def _execute(client):
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
            return client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=localized_system_prompt,
                    response_mime_type="application/json",
                )
            )

        try:
            response = self._call_with_retry(_execute)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            return {"error": "Failed to generate structured analysis", "raw_text": str(e)}

    def search_section(self, query, system_prompt, lang='English'):
        def _execute(client):
            localized_system_prompt = f"{system_prompt}\n\nIMPORTANT: ALL ANALYSIS AND DESCRIPTIONS WITHIN THE JSON MUST BE IN {lang}."
            prompt = f"Analyze legal query: {query}. Respond in STRICT JSON format."
            return client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=localized_system_prompt,
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

        try:
            response = self._call_with_retry(_execute)
            return json.loads(response.text)
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
        def _execute(client):
            localized_system_prompt = f"{system_prompt}\n\nIMPORTANT: YOU MUST GENERATE THE COMPLAINT TEXT ONLY IN {lang}."
            prompt = f"Complaint Details: {json.dumps(details, default=str)}\n\nGenerate the formal complaint text."
            return client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=localized_system_prompt)
            )
        
        response = self._call_with_retry(_execute)
        return response.text

    def generate_legal_document(self, doc_type, form_data, lang='English'):
        def _execute(client):
            system_prompt = f"""
            You are an expert Indian Legal Advisor and Document Drafter. 
            Your task is to generate a professional, legally valid {doc_type} based on the user's details.

            STRICT RULES:
            1. Format the document properly with clear headings, subheadings, and sections.
            2. Use formal Indian legal language.
            3. Incorporate all the details provided by the user.
            4. CRITICAL: For any details or optional information NOT provided by the user, DO NOT remove the section and DO NOT use placeholder variables like [Your Name] or <Address>. Instead, leave a clear blank line (e.g., "_________________________") so the user can fill it in manually later.
            5. MUST respond ONLY in {lang}.
            """
            prompt = f"Document Type: {doc_type}\n\nUser Provided Details:\n{json.dumps(form_data, default=str)}\n\nPlease draft the complete {doc_type} now."
            return client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system_prompt)
            )
        
        response = self._call_with_retry(_execute)
        return response.text

    def analyze_document(self, image_data, mime_type, system_prompt, lang='English'):
        def _execute(client):
            localized_system_prompt = f"{system_prompt}\n\nIMPORTANT: ALL JSON VALUES MUST BE PROVIDED IN {lang}."
            prompt = """
            Analyze this legal document (Case File, FIR, Contract, or Policy) and identify its type.
            Provide a professional breakdown in Indian Legal context.
            
            Identify the document type as one of: 'case_file', 'contract_policy', 'fir', or 'other'.

            Provide the analysis in STRICT JSON format:
            {
                "document_type": "case_file" | "contract_policy" | "fir" | "other",
                "simplified_summary": "An easy-to-understand explanation for a common person",
                "sections": ["List of key sections, articles, or chapters found"],
                "recommendation": "Final professional advice for the user",

                // Fields for 'case_file':
                "risk_percentage": 0-100 (Estimate the risk/strength of the case),
                "important_points": ["Critical facts or legal points to be analyzed"],

                // Fields for 'contract_policy':
                "pros": ["Benefits for the user"],
                "cons": ["Risks or hidden traps for the user"],
                "beneficiary": {
                    "party": "Who does this document favor more?",
                    "reason": "Explain why"
                },

                // Fields for 'fir':
                "complete_analysis": "A detailed breakdown of the FIR, including offense nature and sections mentioned",

                // Key clauses if applicable (optional):
                "key_clauses": [
                    {
                        "clause": "Name of clause",
                        "impact": "What it means for the user"
                    }
                ]
            }
            
            CRITICAL: 
            - If a field is not relevant to the document type, return [] or null for it.
            - Ensure "risk_percentage" is a number.
            """
            return client.models.generate_content(
                model=self.model_name,
                contents=[types.Part.from_bytes(data=image_data, mime_type=mime_type), prompt],
                config=types.GenerateContentConfig(
                    system_instruction=localized_system_prompt,
                    response_mime_type="application/json",
                )
            )

        try:
            response = self._call_with_retry(_execute)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error parsing Document Analysis: {e}")
            return {
                "document_type": "other",
                "simplified_summary": "Failed to parse analysis.",
                "sections": [],
                "recommendation": "Error in AI generation.",
                "raw_text": str(e)
            }

    def extract_text_from_media(self, media_data, mime_type):
        """Extracts all text from an image or PDF using Gemini."""
        def _execute(client):
            prompt = "Extract all text from this document accurately. Provide only the text content."
            return client.models.generate_content(
                model=self.model_name,
                contents=[types.Part.from_bytes(data=media_data, mime_type=mime_type), prompt]
            )
        
        response = self._call_with_retry(_execute)
        return response.text

    def find_nearby_legal_resources(self, lat, lng, lang='English'):
        # Cache key based on rounded coordinates (2 decimal places ~1km accuracy)
        cache_key = f"{round(float(lat), 2)}_{round(float(lng), 2)}_{lang}"
        if cache_key in self.spatial_cache:
            print(f"Returning cached spatial results for {cache_key}")
            return self.spatial_cache[cache_key]

        def _execute(client):
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
            return client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
        
        try:
            response = self._call_with_retry(_execute)
            result = json.loads(response.text)
            self.spatial_cache[cache_key] = result
            return result
        except Exception as e:
            print(f"Error in find_nearby_legal_resources: {e}")
            return []

    def geocode_location(self, query):
        def _execute(client):
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
            return client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
        
        try:
            response = self._call_with_retry(_execute)
            return json.loads(response.text)
        except Exception as e:
            print(f"Geocoding Error: {e}")
            return None

    def generate_rights_guide(self, topic, lang='English'):
        def _execute(client):
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
            return client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
        
        try:
            response = self._call_with_retry(_execute)
            return json.loads(response.text)
        except Exception as e:
            print(f"Error parsing rights guide: {e}")
            return {"title": "Error", "points": ["Service unavailable"], "tips": "Please try again later."}

gemini_service = GeminiService()
