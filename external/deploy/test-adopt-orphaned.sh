#!/bin/bash

# Test script for adopting orphaned AAF services
# Usage: ./test-adopt-orphaned.sh PROJECT_ID [ORCHESTRATOR_SECRET]

set -e

PROJECT_ID="${1:-production-pingday}"
ORCHESTRATOR_SECRET="${2:-your-orchestrator-secret-here}"
ORCHESTRATOR_URL="https://aaf-orchestrator-v2-631341022010.europe-west1.run.app"

if [[ "$PROJECT_ID" == "" ]]; then
    echo "Usage: $0 PROJECT_ID [ORCHESTRATOR_SECRET]"
    echo "Example: $0 production-pingday my-secret-key"
    exit 1
fi

echo "🔍 Testing Adopt Orphaned Services for project: $PROJECT_ID"
echo "============================================================"

# First, sync to see current status
echo "1. Syncing project to identify orphaned services..."
SYNC_RESPONSE=$(curl -s -X POST "$ORCHESTRATOR_URL/projects/$PROJECT_ID/sync" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ORCHESTRATOR_SECRET")

echo "Sync response:"
echo "$SYNC_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SYNC_RESPONSE"
echo ""

# Extract orphaned services count
ORPHANED_COUNT=$(echo "$SYNC_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    orphaned = data.get('orphaned_services', [])
    print(len(orphaned))
except:
    print('0')
" 2>/dev/null || echo "0")

if [[ "$ORPHANED_COUNT" == "0" ]]; then
    echo "✅ No orphaned services found. All services are properly registered."
    exit 0
fi

echo "📋 Found $ORPHANED_COUNT orphaned service(s)"
echo ""

# Adopt orphaned services
echo "2. Adopting orphaned services..."
ADOPT_RESPONSE=$(curl -s -X POST "$ORCHESTRATOR_URL/projects/$PROJECT_ID/adopt-orphaned" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ORCHESTRATOR_SECRET")

echo "Adoption response:"
echo "$ADOPT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ADOPT_RESPONSE"
echo ""

# Check adoption results
ADOPTED_COUNT=$(echo "$ADOPT_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    adopted = data.get('adopted_services', [])
    print(len(adopted))
except:
    print('0')
" 2>/dev/null || echo "0")

FAILED_COUNT=$(echo "$ADOPT_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    failed = data.get('failed_adoptions', [])
    print(len(failed))
except:
    print('0')
" 2>/dev/null || echo "0")

if [[ "$ADOPTED_COUNT" -gt "0" ]]; then
    echo "✅ Successfully adopted $ADOPTED_COUNT service(s)"
fi

if [[ "$FAILED_COUNT" -gt "0" ]]; then
    echo "❌ Failed to adopt $FAILED_COUNT service(s)"
fi

echo ""
echo "3. Verifying adoption by running sync again..."
FINAL_SYNC=$(curl -s -X POST "$ORCHESTRATOR_URL/projects/$PROJECT_ID/sync" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ORCHESTRATOR_SECRET")

FINAL_ORPHANED=$(echo "$FINAL_SYNC" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    orphaned = data.get('orphaned_services', [])
    print(len(orphaned))
except:
    print('0')
" 2>/dev/null || echo "0")

TOTAL_DB_INSTANCES=$(echo "$FINAL_SYNC" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    total = data.get('total_db_instances', 0)
    print(total)
except:
    print('0')
" 2>/dev/null || echo "0")

echo "Final status:"
echo "- Database instances: $TOTAL_DB_INSTANCES"
echo "- Orphaned services: $FINAL_ORPHANED"

if [[ "$FINAL_ORPHANED" == "0" ]]; then
    echo ""
    echo "🎉 Success! All services are now properly registered in the database."
else
    echo ""
    echo "⚠️  There are still $FINAL_ORPHANED orphaned service(s). Check the logs for details."
fi
