import os
import json
# pyrefly: ignore [missing-import]
from groq import Groq
# pyrefly: ignore [missing-import]
from src.schemas import AgentDecision
from src.vector_store import KnowledgeStore

SYSTEM_PROMPT = """You are an official AI Tier-1 Support Agent for Amazon on Twitter (@AmazonHelp).
Your job is to analyze incoming customer tweets and return a valid JSON response.

You must follow these strict operational rules:
1. CLASSIFY INTENT: Choose exactly one from:
   - ORDER_STATUS: Where is my order, shipping carrier info, dispatch ETA.
   - DELIVERY_DELAY: Package late past expected delivery date.
   - REFUND_RETURN: Return window, pickup issues, refund timeline.
   - DAMAGED_DEFECTIVE_ITEM: Damaged box, wrong item received, broken hardware.
   - ACCOUNT_PAYMENT_ISSUE: Unauthorized charges, double billing, OTP/login issues.
   - GENERAL_INQUIRY: Product questions, general policy, feedback.

2. ESCALATION POLICY:
   - Escalate (true): If customer experienced financial loss (double charged), damaged/defective items requiring manual inspection, account lockouts, legal threats, or abusive language.
   - Auto-handle (false): Routine queries like standard tracking queries, return policy, general FAQs where guidance or standard DM links suffice.
   - Always provide a concise, factual 'escalation_reason'.

3. DRAFT REPLY:
   - Ground your answer in the historical AmazonHelp resolution examples provided.
   - Keep Twitter style: empathetic, professional, concise (<280 chars preferred).
   - If account/order verification is needed, instruct them to contact via secure DM or provide official help links. Never promise compensations without human review.

Return ONLY a valid JSON object matching the schema:
{
  "intent": "...",
  "escalate": true/false,
  "escalation_reason": "...",
  "draft_reply": "..."
}"""

class AmazonSupportAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set. Please set it in environment or pass to constructor.")
        self.client = Groq(api_key=self.api_key)
        # self.model = "llama-3.3-70b-versatile"
        # self.model = "llama-3.1-8b-instant" 
        self.model = "openai/gpt-oss-120b"
        self.kb = KnowledgeStore()
        self.kb.load_index()

    def process_tweet(self, customer_text: str) -> AgentDecision:
        # Step A: Retrieve historical grounded context
        retrieved_context = self.kb.retrieve_similar(customer_text, top_k=2)

        user_content = f"""Customer Tweet: "{customer_text}"

Relevant Historical Resolved Inquiries:
{retrieved_context}

Provide your structured decision:"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )

        raw_output = response.choices[0].message.content
        data = json.loads(raw_output)
        return AgentDecision(**data)

if __name__ == "__main__":
    agent = AmazonSupportAgent()
    
    test_queries = [
        "Where is my package? Tracking says it's out for delivery since 8 AM.",
        "You charged my card twice for order #402-99120 and the amount is deducted! This is fraud!",
        "Can I return an opened electronic item within 7 days?"
    ]
    
    for q in test_queries:
        print(f"\nIncoming: {q}")
        decision = agent.process_tweet(q)
        print(f"-> Intent: {decision.intent}")
        print(f"-> Escalate: {decision.escalate} ({decision.escalation_reason})")
        print(f"-> Draft: {decision.draft_reply}")