#!/usr/bin/env python3
"""
Monitor document ingestion progress
"""

import requests
import time
import json
from datetime import datetime

def get_document_count():
    """Get current document count from Elasticsearch"""
    try:
        response = requests.get("http://localhost:9200/documents/_search?size=0")
        if response.status_code == 200:
            data = response.json()
            return data["hits"]["total"]["value"]
    except:
        pass
    return None

def get_index_size():
    """Get index size"""
    try:
        response = requests.get("http://localhost:9200/_cat/indices/documents?format=json")
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]["store.size"]
    except:
        pass
    return "Unknown"

def main():
    print("Document Ingestion Monitor")
    print("=" * 40)
    print("Press Ctrl+C to stop monitoring")
    print()
    
    initial_count = get_document_count()
    start_time = time.time()
    
    if initial_count is None:
        print("Error: Could not connect to Elasticsearch")
        return
    
    print(f"Initial document count: {initial_count}")
    print()
    
    try:
        while True:
            current_count = get_document_count()
            index_size = get_index_size()
            elapsed = time.time() - start_time
            
            if current_count is not None:
                added = current_count - initial_count
                rate = added / (elapsed / 60) if elapsed > 60 else 0
                
                print(f"{datetime.now().strftime('%H:%M:%S')} | "
                      f"Total: {current_count} | "
                      f"Added: {added} | "
                      f"Rate: {rate:.1f}/min | "
                      f"Size: {index_size}")
            else:
                print(f"{datetime.now().strftime('%H:%M:%S')} | Error connecting to Elasticsearch")
            
            time.sleep(30)  # Update every 30 seconds
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        final_count = get_document_count()
        if final_count:
            total_added = final_count - initial_count
            print(f"Final count: {final_count}")
            print(f"Total documents added: {total_added}")

if __name__ == "__main__":
    main()


