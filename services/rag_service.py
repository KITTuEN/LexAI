from services.pinecone_service import pinecone_service
from services.gemini_service import gemini_service
import json
import re

class RagService:
    def get_grounded_answer(self, question, doc_id=None, lang='English'):
        """
        Retrieves context and generates a grounded answer using Gemini.
        """
        matches = pinecone_service.query_context(question, doc_id=doc_id, top_k=5)
        
        if not matches:
            return "Not available in provided documents."

        context = "\n\n".join([m.metadata['text'] for m in matches])
        
        system_prompt = f"""
        You are the LexAI Legal Intelligence Assistant, an expert in Indian Law.
        Your goal is to provide accurate, grounded answers to legal queries while ELIMINATING hallucinations.

        You have been provided with specific context retrieved from our specialized legal datasets (IPC, BNS, and Indian Law Precedents).

        STRICT RULES:
        1. Answer ONLY using the provided context. 
        2. If the context does not contain the answer, state: "I cannot find a specific legal basis for this in my current datasets. Please consult a legal professional."
        3. Prioritize factual data from IPC/BNS sections over general knowledge.
        4. If multiple sections are relevant, summarize them clearly.
        5. Provide citations (e.g., 'As per IPC Section 302...') based on the metadata in the context.
        6. MUST respond only in {lang}.
        """
        
        prompt = f"Context:\n{context}\n\nQuestion: {question}"
        
        def _execute(client):
            return client.models.generate_content(
                model=gemini_service.model_name,
                contents=prompt,
                config=gemini_service.types.GenerateContentConfig(system_instruction=system_prompt)
            )
            
        response = gemini_service._call_with_retry(_execute)
        return response.text

    def generate_case_brief(self, doc_id, lang='English'):
        """
        Generates a structured case brief (JSON) from retrieved context.
        """
        # Retrieve a large amount of context for a full brief
        matches = pinecone_service.query_context("Analyze this case for facts, issues, verdict and reasoning", doc_id=doc_id, top_k=15)
        
        if not matches:
            return {"error": "No context found for this case."}

        context = "\n\n".join([m.metadata['text'] for m in matches])
        
        prompt = f"""
        Analyze the following case context and generate a structured brief in JSON format.
        
        Context:
        {context}
        
        JSON Structure:
        {{
            "facts": "Briefly state the essential facts of the case",
            "issues": "List the legal issues or questions being addressed",
            "verdict": "The final decision or judgment",
            "reasoning": "The legal reasoning behind the verdict"
        }}
        
        STRICT RULES:
        1. NO HALLUCINATION. Only use provided context.
        2. Respond ONLY in {lang}.
        """
        
        def _execute(client):
            return client.models.generate_content(
                model=gemini_service.model_name,
                contents=prompt,
                config=gemini_service.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
        response = gemini_service._call_with_retry(_execute)
        return json.loads(response.text)

    def extract_citations(self, text=None, doc_id=None):
        """
        Extracts legal citations (IPC, Acts, Articles) using Regex + AI.
        """
        if doc_id:
            matches = pinecone_service.query_context("Find all legal citations, sections, and acts", doc_id=doc_id, top_k=10)
            text = "\n\n".join([m.metadata['text'] for m in matches])
        
        if not text:
            return []

        # Regex patterns for common Indian legal citations
        patterns = [
            r"Section\s+\d+[a-zA-Z]*\s+of\s+the\s+[A-Za-z\s]+Act",
            r"Article\s+\d+[A-Z]*",
            r"IPC\s+Section\s+\d+",
            r"BNS\s+Section\s+\d+",
            r"\d+\s+of\s+\d+\s+IPC",
        ]
        
        regex_citations = []
        for p in patterns:
            regex_citations.extend(re.findall(p, text, re.IGNORECASE))
        
        # AI-based extraction for more complex entities
        prompt = f"Extract all unique legal citations (IPC sections, Articles, Acts) from this text and return them as a JSON list of strings.\n\nText: {text}"
        
        def _execute(client):
            return client.models.generate_content(
                model=gemini_service.model_name,
                contents=prompt,
                config=gemini_service.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            
        response = gemini_service._call_with_retry(_execute)
        ai_citations = json.loads(response.text)
        
        # Combine and deduplicate
        all_citations = list(set(regex_citations + ai_citations))
        return sorted(all_citations)

    def generate_opposing_argument(self, user_claim, doc_id=None, lang='English'):
        """
        Generates counter-arguments based on retrieved context.
        """
        matches = pinecone_service.query_context(user_claim, doc_id=doc_id, top_k=5)
        context = "\n\n".join([m.metadata['text'] for m in matches]) if matches else ""
        
        prompt = f"""
        User Legal Claim: {user_claim}
        
        Retrieved Legal Precedents/Context:
        {context}
        
        Acting as opposing counsel, generate a strong counter-argument to the user's claim. 
        Reference the retrieved context to ground your argument in legal precedent or facts if available.
        
        MUST respond only in {lang}.
        """
        
        def _execute(client):
            return client.models.generate_content(
                model=gemini_service.model_name,
                contents=prompt
            )
            
        response = gemini_service._call_with_retry(_execute)
        return response.text

    def analyze_document_with_rag(self, doc_id, lang='English'):
        """
        Performs a full RAG-based analysis of a document.
        """
        # Query for general summary, pros/cons, and risks
        matches = pinecone_service.query_context("Give me a summary, pros, cons, and hidden traps in this document.", doc_id=doc_id, top_k=15)
        
        if not matches:
            return {"error": "No context found for this document."}

        context = "\n\n".join([m.metadata['text'] for m in matches])
        
        prompt = f"""
        You are the LexAI Document Analyst. Analyze the provided context from a legal document.
        Your goal is to provide a clear, grounded, and authoritative breakdown.

        Context:
        {context}

        Identify all legal citations (e.g., IPC Section 302), specific Articles, and Acts mentioned.
        If this is a case file, provide a "Strategy Room" insight: how should a lawyer/user approach this based on the retrieved facts?

        Provide the analysis in STRICT JSON format:
        {{
            "document_type": "case_file" | "contract_policy" | "fir" | "other",
            "simplified_summary": "An easy-to-understand explanation for a common person",
            "sections": ["List of ALL key sections, articles, or chapters found (e.g. IPC 420, Art 21)"],
            "recommendation": "Final professional advice for the user",
            "strategic_insight": "A professional legal strategy or next steps based on the document",

            // Fields for 'case_file':
            "risk_percentage": 0-100,
            "important_points": ["Critical facts or legal points"],
            "citations": ["List of legal precedents or case citations found"],

            // Fields for 'contract_policy':
            "pros": ["Benefits for the user"],
            "cons": ["Risks or hidden traps"],
            "beneficiary": {{
                "party": "Who does this document favor more?",
                "reason": "Explain why"
            }},

            // Fields for 'fir':
            "complete_analysis": "A detailed breakdown of the FIR charges and implications",

            // Key clauses if applicable:
            "key_clauses": [
                {{
                    "clause": "Name of clause / Section",
                    "impact": "What it means for the user's legal standing"
                }}
            ]
        }}

        STRICT RULES:
        1. Answer ONLY using the provided context. 
        2. NO HALLUCINATION. If a value isn't found, use [] or null.
        3. Extract EVERY section and article mentioned.
        4. MUST respond only in {lang}.
        """
        
        def _execute(client):
            return client.models.generate_content(
                model=gemini_service.model_name,
                contents=prompt,
                config=gemini_service.types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )

        response = gemini_service._call_with_retry(_execute)
        text = response.text
        
        # Robust JSON extraction
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"(\{.*\})", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            raise

rag_service = RagService()
