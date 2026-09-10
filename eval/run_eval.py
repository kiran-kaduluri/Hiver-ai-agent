import os
import json
import time
from tqdm import tqdm
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from src.agent import AmazonSupportAgent
# pyrefly: ignore [missing-import]
from eval.baselines import TrivialKeywordBaseline, SimpleZeroShotBaseline

def evaluate_predictions(gold_records, preds, name="Model"):
    y_true_intent = [g["gold_intent"] for g in gold_records]
    y_pred_intent = [p.get("intent", "GENERAL_INQUIRY") for p in preds]
    
    y_true_esc = [g["gold_escalate"] for g in gold_records]
    y_pred_esc = [bool(p.get("escalate", False)) for p in preds]

    intent_acc = accuracy_score(y_true_intent, y_pred_intent)
    esc_p, esc_r, esc_f1, _ = precision_recall_fscore_support(y_true_esc, y_pred_esc, average="binary", zero_division=0)

    print(f"\n==================== {name} Results ====================")
    print(f"Intent Classification Accuracy : {intent_acc * 100:.2f}%")
    print(f"Escalation Precision          : {esc_p * 100:.2f}%")
    print(f"Escalation Recall             : {esc_r * 100:.2f}%")
    print(f"Escalation F1-Score           : {esc_f1 * 100:.2f}%")
    
    return {
        "model": name,
        "intent_accuracy": round(intent_acc, 4),
        "escalation_f1": round(esc_f1, 4),
        "escalation_recall": round(esc_r, 4)
    }

def run_full_evaluation(sample_limit: int = 150):
    # Prototyping & speed kosam default ga 30 examples meedha run chestunnam
    with open("data/processed/golden_set.json", "r", encoding="utf-8") as f:
        golden_data = json.load(f)[:sample_limit]

    print(f"Loaded {len(golden_data)} golden evaluation test cases.")

    # 1. Trivial Baseline
    print("\n[1/3] Running Baseline 1: Keyword-based...")
    kw_baseline = TrivialKeywordBaseline()
    kw_preds = [kw_baseline.predict(item["customer_text"]) for item in golden_data]
    res_kw = evaluate_predictions(golden_data, kw_preds, name="Baseline 1 (Keyword)")

    # 2. Simple Zero-shot Baseline
    print("\n[2/3] Running Baseline 2: Zero-shot LLM...")
    zs_baseline = SimpleZeroShotBaseline()
    zs_preds = []
    for item in tqdm(golden_data, desc="Zero-shot"):
        zs_preds.append(zs_baseline.predict(item["customer_text"]))
        time.sleep(0.3)  # Rate-limit safety
    res_zs = evaluate_predictions(golden_data, zs_preds, name="Baseline 2 (Zero-shot)")

    # 3. Main AI Agent (RAG + Llama/GPT 120B)
    print("\n[3/3] Running Main AI Agent (RAG Grounded)...")
    agent = AmazonSupportAgent()
    agent_preds = []
    for item in tqdm(golden_data, desc="Agent"):
        decision = agent.process_tweet(item["customer_text"])
        agent_preds.append(decision.model_dump())
        time.sleep(0.3)
    res_agent = evaluate_predictions(golden_data, agent_preds, name="Main AI Agent (Ours)")

    # Save benchmark metrics to file
    summary = [res_kw, res_zs, res_agent]
    os.makedirs("eval/results", exist_ok=True)
    with open("eval/results/benchmark_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved benchmark metrics to 'eval/results/benchmark_summary.json'!")

if __name__ == "__main__":
    run_full_evaluation(sample_limit=30)
