/**
 * Knowledge Hub Debug Console Script
 * 
 * Paste this into your browser console (F12) when viewing Knowledge Hub
 * to diagnose issues with documents, relationships, drag, and community detection
 */

console.log('\n' + '='.repeat(80));
console.log('KNOWLEDGE HUB DIAGNOSTIC REPORT');
console.log('='.repeat(80) + '\n');

// 1. Check if data is loaded
console.log('1. DATA LOADED');
console.log('-'.repeat(80));
if (typeof graphData === 'undefined') {
  console.error('❌ graphData not found in scope');
  console.log('💡 Try running this in React DevTools component scope');
} else {
  console.log(`✅ Total nodes: ${graphData.nodes.length}`);
  console.log(`✅ Total links: ${graphData.links.length}`);
}

// 2. Check documents
console.log('\n2. DOCUMENTS');
console.log('-'.repeat(80));
const documents = graphData ? graphData.nodes.filter(n => n.type === 'Document') : [];
console.log(`Documents in data: ${documents.length}`);
if (documents.length > 0) {
  console.log('Sample document:', documents[0]);
  console.log('📌 Toggle "Show Documents" ON to see pink nodes!');
} else {
  console.log('❌ No documents found in graphData');
  console.log('💡 Documents might not have been imported into Neo4j yet');
}

// 3. Check relationship types
console.log('\n3. RELATIONSHIP TYPES');
console.log('-'.repeat(80));
if (graphData) {
  const relationshipTypes = [...new Set(graphData.links.map(l => l.type || l.label))];
  console.log(`Unique relationship types: ${relationshipTypes.length}`);
  relationshipTypes.forEach((type, i) => {
    const count = graphData.links.filter(l => (l.type || l.label) === type).length;
    console.log(`  ${i+1}. ${type}: ${count} links`);
  });
  
  if (relationshipTypes.length === 1) {
    console.log('\n⚠️  Only ONE relationship type found!');
    console.log('This is why all links look the same.');
    console.log('💡 You need to run semantic relationship extraction to get:');
    console.log('   - TREATS, CAUSES, INTERACTS_WITH, STUDIED_BY, etc.');
  }
}

// 4. Check predicates
console.log('\n4. RELATIONSHIP PREDICATES');
console.log('-'.repeat(80));
if (graphData) {
  const predicates = [...new Set(graphData.links.map(l => l.predicate || l.type))];
  console.log(`Unique predicates: ${predicates.length}`);
  predicates.forEach((pred, i) => {
    const count = graphData.links.filter(l => (l.predicate || l.type) === pred).length;
    console.log(`  ${i+1}. ${pred}: ${count} links`);
  });
}

// 5. Check filtered data
console.log('\n5. FILTERED DATA (What you see)');
console.log('-'.repeat(80));
if (typeof filteredGraphData !== 'undefined') {
  console.log(`Visible nodes: ${filteredGraphData.nodes.length}`);
  console.log(`Visible links: ${filteredGraphData.links.length}`);
  
  const visibleDocs = filteredGraphData.nodes.filter(n => n.type === 'Document');
  console.log(`Visible documents: ${visibleDocs.length}`);
  
  if (documents.length > 0 && visibleDocs.length === 0) {
    console.log('⚠️  Documents exist but are filtered out!');
    console.log('💡 Toggle "Show Documents" ON in Advanced Filters');
  }
} else {
  console.log('❌ filteredGraphData not found');
}

// 6. Check community detection
console.log('\n6. COMMUNITY DETECTION');
console.log('-'.repeat(80));
if (typeof communities !== 'undefined') {
  const communityCounts = {};
  Object.values(communities).forEach(c => {
    communityCounts[c] = (communityCounts[c] || 0) + 1;
  });
  console.log(`Communities found: ${Object.keys(communityCounts).length}`);
  console.log(`Nodes with community assignment: ${Object.keys(communities).length}`);
  
  if (typeof showCommunities !== 'undefined') {
    console.log(`showCommunities toggle: ${showCommunities ? 'ON ✅' : 'OFF ❌'}`);
    if (!showCommunities) {
      console.log('💡 Toggle "Show Communities" ON to see cluster-based colors');
    }
  }
  
  if (typeof communityColors !== 'undefined') {
    console.log(`Community colors defined: ${Object.keys(communityColors).length}`);
    console.log('Sample colors:', Object.entries(communityColors).slice(0, 5));
  }
} else {
  console.log('❌ communities object not found');
}

// 7. Check toggles
console.log('\n7. CURRENT FILTER SETTINGS');
console.log('-'.repeat(80));
if (typeof showAllNodes !== 'undefined') console.log(`showAllNodes: ${showAllNodes}`);
if (typeof showCommunities !== 'undefined') console.log(`showCommunities: ${showCommunities}`);
if (typeof showDocuments !== 'undefined') console.log(`showDocuments: ${showDocuments ? '✅ ON' : '❌ OFF'}`);
if (typeof minConnections !== 'undefined') console.log(`minConnections: ${minConnections}`);
if (typeof minConfidence !== 'undefined') console.log(`minConfidence: ${minConfidence}`);
if (typeof sourceFilter !== 'undefined') console.log(`sourceFilter: ${sourceFilter}`);

// 8. Check drag functionality
console.log('\n8. DRAG FUNCTIONALITY');
console.log('-'.repeat(80));
console.log('enableNodeDrag should be set to: true');
console.log('💡 Try clicking and holding a node, then moving your mouse');
console.log('If drag still doesn\'t work, check browser console for errors');

// 9. Recommendations
console.log('\n9. 📋 RECOMMENDATIONS');
console.log('='.repeat(80));

const recommendations = [];

if (documents.length === 0) {
  recommendations.push('❌ No documents in data → Import documents into Neo4j');
}

if (documents.length > 0 && typeof showDocuments !== 'undefined' && !showDocuments) {
  recommendations.push('🔧 Documents hidden → Toggle "Show Documents" ON');
}

if (graphData && [...new Set(graphData.links.map(l => l.type || l.label))].length === 1) {
  recommendations.push('🔧 Only one relationship type → Run semantic relationship extraction');
}

if (typeof showCommunities !== 'undefined' && !showCommunities) {
  recommendations.push('🔧 Community colors not visible → Toggle "Show Communities" ON');
}

if (recommendations.length === 0) {
  console.log('✅ Everything looks good! If issues persist, check browser console for errors.');
} else {
  recommendations.forEach((rec, i) => console.log(`${i+1}. ${rec}`));
}

console.log('\n' + '='.repeat(80));
console.log('END OF DIAGNOSTIC REPORT');
console.log('='.repeat(80) + '\n');

console.log('💡 TIP: To access component state, use React DevTools:');
console.log('   1. Install React DevTools browser extension');
console.log('   2. Find KnowledgeHub component');
console.log('   3. Right-click → "Store as global variable"');
console.log('   4. Access state via $r or $reactTemp1\n');

