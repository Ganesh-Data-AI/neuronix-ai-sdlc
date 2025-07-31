import streamlit as st 
import requests
import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
load_dotenv()
# Constants 
PROJECT_ID = "sample"  # Replace with your actual project ID
BASE_URL = f"https://neuronix-15.openproject.com/api/v3/projects/{PROJECT_ID}/work_packages"
BASE_URL_1="https://neuronix-15.openproject.com/api/v3"
API_KEY = os.getenv('OPEN_PROJECT_API_KEY')
# Headers for API calls
HEADERS = {
    "Content-Type": "application/json"
}

def get_all_work_package_ids():
    """Fetch all work packages associated with the user and exclude those in closed state."""
    response = requests.get(f"{BASE_URL}", headers=HEADERS, auth=HTTPBasicAuth('apikey', API_KEY))
    if response.status_code == 200:
        work_packages = response.json()["_embedded"]["elements"]
        #print(f"Found {len(work_packages)} work packages:")
        # Filter out work packages with the closed state (state ID = 12)
        filtered_wp_ids = []
        for wp in work_packages:
            state_id = int(wp["_links"]["status"]["href"].split("/")[-1])  # Extract state ID from the href
            if state_id != 12:  # Exclude closed state
                filtered_wp_ids.append(wp['id'])
        return filtered_wp_ids
    else:
        print("Failed to fetch work packages:", response.status_code, response.text)

    # """Fetch all work packages associated with the user."""
    # # url = f"{BASE_URL}/work_packages"
    # response = requests.get(BASE_URL, headers=HEADERS, auth=HTTPBasicAuth('apikey', API_KEY))
    # if response.status_code == 200:
    #     work_packages = response.json()["_embedded"]["elements"]
    #     print(f"Found {len(work_packages)} work packages:")
    #     wp_ids=[]
    #     for wp in work_packages:
    #         wp_ids.append(wp['id'])
    #     return wp_ids
    # else:
    #     print("Failed to fetch work packages:", response.status_code, response.text)

def get_all_work_package_title(work_package_id):
    """Fetch all work packages associated with the user."""
    # url = f"{BASE_URL}/work_packages"
    response = requests.get(BASE_URL, headers=HEADERS, auth=HTTPBasicAuth('apikey', API_KEY))
    if response.status_code == 200:
        work_packages = response.json()["_embedded"]["elements"]
        #print(f"Found {len(work_packages)} work packages:")
        wp_subjects=[]
        for wp in work_packages:
            if wp["id"] == work_package_id:
                # print("\nWork Package Found:")
                # print(f"ID: {wp['id']}")
                return wp['subject']
        return wp_subjects
    else:
        print("Failed to fetch work packages:", response.status_code, response.text)


def get_all_work_package_description(work_package_id):
    """Fetch all work packages associated with the user."""
    # url = f"{BASE_URL}/work_packages"
    response = requests.get(BASE_URL, headers=HEADERS, auth=HTTPBasicAuth('apikey', API_KEY))
    if response.status_code == 200:
        work_packages = response.json()["_embedded"]["elements"]
        #print(f"Found {len(work_packages)} work packages:")
        wp_subjects=[]
        for wp in work_packages:
            if wp["id"] == work_package_id:
                # print("\nWork Package Found:")
                # print(f"ID: {wp['id']}")
                return wp.get('description', {}).get('raw', 'No description')
        return wp_subjects
    else:
        print("Failed to fetch work packages:", response.status_code, response.text)

def get_work_package(work_package_id):
    """Retrieve a work package by its ID."""
    url = f"{BASE_URL_1}/work_packages/{work_package_id}"
    response = requests.get(url, headers=HEADERS, auth=HTTPBasicAuth('apikey', API_KEY))
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve work package:", response.status_code, response.text)
        return None

def update_work_package_status(work_package_id, new_status_id=1):
    """Update the status of an existing work package."""
    # Fetch the latest work package details
    work_package = get_work_package(work_package_id)
    if not work_package:
        print("Work package not found, cannot update.")
        return
    # Extract lockVersion
    lock_version = work_package.get("lockVersion")
    if lock_version is None:
        print("Failed to retrieve lockVersion for the work package.")
        return
    # Prepare the payload for updating the status
    payload = {
        "lockVersion": lock_version,
        "_links": {
            "status": {
                "href": f"/api/v3/statuses/{new_status_id}"
            }
        }
    }
    # Make the PATCH request to update the status
    url = f"{BASE_URL_1}/work_packages/{work_package_id}"
    response = requests.patch(url, headers=HEADERS, json=payload, auth=HTTPBasicAuth('apikey', API_KEY))
    if response.status_code == 200:
        print("Work package updated successfully:", response.json())
    else:
        print("Failed to update work package status:", response.status_code, response.text)
