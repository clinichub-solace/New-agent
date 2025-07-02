#!/usr/bin/env python3
"""
Script to fix MongoDB queries by adding {"_id": 0} projection to avoid ObjectId serialization issues.
This script will update all find_one and find operations in the server.py file that are missing the projection.
"""

import re

def fix_mongodb_queries():
    with open('/app/backend/server.py', 'r') as f:
        content = f.read()
    
    # Pattern 1: find_one({"id": variable}) without projection
    pattern1 = r'find_one\(\{"id": ([^}]+)\}\)'
    replacement1 = r'find_one({"id": \1}, {"_id": 0})'
    
    # Pattern 2: find_one({"patient_id": variable}) without projection
    pattern2 = r'find_one\(\{"patient_id": ([^}]+)\}\)'
    replacement2 = r'find_one({"patient_id": \1}, {"_id": 0})'
    
    # Pattern 3: find_one({"category_id": variable}) without projection
    pattern3 = r'find_one\(\{"category_id": ([^}]+)\}\)'
    replacement3 = r'find_one({"category_id": \1}, {"_id": 0})'
    
    # Pattern 4: find(query).sort() operations without projection
    pattern4 = r'find\(([^)]+)\)\.sort\('
    replacement4 = r'find(\1, {"_id": 0}).sort('
    
    # Apply fixes
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Skip lines that already have projection
        if '{"_id": 0}' in line:
            fixed_lines.append(line)
            continue
            
        # Apply pattern replacements
        line = re.sub(pattern1, replacement1, line)
        line = re.sub(pattern2, replacement2, line)
        line = re.sub(pattern3, replacement3, line)
        
        # Special handling for find operations with complex queries
        if 'find(' in line and '.sort(' in line and '{"_id": 0}' not in line:
            # Extract the find part and add projection
            find_match = re.search(r'find\(([^)]+)\)', line)
            if find_match:
                query = find_match.group(1)
                # Add projection
                new_find = f'find({query}, {{"_id": 0}})'
                line = line.replace(f'find({query})', new_find)
        
        fixed_lines.append(line)
    
    # Write back the fixed content
    with open('/app/backend/server.py', 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    print("MongoDB queries fixed successfully!")

if __name__ == "__main__":
    fix_mongodb_queries()