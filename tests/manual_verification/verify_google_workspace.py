
import asyncio
import os
import sys
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from langswarm.tools.mcp.google_workspace.gmail import GmailTool
from langswarm.tools.mcp.google_workspace.calendar import CalendarTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_google_workspace():
    print("🧪 Verifying Google Workspace Tools...")
    print("⚠️  NOTE: This test requires 'credentials.json' in the current directory.")
    print("⚠️  A browser window will open for authentication if 'token.pickle' is missing.")
    
    if not os.path.exists("credentials.json"):
        print("❌ 'credentials.json' not found. Skipping verification.")
        print("   Please download OAuth client credentials from Google Cloud Console.")
        return

    # 1. Verify Gmail Tool
    print("\n📧 Testing Gmail Tool...")
    gmail = GmailTool()
    try:
        # Initialize (triggers auth)
        await gmail.initialize()
        
        # List threads
        result = await gmail.execute({
            "method": "list_threads", 
            "params": {"max_results": 3}
        })
        
        if result.get("success"):
            print(f"✅ Successfully listed {len(result.get('threads', []))} threads")
            for thread in result.get('threads', []):
                print(f"   - {thread['subject']} (from: {thread['sender']})")
        else:
            print(f"❌ Failed to list threads: {result.get('error')}")
            
        # Create Draft (Safe operation)
        draft_result = await gmail.execute({
            "method": "create_draft",
            "params": {
                "to": "test@example.com",
                "subject": "LangSwarm Test Draft",
                "body": "This is a test draft created by LangSwarm."
            }
        })
        
        if draft_result.get("success"):
            print(f"✅ Successfully created draft: {draft_result.get('draft_id')}")
        else:
            print(f"❌ Failed to create draft: {draft_result.get('error')}")

    except Exception as e:
        print(f"❌ Gmail verification failed: {e}")

    # 2. Verify Calendar Tool
    print("\nkb  Testing Calendar Tool...")
    calendar = CalendarTool()
    try:
        # Initialize
        await calendar.initialize()
        
        # List events
        result = await calendar.execute({
            "method": "list_events",
            "params": {"max_results": 5}
        })
        
        if result.get("success"):
            print(f"✅ Successfully listed {len(result.get('events', []))} events")
            for event in result.get('events', []):
                print(f"   - {event['summary']} ({event['start']})")
        else:
            print(f"❌ Failed to list events: {result.get('error')}")

    except Exception as e:
        print(f"❌ Calendar verification failed: {e}")

    print("\n🎉 Google Workspace Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify_google_workspace())
