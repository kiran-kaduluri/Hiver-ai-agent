import os
import json
from groq import Groq
from src.schemas import AgentDecision, IntentType

KEYWORD_RULES = {
    "DELIVERY_DELAY": ["late", "delay", "not arrived", "where is", "stuck", "still waiting"],
    "ORDER_STATUS": ["track", "status", "dispatch", "shipped", "tracking id", "order #"],
    "REFUND_RETURN": ["refund", "return", "replacement", "money back", "cancelled"],
    "DAMAGED_DEFECTIVE_ITEM": ["damaged", "broken", "defective", "scratched", "faulty"],
    "ACCOUNT_PAYMENT_ISSUE": ["charge", "debited", "double", "otp", "login", "fraud", "unauthorized"]
}

class TrivialKeywordBaseline:
    """Baseline 1: Pure deterministic keyword matching without LLM."""
    def predict(self, text: str) -> dict:
        lower = text.lower()
        pred_intent: IntentType = "GENERAL_INQUIRY"
        
        for intent, kws in KEYWORD_RULES.items():
            if any(k in lower for k in kws):
                pred_intent = intent
                break
                
        # Simple heuristic: damage or payment issues get escalated
        escalate = pred_intent in ["DAMAGED_DEFECTIVE_ITEM", "ACCOUNT_PAYMENT_ISSUE"]
        
        return {
            "intent": pred_intent,
            "escalate": escalate,
            "escalation_reason": "Rule-based keyword trigger" if escalate else "No risk keyword detected",
            "draft_reply": "Please reach out to our customer support team for further assistance."
        }

class SimpleZeroShotBaseline:
    """Baseline 2: Zero-shot LLM without RAG/retrieved historical context."""
    def __init__(self, api_key: str = None):
        key = api_key or os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=key)
        self.model = "openai/gpt-oss-120b"

    def predict(self, text: str) -> dict:
        prompt = f"""Classify this tweet into one intent: ORDER_STATUS, DELIVERY_DELAY, REFUND_RETURN, DAMAGED_DEFECTIVE_ITEM, ACCOUNT_PAYMENT_ISSUE, GENERAL_INQUIRY.
Decide if escalate (true/false) and draft a brief reply.
Tweet: "{text}"

Return JSON: {{"intent": "...", "escalate": true/false, "escalation_reason": "...", "draft_reply": "..."}}"""

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(resp.choices[0].message.content)