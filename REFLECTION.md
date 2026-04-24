# Reflection: Multi-Memory Agent (Lab #17)

## 1. PII and Privacy Risks
The current implementation saves user facts (Long-term Profile) and conversation summaries (Episodic Memory) in local JSON files. If this system were deployed:
- **Sensitive Facts**: The agent might inadvertently save PII (Personally Identifiable Information) such as home addresses, health conditions (allergies), or financial details.
- **Episodic Data**: Summaries of past conversations can leak context that was intended to be transient.

## 2. Most Sensitive Memory Type
**Long-term Profile** is the most sensitive because it contains distilled facts that persist indefinitely. Unlike episodic memory which might get buried, profile facts are injected into almost every prompt, making them highly prone to exposure if the agent is "jailbroken" or asked to reveal its state.

## 3. Deletion, TTL, and Consent
- **Consent**: Users should be notified that the agent uses long-term memory to personalize experiences and given an option to disable it.
- **Deletion**: A "forget me" command should be implemented to clear `profile.json` and `episodes.json`.
- **TTL (Time To Live)**: Episodic memories should ideally have an expiration date (e.g., deleted after 30 days) to comply with "right to be forgotten" principles.

## 4. Technical Limitations and Scaling
- **Vector Search Latency**: As semantic memory grows, searching local vector indices (FAISS) might become slow. A managed vector database (like Pinecone or Weaviate) would be needed.
- **Prompt Window Limits**: Injecting all 4 memory types can quickly consume the context window. We currently use a message trim and limit episodic memory to 10 items, but a more sophisticated "relevance-based" pruning is needed.
- **Conflict Management**: Our current logic simply overwrites facts. In complex scenarios, a user might have temporary states (e.g., "I'm in Hanoi for 1 week") that shouldn't permanently overwrite their home location.
