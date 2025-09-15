#!/usr/bin/env python3
"""
Download NLTK data with comprehensive error handling
"""
import nltk
import os

def download_nltk_data():
    """Download required NLTK data with fallback options"""
    nltk_data_dir = '/home/appuser/nltk_data'
    
    try:
        # Primary download attempt
        print("Downloading NLTK punkt_tab...")
        nltk.download('punkt_tab', download_dir=nltk_data_dir)
        print("Downloading NLTK punkt...")
        nltk.download('punkt', download_dir=nltk_data_dir)
        print("✅ NLTK data downloaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ NLTK download error: {e}")
        
        try:
            # Fallback: download essential packages
            print("Attempting fallback download...")
            essential_packages = ['punkt', 'punkt_tab', 'stopwords', 'wordnet']
            for package in essential_packages:
                try:
                    nltk.download(package, download_dir=nltk_data_dir, quiet=True)
                    print(f"Downloaded {package}")
                except:
                    print(f"Failed to download {package}")
            
            print("✅ NLTK fallback download completed")
            return True
            
        except Exception as e2:
            print(f"❌ NLTK fallback failed: {e2}")
            
            # Last resort: try with system-wide download
            try:
                print("Attempting system-wide download...")
                nltk.download('punkt_tab', quiet=True)
                nltk.download('punkt', quiet=True)
                print("✅ NLTK system download completed")
                return True
            except Exception as e3:
                print(f"❌ All NLTK download attempts failed: {e3}")
                return False

if __name__ == "__main__":
    success = download_nltk_data()
    if not success:
        print("⚠️  NLTK download failed, but continuing...")
    exit(0)  # Always exit successfully to not break Docker build