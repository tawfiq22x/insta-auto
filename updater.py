# updater.py - Fast & Reliable Updater for Instagram Bot
import os
import sys
import glob
import time
import shutil
import zipfile
import urllib.request
import urllib.error

FILES_TO_UPDATE = [
    'main.py',
    'ldplayer_automation.py',
    'easyearn_client.py',
    'requirements.txt',
    'run.bat',
    'UPDATE.bat',
    'updater.py'
]

def print_banner():
    print("=" * 55)
    print("       🤖 Instagram Bot - Update Utility")
    print("=" * 55)
    print()

def update_from_github(repo_url: str) -> bool:
    repo_url = repo_url.strip().rstrip('/')
    if not repo_url.startswith('http'):
        repo_url = 'https://' + repo_url
    
    # Extract owner and repo
    # e.g. https://github.com/owner/repo or https://raw.githubusercontent.com/owner/repo
    clean_url = repo_url.replace('https://github.com/', '').replace('http://github.com/', '')
    parts = clean_url.split('/')
    if len(parts) < 2:
        print(f"❌ Invalid GitHub repository format: {repo_url}")
        return False
        
    owner, repo = parts[0], parts[1].replace('.git', '')
    print(f"🌐 Fetching latest files from GitHub: {owner}/{repo}...")
    
    branches = ['main', 'master']
    updated_count = 0
    
    for filename in FILES_TO_UPDATE:
        downloaded = False
        for branch in branches:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"
            try:
                req = urllib.request.Request(raw_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    content = response.read()
                    with open(filename, 'wb') as f:
                        f.write(content)
                    print(f"  ✅ Updated: {filename}")
                    downloaded = True
                    updated_count += 1
                    break
            except Exception:
                continue
                
        if not downloaded:
            print(f"  ⚠️ Skipped / unchanged: {filename}")
            
    if updated_count > 0:
        print(f"\n🎉 Successfully updated {updated_count} files from GitHub!")
        return True
    else:
        print("\n❌ Could not download any files from that repository. Check the repo URL or branch name.")
        return False

def update_from_zip() -> bool:
    downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
    print(f"🔍 Searching for exported ZIP files in: {downloads_dir} ...")
    
    zip_files = glob.glob(os.path.join(downloads_dir, "*.zip")) + glob.glob("*.zip")
    
    # Filter by recent files or matching names
    candidates = []
    now = time.time()
    for zf in zip_files:
        try:
            mtime = os.path.getmtime(zf)
            fname = os.path.basename(zf).lower()
            # If created in last 4 hours or contains project keywords
            if (now - mtime < 14400) or any(k in fname for k in ['c7cb', 'instagram', 'bot', 'react', 'export']):
                candidates.append((mtime, zf))
        except Exception:
            pass
            
    if not candidates:
        print("❌ No recently downloaded ZIP found in your Downloads folder.")
        return False
        
    candidates.sort(reverse=True)
    latest_zip = candidates[0][1]
    print(f"📦 Found export ZIP: {os.path.basename(latest_zip)}")
    print(f"   Extracting files into bot directory...")
    
    updated_count = 0
    try:
        with zipfile.ZipFile(latest_zip, 'r') as z:
            for member in z.namelist():
                base_name = os.path.basename(member)
                if base_name in FILES_TO_UPDATE:
                    source = z.open(member)
                    target_path = os.path.join(os.getcwd(), base_name)
                    with open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    print(f"  ✅ Extracted: {base_name}")
                    updated_count += 1
                    
        if updated_count > 0:
            print(f"\n🎉 Successfully updated {updated_count} files from ZIP!")
            return True
    except Exception as e:
        print(f"❌ Error extracting ZIP: {e}")
        
    return False

def main():
    print_banner()
    repo_file = ".github_repo"
    repo_url = None
    
    if os.path.exists(repo_file):
        try:
            with open(repo_file, "r", encoding="utf-8") as f:
                repo_url = f.read().strip()
        except Exception:
            repo_url = None
            
    success = False
    
    if repo_url:
        print(f"📌 Found saved GitHub repository: {repo_url}")
        success = update_from_github(repo_url)
        
    if not success:
        print("\n" + "=" * 55)
        print("                HOW WOULD YOU LIKE TO UPDATE?")
        print("=" * 55)
        print("Option 1 (Zero-Click Sync): Enter your GitHub repo URL")
        print("           (Export from AI Studio top-right menu -> 'Export to GitHub')")
        print("Option 2 (1-Click ZIP): Press ENTER to auto-detect a downloaded ZIP")
        print("=" * 55)
        
        user_input = input("\nGitHub Repo URL (or press ENTER for ZIP detection): ").strip()
        
        if user_input:
            with open(repo_file, "w", encoding="utf-8") as f:
                f.write(user_input)
            print(f"💾 Saved repo URL to '{repo_file}' for future 1-click updates!")
            success = update_from_github(user_input)
        else:
            success = update_from_zip()
            
    if not success:
        print("\n❌ Update could not be completed.")
        print("💡 Quick manual update:")
        print("   1. In AI Studio, click top-right 'Export to ZIP'.")
        print("   2. Open the ZIP and copy main.py, ldplayer_automation.py, and easyearn_client.py")
        print("      directly into this folder.")
    else:
        print("\n" + "=" * 55)
        print("✅ UPDATE COMPLETE! Everything is up to date.")
        print("=" * 55)
        
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
