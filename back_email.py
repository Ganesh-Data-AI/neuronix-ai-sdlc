import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import threading
from get_project_details import get_all_work_package_ids,get_all_work_package_title,get_all_work_package_description,get_work_package,update_work_package_status
import re  # Importing regex for extracting the work package ID
import os

def extract_work_package_id_from_title(pr_title):
    """Extract the work package ID from the PR title."""
    match = re.search(r"Work Package (\d+)", pr_title)  # Search for "Work Package <number>"
    if match:
        return int(match.group(1))  # Return the number part as an integer
    return None  # Return None if no match is found

# Define your GitHub details
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_OWNER = os.getenv('GITHUB_OWNER')
GITHUB_REPO = os.getenv('GITHUB_REPO')

# Email setup
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = os.getenv('SMTP_PORT')

pr_numbers_to_check = []
sent_pr_numbers = []  # Track sent PRs


def get_pull_requests(owner, repo, token):
    """Retrieve the list of PRs for a given repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all"
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        prs = response.json()
        return prs
    else:
        print(f"Failed to retrieve pull requests: {response.status_code}")
        return []

def get_pr_details(owner, repo, pr_number, token):
    """Retrieve the details of a pull request."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        pr = response.json()
        return pr
    else:
        print(f"Failed to retrieve PR #{pr_number}: {response.status_code}")
        return None

def get_pr_files(owner, repo, pr_number, token):
    """Retrieve the files changed in a pull request."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        files = response.json()
        return files
    else:
        print(f"Failed to retrieve files for PR #{pr_number}: {response.status_code}")
        return []

def send_email(subject, body):
    """Send an email notification."""
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAIL
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.as_string())
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_and_send_email_for_merged_prs(selected_wp_id_gh):
    """Check the PRs and send email if they are merged."""
    global pr_numbers_to_check, sent_pr_numbers

    prs = get_pull_requests(GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN)
    
    for pr in prs:
        pr_number = pr['number']
        if pr_number not in pr_numbers_to_check and pr_number not in sent_pr_numbers:
            pr_numbers_to_check.append(pr_number)

    for pr_number in pr_numbers_to_check[:]:  # Iterate through PRs to check their merge status
        if pr_number in sent_pr_numbers:
            pr_numbers_to_check.remove(pr_number)
            continue  # Skip if already sent email for this PR
        
        pr_details = get_pr_details(GITHUB_OWNER, GITHUB_REPO, pr_number, GITHUB_TOKEN)
        
        if pr_details:
            pr_title = pr_details['title']
            pr_url = pr_details['html_url']
            is_merged = pr_details.get('merged', False)
            merged_by = pr_details.get('merged_by', {}).get('login', 'Unknown') if is_merged else 'N/A'
            merged_at = pr_details.get('merged_at', 'N/A') if is_merged else 'N/A'
            source_branch = pr_details['head']['ref']
            target_branch = pr_details['base']['ref']
            if is_merged:  # If PR is merged
                # Get changed files
                files = get_pr_files(GITHUB_OWNER, GITHUB_REPO, pr_number, GITHUB_TOKEN)
                file_changes = '\n'.join([f"- {file['filename']}" for file in files]) if files else "No files changed"
                work_package_id = extract_work_package_id_from_title(pr_title)
                subject = f"Pull Request #{pr_number} Merged: {pr_title}"
                body = (f"Dear Team,\n\n"
                        f"We are pleased to inform you that Pull Request #{pr_number} titled '{pr_title}' has been successfully merged.\n\n"
                        f"PR Details:\n"
                        f"PR Title: {pr_title}\n"
                        f"PR URL: {pr_url}\n"
                        f"Merged By: {merged_by}\n"
                        f"Merged At: {merged_at}\n\n"
                        f"Source Branch: {source_branch}\n"
                        f"Target Branch: {target_branch}\n\n"
                        f"Files Changed:\n{file_changes}\n\n"
                        f"Please review and proceed as needed.\n\n"
                        f"Best Regards,\n"
                        f"Your Automated PR Monitoring System")
                
                send_email(subject, body)
                sent_pr_numbers.append(pr_number)
                pr_numbers_to_check.remove(pr_number)  # Remove PR from the check list once email is sent
                
                # Now update the work package status after sending the email
                update_work_package_status(work_package_id, 12)  # Assuming 13 is the status indicating PR is merged
                
            else:
                print(f"PR #{pr_number} is not yet merged.")
        else:
            print(f"PR #{pr_number} details not found. No email sent.")

def check_for_prs_periodically(selected_wp_id_gh, interval_seconds):
    """Run the email check at regular intervals."""
    while True:
        print("Checking for merged PRs...")
        check_and_send_email_for_merged_prs(selected_wp_id_gh)  
        
        print(f"Waiting for {interval_seconds} seconds before the next check...")
        time.sleep(interval_seconds)

def start_backend_monitoring(selected_wp_id_gh):
    check_for_prs_periodically(selected_wp_id_gh, 60)  # Run every 60 seconds

def start_backend(selected_wp_id_gh):
    backend_thread = threading.Thread(target=start_backend_monitoring, args=(selected_wp_id_gh,), daemon=True)
    backend_thread.start()
