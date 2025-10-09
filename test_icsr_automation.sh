#!/bin/bash

echo "🧪 Testing ICSR Automation Module"
echo "=================================="
echo ""

# Test 1: Check service health
echo "1️⃣ Testing ICSR Service Health..."
curl -s http://localhost:8010/health | jq '.'
echo ""

# Test 2: Get statistics
echo "2️⃣ Getting ICSR Statistics..."
curl -s http://localhost:8010/api/v1/icsr/statistics | jq '.'
echo ""

# Test 3: Process a test email
echo "3️⃣ Testing Email Processing..."
curl -s -X POST http://localhost:8010/api/v1/icsr/process-email \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "test-email-001",
    "subject": "Adverse Event Report - Patient ID 12345",
    "body": "Patient: John Doe, Age: 45, experienced severe headache and nausea after taking Drug X (50mg) on 2024-01-15. Onset: 2 hours after administration. Reporter: Dr. Jane Smith, Hospital XYZ.",
    "sender": "dr.smith@hospital.com",
    "received_date": "2024-01-16T10:30:00Z",
    "attachments": []
  }' | jq '.'
echo ""

# Test 4: Extract ICSR from literature
echo "4️⃣ Testing ICSR Extraction from Literature..."
curl -s -X POST http://localhost:8010/api/v1/icsr/extract \
  -H "Content-Type: application/json" \
  -d '{
    "article": {
      "title": "Case Report: Severe Allergic Reaction to New Drug",
      "abstract": "A 52-year-old male patient developed anaphylaxis after administration of Drug ABC. Patient presented with urticaria, hypotension, and respiratory distress 30 minutes post-administration. Treatment: Epinephrine 0.5mg IM, IV fluids. Outcome: Complete recovery after 24 hours.",
      "full_text": "Patient Information: 52-year-old Caucasian male, no prior allergies. Drug: ABC 100mg oral tablet. Event: Anaphylaxis. Onset: 30 minutes. Outcome: Recovered. Reporter: Dr. Johnson, Cardiology Department.",
      "authors": ["Johnson MD", "Williams PhD"],
      "journal": "Clinical Case Reports",
      "publication_date": "2024-01-10",
      "pmid": "98765432"
    }
  }' | jq '.'
echo ""

# Test 5: Through API Gateway
echo "5️⃣ Testing via API Gateway..."
curl -s http://localhost:8000/api/v1/icsr/statistics | jq '.total_cases'
echo " total cases"
echo ""

echo "✅ ICSR Automation tests completed!"
echo ""

