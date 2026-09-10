import os
import json
from groq import Groq

JUDGE_RUBRIC = """You are an impartial Quality Assurance Evaluator for Amazon Customer Support.
Evaluate the Generated Reply against the Customer Query and Ideal Historical Resolution.

Criteria (Score each from 1 to 5):
1. Groundedness (1-5): Does the response avoid making false promises? Does it match Amazon policy?
2. Empathy & Tone (1-5): Is it polite, professional, and matching Twitter support voice?
3. Actionability (1-5): Does it offer a clear next step (e.g., DM link, order help link)?

Customer Query: "{query}"
Ideal Amazon Reply: "{ideal}"
Generated Reply: "{generated}"

Return ONLY a valid JSON:
{{
  "groundedness": 4,
  "tone": 4,
  "actionability": 4,
  "overall_score": 4.0,
  "reason": "short explanation"
}}"""

class LLMJudge:
    def __init__(self, api_key: str = None):
        key = api_key or os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=key)
        self.model = "openai/gpt-oss-120b"

    def evaluate_reply(self, query: str, ideal: str, generated: str) -> dict:
        prompt = JUDGE_RUBRIC.format(query=query, ideal=ideal, generated=generated)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            return {"groundedness": 3, "tone": 3, "actionability": 3, "overall_score": 3.0, "reason": str(e)}

if __name__ == "__main__":
    judge = LLMJudge()
    res = judge.evaluate_reply(
        query="My package was supposed to arrive today but it says delayed!",
        ideal="We're sorry for the delay! Please DM us your order ID so we can look into it.",
        generated="Hi there, apologies for the inconvenience. Please send us a direct message with your tracking details."
    )
    print("Judge Evaluation Result:")
    print(json.dumps(res, indent=2))