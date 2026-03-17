import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found.")
        genai.configure(api_key=api_key)
        # Using gemini-flash-latest as it is the most stable alias in this environment
        self.model_name = 'gemini-flash-latest'

    def get_chat_response(self, chat_history, system_prompt):
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt
        )
        
        # Format history for Gemini (excluding the last user message)
        formatted_history = []
        for msg in chat_history[:-1]:
            role = "user" if msg['role'] == 'user' else "model"
            formatted_history.append({"role": role, "parts": [msg['content']]})
        
        last_message = chat_history[-1]['content']
        
        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(last_message)
        return response.text

    def analyze_case(self, situation, chat_history, system_prompt):
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt
        )
        # Convert chat history to a JSON-serializable format (handling datetime objects)
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
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        try:
            return json.loads(response.text)
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            return {"error": "Failed to generate structured analysis", "raw_text": response.text}

    def search_section(self, query, system_prompt):
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt
        )
        prompt = f"Find details for: {query}\n\nReturn analysis in JSON format."
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        return json.loads(response.text)

    def generate_complaint(self, details, system_prompt):
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt
        )
        # Ensure details are JSON serializable
        prompt = f"Complaint Details: {json.dumps(details, default=str)}\n\nGenerate the formal complaint text."
        response = model.generate_content(prompt)
        return response.text

    def analyze_document(self, image_data, mime_type, system_prompt):
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt
        )
        
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
        
        response = model.generate_content(
            [{"mime_type": mime_type, "data": image_data}, prompt],
            generation_config=genai.GenerationConfig(
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

gemini_service = GeminiService()
