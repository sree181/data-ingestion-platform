#!/usr/bin/env python3
"""
Test Knowledge Hub Entity Type Colors
Verifies that nodes are correctly typed and will render in color in the UI
"""

import requests
import json
from collections import Counter

API_BASE = "http://localhost:8000"

def test_knowledge_hub_colors():
    """Test that the Knowledge Hub returns correctly typed nodes"""
    
    print("🧪 Testing Knowledge Hub Entity Type Colors")
    print("=" * 60)
    
    # 1. Get full graph
    print("\n1️⃣ Fetching full knowledge graph...")
    response = requests.get(f"{API_BASE}/api/v1/knowledge-hub/full-graph?limit=500")
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch graph: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    nodes = data.get('nodes', [])
    edges = data.get('edges', [])
    
    print(f"✅ Retrieved {len(nodes)} nodes, {len(edges)} edges")
    
    # 2. Analyze node types
    print("\n2️⃣ Analyzing node type distribution...")
    type_counter = Counter([node['type'] for node in nodes])
    
    print("\nNode Type Distribution:")
    for node_type, count in type_counter.most_common():
        percentage = (count / len(nodes) * 100) if nodes else 0
        color = get_color_for_type(node_type)
        print(f"  {color} {node_type}: {count} ({percentage:.1f}%)")
    
    # 3. Expected pharmacovigilance types
    expected_types = ['Drug', 'Disease', 'Procedure', 'Organization', 'Person']
    found_types = {t: type_counter.get(t, 0) for t in expected_types}
    
    print("\n3️⃣ Pharmacovigilance Entity Types Found:")
    total_colored = sum(found_types.values())
    colored_percentage = (total_colored / len(nodes) * 100) if nodes else 0
    
    for entity_type, count in found_types.items():
        color = get_color_for_type(entity_type)
        if count > 0:
            print(f"  ✅ {color} {entity_type}: {count}")
        else:
            print(f"  ⚠️  {color} {entity_type}: 0 (none found)")
    
    print(f"\n🎨 Total Colored Nodes: {total_colored} ({colored_percentage:.1f}%)")
    print(f"⚫ Generic Entity Nodes: {type_counter.get('Entity', 0)} ({(type_counter.get('Entity', 0) / len(nodes) * 100) if nodes else 0:.1f}%)")
    
    # 4. Sample nodes by type
    print("\n4️⃣ Sample Nodes by Type:")
    for entity_type in expected_types:
        samples = [n for n in nodes if n['type'] == entity_type][:3]
        if samples:
            print(f"\n  {get_color_for_type(entity_type)} {entity_type} samples:")
            for node in samples:
                print(f"    - {node['name']} (id: {node['id'][:20]}...)")
    
    # 5. Validation
    print("\n5️⃣ Validation Results:")
    print("=" * 60)
    
    success = True
    
    if total_colored == 0:
        print("❌ FAILED: No colored nodes found! All nodes are generic 'Entity'")
        success = False
    elif colored_percentage < 30:
        print(f"⚠️  WARNING: Only {colored_percentage:.1f}% nodes are colored (expected >30%)")
        success = False
    else:
        print(f"✅ SUCCESS: {colored_percentage:.1f}% of nodes have specific types!")
        print(f"   - {found_types['Drug']} Drugs (GREEN)")
        print(f"   - {found_types['Disease']} Diseases (RED)")
        print(f"   - {found_types['Organization']} Organizations (ORANGE)")
        print(f"   - {found_types['Person']} People (PURPLE)")
        print(f"   - {found_types['Procedure']} Procedures (CYAN)")
    
    print("\n6️⃣ Frontend Rendering Expectation:")
    print("=" * 60)
    print("When you refresh the Knowledge Hub in your browser, you should see:")
    print(f"  🟢 {found_types['Drug']} GREEN nodes (Drugs)")
    print(f"  🔴 {found_types['Disease']} RED nodes (Diseases)")
    print(f"  🟠 {found_types['Organization']} ORANGE nodes (Organizations)")
    print(f"  🟣 {found_types['Person']} PURPLE nodes (People)")
    print(f"  🔵 {found_types['Procedure']} CYAN nodes (Procedures)")
    print(f"  ⚫ {type_counter.get('Entity', 0)} GRAY nodes (Other entities)")
    print("\n💡 Make sure to do a HARD REFRESH: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)")
    
    return success

def get_color_for_type(node_type):
    """Get emoji color indicator for node type"""
    color_map = {
        'Drug': '🟢',
        'Disease': '🔴',
        'Organization': '🟠',
        'Person': '🟣',
        'Procedure': '🔵',
        'Entity': '⚫'
    }
    return color_map.get(node_type, '⚪')

if __name__ == "__main__":
    success = test_knowledge_hub_colors()
    exit(0 if success else 1)

