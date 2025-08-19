#!/usr/bin/env python3
import os
import re

# Read the file
with open('/app/test_result.md', 'r') as file:
    content = file.read()

# Update Appointment Scheduling System status
content = content.replace(
    '  - task: "Appointment Scheduling System"\n    implemented: true\n    working: false\n    file: "/app/backend/server.py"\n    stuck_count: 0\n    priority: "high"\n    needs_retesting: true',
    '  - task: "Appointment Scheduling System"\n    implemented: true\n    working: true\n    file: "/app/backend/server.py"\n    stuck_count: 0\n    priority: "high"\n    needs_retesting: false'
)

# Update Patient Communications System status
content = content.replace(
    '  - task: "Patient Communications System"\n    implemented: true\n    working: "NA"\n    file: "/app/backend/server.py"\n    stuck_count: 0\n    priority: "high"\n    needs_retesting: true',
    '  - task: "Patient Communications System"\n    implemented: true\n    working: false\n    file: "/app/backend/server.py"\n    stuck_count: 0\n    priority: "high"\n    needs_retesting: false'
)

# Add status history for Patient Communications System
pattern = re.compile(r'  - task: "Patient Communications System".*?status_history:\n(.*?)(\n\n|\Z)', re.DOTALL)
match = pattern.search(content)
if match:
    status_history = match.group(1)
    new_status_history = status_history + '      - working: false\n        agent: "testing"\n        comment: "Partially working. Successfully tested template initialization and creation. The POST /api/communications/init-templates endpoint works correctly and initializes message templates. However, there are issues with: 1) GET /api/communications/templates - Returns 500 Internal Server Error, 2) POST /api/communications/send - Has issues with template variable processing. The message sending functionality works when using a manually created template, but the template variable processing needs to be fixed."\n'
    content = content.replace(status_history, new_status_history)

# Write the updated content back to the file
with open('/app/test_result.md', 'w') as file:
    file.write(content)

print("Updated test_result.md successfully")