import json
import re
import pandas as pd

# 6 defined intents matching schemas.py
INTENT_KEYWORDS = {
    "DELIVERY_DELAY": ["late", "delayed", "not arrived", "where is", "not delivered", "still waiting", "estimated"],
    "ORDER_STATUS": ["track", "status", "dispatch", "shipped", "tracking id", "order number"],
    "REFUND_RETURN": ["refund", "return", "replacement", "money back", "cancelled", "return pickup"],
    "DAMAGED_DEFECTIVE_ITEM": ["damaged", "broken", "defective", "scratched", "wrong item", "faulty", "poor quality"],
    "ACCOUNT_PAYMENT_ISSUE": ["charged twice", "double charged", "otp", "login", "password", "prime membership", "unauthorized", "payment failed"],
    "GENERAL_INQUIRY": ["available", "restock", "warranty", "how to", "international shipping", "offer", "discount"]
}

def clean_text(text: str) -> str:
    # Handle handles like @AmazonHelp
    text = re.sub(r"@\w+", "", text)
    return text.strip()

def rule_classify(text: str):
    lower = text.lower()
    for intent, kws in INTENT_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            # Escalation policy heuristic for initial template
            escalate = intent in ["DAMAGED_DEFECTIVE_ITEM", "ACCOUNT_PAYMENT_ISSUE"] or any(
                w in lower for w in ["fraud", "urgent", "lawyer", "consumer court", "money lost", "cheat"]
            )
            reason = "High risk/financial/damage inquiry requires human investigation" if escalate else "Standard informational/tracking flow suitable for self-serve auto-handling"
            return intent, escalate, reason
    return "GENERAL_INQUIRY", False, "General inquiry handleable by self-serve bot"

def generate_golden_template(pairs_path: str = "data/processed/amazon_pairs.csv", output_json: str = "data/processed/golden_set.json", target_count: int = 150):
    df = pd.read_csv(pairs_path)
    df["cleaned_query"] = df["customer_text"].apply(clean_text)
    # Remove extremely short or noisy tweets
    df = df[df["cleaned_query"].str.split().str.len() > 5]

    sampled_list = []
    per_intent = target_count // len(INTENT_KEYWORDS)

    for intent, kws in INTENT_KEYWORDS.items():
        pattern = "|".join(kws)
        subset = df[df["cleaned_query"].str.contains(pattern, case=False, na=False)]
        sample = subset.drop_duplicates(subset=["cleaned_query"]).head(per_intent)
        sampled_list.append(sample)

    combined = pd.concat(sampled_list).drop_duplicates(subset=["customer_text"])
    
    # If stratified falls short, fill with remaining clean tweets
    if len(combined) < target_count:
        remaining = df[~df.index.isin(combined.index)].head(target_count - len(combined))
        combined = pd.concat([combined, remaining])

    golden_records = []
    for idx, row in enumerate(combined.iterrows(), 1):
        r = row[1]
        c_text = r["customer_text"]
        b_reply = r["brand_reply_text"]
        intent, escalate, reason = rule_classify(c_text)

        golden_records.append({
            "id": f"gold_{idx:03d}",
            "customer_text": c_text,
            "gold_intent": intent,
            "gold_escalate": escalate,
            "gold_escalation_reason": reason,
            "ideal_reply": b_reply
        })

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(golden_records[:target_count], f, indent=2)

    print(f"Generated {len(golden_records[:target_count])} golden evaluation cases saved to '{output_json}'.")

if __name__ == "__main__":
    generate_golden_template()