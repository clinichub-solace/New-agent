#!/usr/bin/env python3
"""
ClinicHub Frontend Architecture Fix Script
Fixes all axios usage issues and API path problems
"""

import re
import os

def fix_app_js():
    """Fix all axios references in App.js to use the configured api instance"""
    file_path = "/app/frontend/src/App.js"
    
    print("🔧 Fixing App.js axios references...")
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Remove duplicate environment variable definitions
    content = re.sub(
        r'// Dynamic API configuration.*?\n.*?const API = .*?\n',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Replace all axios.get/post/put/delete with api.get/post/put/delete
    content = re.sub(r'axios\.(get|post|put|delete)', r'api.\1', content)
    
    # Replace URL construction patterns
    # ${API}/endpoint -> /endpoint
    content = re.sub(r'\$\{API\}(/[^`\'"\s\)]+)', r'\1', content)
    
    # Remove API variable references
    content = re.sub(r'const API = .*?\n', '', content)
    content = re.sub(r'const BACKEND_URL = .*?\n', '', content)
    
    with open(file_path, 'w') as file:
        file.write(content)
    
    print("✅ App.js fixed")

def fix_login_page():
    """Fix LoginPage.js if it has similar issues"""
    file_path = "/app/frontend/src/components/LoginPage.js"
    
    if not os.path.exists(file_path):
        return
    
    print("🔧 Fixing LoginPage.js...")
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Check if it imports axios directly
    if 'import axios from "axios"' in content:
        content = content.replace('import axios from "axios"', 'import api from "../api/axios"')
        content = re.sub(r'axios\.(get|post|put|delete)', r'api.\1', content)
        content = re.sub(r'\$\{.*?\}(/[^`\'"\s\)]+)', r'\1', content)
        
        with open(file_path, 'w') as file:
            file.write(content)
        
        print("✅ LoginPage.js fixed")

def verify_axios_config():
    """Verify the axios configuration is correct"""
    file_path = "/app/frontend/src/api/axios.js"
    
    print("🔍 Verifying axios configuration...")
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    if 'baseURL: BACKEND_URL' in content and 'process.env.REACT_APP_BACKEND_URL' in content:
        print("✅ Axios configuration looks correct")
    else:
        print("⚠️ Axios configuration may need attention")

def main():
    """Main execution"""
    print("🚀 ClinicHub Frontend Architecture Fix")
    print("=====================================")
    
    fix_app_js()
    fix_login_page()
    verify_axios_config()
    
    print("\n🎉 Frontend architecture fixes completed!")
    print("🔄 Please restart the frontend service to apply changes")

if __name__ == "__main__":
    main()