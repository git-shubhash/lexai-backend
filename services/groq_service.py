"""
Groq AI Service - Legal document analysis using llama-3.3-70b-versatile
"""

import os
import time
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv('GROQ_API_KEY'))
MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
MAX_TOKENS_PER_CHUNK = 6000
MAX_RETRIES = 3


def chunk_text(text: str, max_tokens: int = MAX_TOKENS_PER_CHUNK) -> list[str]:
    """Split text into manageable chunks"""
    # Approximate: 1 token ≈ 4 characters
    max_chars = max_tokens * 4
    chunks = []
    while len(text) > max_chars:
        split_point = text[:max_chars].rfind('\n\n')
        if split_point == -1:
            split_point = text[:max_chars].rfind('. ')
        if split_point == -1:
            split_point = max_chars
        chunks.append(text[:split_point])
        text = text[split_point:].strip()
    if text:
        chunks.append(text)
    return chunks


def call_groq(messages: list, temperature: float = 0.3, max_tokens: int = 4096) -> str:
    """Make a Groq API call with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq API attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
            else:
                raise e


def summarize_document(text: str) -> dict:
    """Generate comprehensive legal document summary"""
    chunks = chunk_text(text)
    combined_summary = ""

    # If multiple chunks, summarize each then combine
    if len(chunks) > 1:
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Summarizing chunk {i+1}/{len(chunks)}")
            summary = call_groq([
                {"role": "system", "content": LEGAL_SYSTEM_PROMPT},
                {"role": "user", "content": f"Summarize this section of a legal document concisely:\n\n{chunk}"}
            ])
            chunk_summaries.append(summary)
        combined_text = "\n\n".join(chunk_summaries)
    else:
        combined_text = chunks[0]

    # Generate structured analysis
    analysis_prompt = f"""Analyze this legal document and provide a comprehensive structured response in the following JSON format:

{{
  "short_summary": "2-3 sentence overview of the document",
  "detailed_summary": "Full detailed summary covering all major aspects (5-8 paragraphs)",
  "document_type": "Type of legal document (e.g., NDA, Employment Contract, etc.)",
  "parties_involved": ["list of parties"],
  "key_legal_points": ["key point 1", "key point 2", ...],
  "obligations": ["obligation 1", "obligation 2", ...],
  "important_deadlines": ["deadline 1", "deadline 2", ...],
  "penalties": ["penalty 1", "penalty 2", ...],
  "legal_risks": [
    {{"risk": "description", "level": "low|medium|high", "explanation": "why this is a risk"}}
  ],
  "clauses": {{
    "confidentiality": "extracted text or null",
    "liability": "extracted text or null",
    "payment": "extracted text or null",
    "arbitration": "extracted text or null",
    "termination": "extracted text or null",
    "non_compete": "extracted text or null",
    "indemnification": "extracted text or null",
    "governing_law": "extracted text or null"
  }},
  "simplified_explanation": "Plain English explanation for non-lawyers",
  "overall_risk_score": "low|medium|high",
  "confidence_score": 0.95
}}

Legal Document:
{combined_text[:12000]}"""

    response = call_groq([
        {"role": "system", "content": LEGAL_SYSTEM_PROMPT},
        {"role": "user", "content": analysis_prompt}
    ], max_tokens=4096)

    # Parse JSON response
    import json
    import re
    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"error": "Could not parse structured response", "raw": response}
    except json.JSONDecodeError:
        return {"error": "JSON parse error", "raw": response}


def chat_with_document(text: str, question: str, history: list) -> str:
    """AI chat about document content"""
    # Build conversation messages
    messages = [
        {"role": "system", "content": f"""You are an expert legal document analyst with 20+ years of experience.
Your role is to answer questions about the following legal document. Be specific, cite relevant sections, and explain complex legal language in clear, natural language.

IMPORTANT INSTRUCTION: ALWAYS respond in natural, conversational language using standard Markdown formatting. DO NOT output raw JSON unless the user explicitly asks for JSON.

DOCUMENT CONTENT:
{text[:8000]}"""}
    ]

    # Add conversation history
    for msg in history[-6:]:  # Last 6 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": question})

    return call_groq(messages, temperature=0.4, max_tokens=2048)


def compare_documents(text1: str, text2: str) -> dict:
    """Compare two legal documents"""
    prompt = f"""Compare these two legal documents and provide a detailed analysis in JSON format:

{{
  "document1_type": "type of document 1",
  "document2_type": "type of document 2",
  "similarities": ["similarity 1", "similarity 2", ...],
  "differences": [
    {{"aspect": "aspect name", "doc1": "how it appears in doc 1", "doc2": "how it appears in doc 2"}}
  ],
  "missing_in_doc1": ["clause/provision missing in document 1"],
  "missing_in_doc2": ["clause/provision missing in document 2"],
  "risk_comparison": {{
    "doc1_risk": "low|medium|high",
    "doc2_risk": "low|medium|high",
    "doc1_risks": ["risk 1", "risk 2"],
    "doc2_risks": ["risk 1", "risk 2"]
  }},
  "recommendation": "Which document is more favorable and why",
  "overall_comparison": "Summary of the comparison"
}}

DOCUMENT 1:
{text1[:5000]}

DOCUMENT 2:
{text2[:5000]}"""

    response = call_groq([
        {"role": "system", "content": LEGAL_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ], max_tokens=4096)

    import json, re
    try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"error": "Could not parse response", "raw": response}
    except json.JSONDecodeError:
        return {"error": "Parse error", "raw": response}


LEGAL_SYSTEM_PROMPT = """You are an expert legal document analyst with 20+ years of experience in contract law, corporate law, and legal risk assessment. Your role is to:

1. Analyze legal documents with precision and accuracy
2. Extract key clauses, obligations, and risks
3. Explain complex legal language in simple terms
4. Identify potential legal risks and their severity
5. Provide actionable insights for non-lawyers

Always be:
- Professional and precise
- Clear and structured in your responses
- Objective in risk assessment
- Thorough in clause extraction
- Helpful in simplifying legal jargon

When returning JSON, ensure it is valid and complete."""
