# 📋 Phase 2: Entity-Centric Chat - Implementation Plan

## **Overview**
Add an AI chat interface to the entity details drawer that allows users to:
- Ask questions about the selected entity
- Get answers based on source documents
- See citations and references
- Natural conversation about entity context

---

## **Backend API Design**

### **Endpoint: POST /api/v1/knowledge-hub/entity/{entity_name}/chat**

**Request:**
```json
{
  "message": "What are the side effects of this drug?",
  "conversation_history": [
    {"role": "user", "content": "What is this entity?"},
    {"role": "assistant", "content": "This is a medication..."}
  ],
  "space_id": "optional-filter"
}
```

**Response:**
```json
{
  "success": true,
  "response": "Based on the documents, the main side effects include...",
  "sources": [
    {
      "doc_id": "doc123",
      "title": "Clinical Trial Results",
      "snippet": "Patients reported <mark>side effects</mark> including...",
      "relevance_score": 0.95
    }
  ],
  "entity_name": "Aspirin"
}
```

---

## **Implementation Steps**

### **Step 1: Backend Service** ✅ NEXT
1. Create `entity_chat_service.py` in `services/api-gateway/services/`
2. Implement RAG pipeline:
   - Retrieve source documents for entity
   - Build context from document snippets
   - Call LLM with context + question
   - Parse response and extract citations
3. Support conversation history for context

### **Step 2: API Route** 
1. Add route in `routes/knowledge_hub.py`
2. Validate request payload
3. Handle authentication

### **Step 3: Frontend UI**
1. Add chat interface to entity drawer (`KnowledgeHub.js`)
2. Message input field
3. Chat history display
4. Source citations as clickable chips
5. Loading states

### **Step 4: Testing**
1. Unit tests for RAG pipeline
2. Integration tests for API
3. UI testing with sample questions

---

## **Technical Architecture**

### **RAG Pipeline Flow:**
```
User Question → Elasticsearch Search (entity docs) 
  → Extract relevant snippets 
  → Build prompt with context 
  → LLM Call 
  → Parse & format response 
  → Return with citations
```

### **LLM Integration:**
- Use existing Ollama setup (Phi3:mini or Llama)
- Fallback to GPT-4 if available
- Context window: ~2000 tokens max
- Include 3-5 most relevant document snippets

---

## **Sample Prompts**

**System Prompt:**
```
You are an AI assistant helping domain experts analyze entities in a knowledge graph.
Answer questions based ONLY on the provided document context.
Always cite your sources using [1], [2] notation.
If information is not in the context, say "I don't have enough information."
```

**User Prompt Template:**
```
Entity: {entity_name}
Type: {entity_type}

Context Documents:
[1] {doc1_title}: {doc1_snippet}
[2] {doc2_title}: {doc2_snippet}
...

Question: {user_question}

Answer:
```

---

## **Success Criteria**

✅ Backend API responds in < 3 seconds
✅ Answers include 2-3 source citations
✅ UI displays chat history smoothly
✅ Citations link to Document Viewer
✅ Handles "I don't know" gracefully

---

## **Next Steps**

1. Implement `entity_chat_service.py` (30 min)
2. Add API route (10 min)
3. Update frontend UI (40 min)
4. Test with sample questions (20 min)

**Total Estimate: ~1.5 hours**

