#!/usr/bin/env python3
"""
Test script to verify Penpot API credentials and list projects.
"""

import os

from dotenv import load_dotenv

from penpot_mcp.api.penpot_api import PenpotAPI


def test_credentials():
    """Test Penpot API credentials and list projects."""
    load_dotenv()
    
    api_url = os.getenv("PENPOT_API_URL")
    username = os.getenv("PENPOT_USERNAME") 
    password = os.getenv("PENPOT_PASSWORD")
    
    if not all([api_url, username, password]):
        print("❌ Missing credentials in .env file")
        print("Required: PENPOT_API_URL, PENPOT_USERNAME, PENPOT_PASSWORD")
        return False
    
    print(f"🔗 Testing connection to: {api_url}")
    print(f"👤 Username: {username}")
    
    try:
        api = PenpotAPI(api_url, debug=False, email=username, password=password)
        
        print("🔐 Authenticating...")
        token = api.login_with_password()
        print("✅ Authentication successful!")
        
        print("📁 Fetching projects...")
        projects = api.list_projects()
        
        if isinstance(projects, dict) and "error" in projects:
            print(f"❌ Failed to list projects: {projects['error']}")
            return False
            
        print(f"✅ Found {len(projects)} projects:")
        for i, project in enumerate(projects, 1):
            if isinstance(project, dict):
                name = project.get('name', 'Unnamed')
                project_id = project.get('id', 'N/A')
                team_name = project.get('team-name', 'Unknown Team')
                print(f"  {i}. {name} (ID: {project_id}) - Team: {team_name}")
            else:
                print(f"  {i}. {project}")
        
        # Test getting project files if we have a project
        if projects and isinstance(projects[0], dict):
            project_id = projects[0].get('id')
            if project_id:
                print(f"\n📄 Testing project files for project: {project_id}")
                try:
                    files = api.get_project_files(project_id)
                    print(f"✅ Found {len(files)} files:")
                    for j, file in enumerate(files[:3], 1):  # Show first 3 files
                        if isinstance(file, dict):
                            print(f"  {j}. {file.get('name', 'Unnamed')} (ID: {file.get('id', 'N/A')})")
                        else:
                            print(f"  {j}. {file}")
                    if len(files) > 3:
                        print(f"  ... and {len(files) - 3} more files")
                except Exception as file_error:
                    print(f"❌ Error getting files: {file_error}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_credentials()
    exit(0 if success else 1)