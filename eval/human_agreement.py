import json
from src.judge import LLMJudge

# 5 representative samples manually scored by human (out of 5)
HUMAN_EVAL_BENCHMARK = [
    {
        "query": "Where is my refund? It's been 10 days!",
        "ideal": "Refunds usually take 3-5 business days. DM us your account email to trace it.",
        "generated": "We apologize for the delay. Please reach out via DM with your details so we can investigate.",
        "human_overall": 4.5
    },
    {
        "query": "You guys are thieves! Charged me twice!",
        "ideal": "We're sorry for the frustration. Please DM your order details so we can verify the duplicate charge.",
        "generated": "Calm down, we will look into your account when possible.",
        "human_overall": 1.5
    },
    {
        "query": "Can I exchange size for my shoes?",
        "ideal": "Yes, you can initiate a replacement via 'Your Orders' within 30 days.",
        "generated": "You can easily request a replacement by heading to 'Your Orders' on Amazon.",
        "human_overall": 5.0
    }
]

def calculate_agreement():
    judge = LLMJudge()
    human_scores = []
    judge_scores = []

    print("Running Human vs. Judge Agreement Test...")
    for item in HUMAN_EVAL_BENCHMARK:
        res = judge.evaluate_reply(item["query"], item["ideal"], item["generated"])
        j_score = res.get("overall_score", 3.0)
        human_scores.append(item["human_overall"])
        judge_scores.append(j_score)
        print(f"Query: {item['query'][:30]}... | Human: {item['human_overall']} | Judge: {j_score}")

    # Mean Absolute Error (MAE)
    mae = sum(abs(h - j) for h, j in zip(human_scores, judge_scores)) / len(human_scores)
    print(f"\nMean Absolute Error between Human and Judge: {mae:.2f} (Scale 1-5)")
    print(f"Human-Judge Agreement Alignment: {(1 - (mae / 4.0)) * 100:.1f}%")

if __name__ == "__main__":
    calculate_agreement()