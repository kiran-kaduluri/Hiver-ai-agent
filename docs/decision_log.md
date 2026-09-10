# Engineering Decision Log (12 Non-Obvious Decisions)

1. **Selection of Groq LPUs (`llama-3.3-70b-versatile`) over OpenAI/Anthropic APIs**
   - *Reason:* Customer support triage requires sub-2s end-to-end response times to prevent real-time drop-offs. Groq provides >250 tokens/sec at ~$0.0004 per ticket, offering a 90%+ cost saving compared to proprietary frontier models while retaining 70B-grade reasoning.

2. **FAISS-CPU over Cloud/Hosted Vector Stores (Pinecone, ChromaDB)**
   - *Reason:* Eliminates external network hops, API credential risks, and ongoing SaaS subscription costs. In-memory FAISS indices are serialized directly inside the Docker container, enabling offline, zero-latency similarity retrieval under 15ms.

3. **CPU-Only PyTorch Packaging in Docker**
   - *Reason:* Standard `torch` installations pull heavy NVIDIA CUDA libraries (>3.5 GB), causing slow build times and container memory crashes on worker nodes. Bypassing CUDA via the official PyTorch CPU wheel index reduced the image footprint to ~180 MB.

4. **Strict Similarity Threshold (0.45 Gating) for Escalation**
   - *Reason:* LLMs will attempt to invent answers when retrieval context is weak. We enforce a cosine similarity cutoff at 0.45—any query scoring below this is automatically escalated to a human agent rather than risking hallucinated resolutions.

5. **Decoupling Intent Classification from Draft Generation (Dual-Stage Pipeline)**
   - *Reason:* Combining classification, routing, and drafting into a single monolithic LLM prompt leads to high instruction-following failures. Breaking this into Stage 1 (Classification & Risk) and Stage 2 (Grounded Draft) significantly increased policy adherence.

6. **Choosing Small Embeddings (`all-MiniLM-L6-v2`) over 1536-dim OpenAI Embeddings**
   - *Reason:* 384-dimensional dense vectors drastically shrink memory consumption in FAISS and execute in under 20ms on standard CPUs without noticeable degradation on customer support sentence-matching.

7. **Rule-Based Hybrid Overrides for Churn & Legal Keywords**
   - *Reason:* Even advanced LLMs occasionally misclassify subtle threats (e.g., *"talking to my lawyer"*, *"cancelling subscription today"*). We implemented deterministic regex/keyword overrides that force immediate escalation regardless of model confidence.

8. **Temperature Set to 0.0 for Classification and 0.2 for Drafting**
   - *Reason:* Classification requires deterministic, reproducible JSON output without creative deviation. Draft generation requires slight conversational fluidity while strictly honoring the retrieved brand macros.

9. **Sampling Multi-Turn Customer Support Threads into Single-Turn Context Windows**
   - *Reason:* Raw Twitter support data contains sprawling multi-turn noise and customer handle mentions. We filtered and consolidated initial customer complaints with the brand's verified resolution reply to maximize grounding clarity.

10. **Structured JSON Output Enforced with Strict Schema Guards**
    - *Reason:* Free-form text responses break downstream routing logic. We bound LLM outputs to structured JSON payloads (`intent`, `confidence`, `should_escalate`, `escalation_reason`) with fallback regex parsers to guarantee pipeline stability.

11. **Stateless Vector Index Initialization at Container Startup**
    - *Reason:* Rather than dynamically building vector embeddings during every user query, pre-computed FAISS index binaries are loaded into memory at startup, guaranteeing deterministic response times from the very first request.

12. **Evaluating Recall over Precision in Escalation Routing**
    - *Reason:* In enterprise support, a False Positive (escalating a routine ticket to human) costs agent time, but a False Negative (auto-replying incorrectly to an angry customer) causes user churn and brand damage. The system was tuned to favor high escalation recall.
