import requests
from get_project_details import *
from requests.auth import HTTPBasicAuth
import streamlit as st
# Constants
PROJECT_ID = "sample"  # Replace with your actual project ID
BASE_URL = f"https://neuronix-15.openproject.com/api/v3/projects/{PROJECT_ID}/work_packages"
API_KEY = os.getenv('OPEN_PROJECT_API_KEY')
def create_work_package(subject, description, type_id, status_id, priority_id, assignee_id,estimated_hours):
    headers = {
        "Content-Type": "application/json"
    }
    # Define the payload for the new work package
    payload = {
        "subject": subject,
        "description": {
            "format": "textile",
            "raw": description
        },
        "estimatedTime": f"PT{int(estimated_hours)}H",  # ISO 8601 format for duration
        "_links": {
            "type": {
                "href": f"/api/v3/types/{type_id}"
            },
            "status": {
                "href": f"/api/v3/statuses/{status_id}"
            },
            "priority": {
                "href": f"/api/v3/priorities/{priority_id}"
            },
            "assignee": {
                "href": f"/api/v3/users/{assignee_id}"  # Replace with a valid numeric user ID
            }
        }
    }
    # Make the POST request to create the work package with Basic Auth
    response = requests.post(BASE_URL, headers=headers, json=payload, auth=HTTPBasicAuth('apikey', API_KEY))
    if response.status_code == 201:
        work_package = response.json()
        work_package_id = work_package.get("id")
        print("Work package created successfully")
        print("Work package ID:", work_package_id)
        return work_package_id
    else:
        print("Failed to create work package:", response.status_code, response.text)
        return None
def get_work_package_by_id(work_package_id):
    headers = {
        "Content-Type": "application/json"
    }
    """Fetch details of a specific work package by ID."""
    response = requests.get(BASE_URL, headers=headers, auth=HTTPBasicAuth('apikey', API_KEY))
    if response.status_code == 200:
        work_packages = response.json()["_embedded"]["elements"]
        print(f"Searching for Work Package ID: {work_package_id}")
        # Filter for the specific work package
        for wp in work_packages:
            if wp["id"] == work_package_id:
                #print("\nWork Package Found:")
                # print(f"ID: {wp['id']}")
                # print(f"Subject: {wp['subject']}")
                # print(f"Description: {wp.get('description', {}).get('raw', 'No description')}")
                # print(f"Status: {wp['_links']['status']['title']}")
                # print(f"Priority: {wp['_links']['priority']['title']}")
                # print(f"Assignee: {wp['_links'].get('assignee', {}).get('title', 'Unassigned')}")
                # print(f"Type: {wp['_links']['type']['title']}")
                # print(f"Project: {wp['_links']['project']['title']}")
                return wp
        print("Work package not found.")
    else:
        print("Failed to fetch work packages:", response.status_code, response.text)
