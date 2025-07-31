import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
from groq import Groq
import json
import os
import re
from ticket import create_work_package,get_work_package_by_id
from get_project_details import get_all_work_package_ids,get_all_work_package_title,get_all_work_package_description,get_work_package,update_work_package_status
from github import Github
from dotenv import load_dotenv
from back_email import start_backend
import base64

load_dotenv()
# Initialize Groq API client
client = Groq(api_key=os.getenv('GROQ_API_KEY'))  # Replace with your actual API key
st.set_page_config(layout="wide")
# Path to store user data
USER_DATA_FILE = "users.json"
col1,col2,col3,col4=st.columns([4,4,0.75,1])
# Function to load user data
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Function to save user data
def save_user_data(data):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(data, file)

# Initialize user data
if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data()
# Initialize current screen
if "screen" not in st.session_state:
    st.session_state.screen = "login"
if 'authenticated' not in st.session_state:
    st.session_state['authenticated']=False

# Function to switch screens
def set_screen(screen_name):
    st.session_state.screen = screen_name
    st.rerun()

# Function to communicate with Groq Cloud Llama 3 model
def get_llama3_response(prompt,task_type=None):
    model = os.getenv('model_name')

    messages = [
        {"role": "user", "content": prompt}
    ]
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=2500,
        top_p=1,
        stream=True,
        stop=None
    )
    response = ""
    for chunk in completion:
        response += chunk.choices[0].delta.content or ""
    return response


def display_user_profile(name, logo_url):
    st.markdown(
        f"""
        <style>
        .user-profile {{
            display: flex;
            justify-content: flex-end;
            align-items: center;
        }}
        .user-name {{
            margin-left: 10px;
            margin-right:10px;
            font-size: 18px;
            font-weight: bold;
            color: #333333;
        }}
        .user-logo img {{
            border-radius: 100%;
            width: 20px;
        }}
        </style>
        <div class="user-profile">
            <div class="user-name">{name}</div>
            <div class="user-logo">
                <img src="{logo_url}" alt="User Logo">
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
GITHUB_ACCESS_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN')
repo_owner = os.getenv('REPO_OWNER')
repo_name = os.getenv('REPO_NAME')
g = Github(GITHUB_ACCESS_TOKEN)

def fetch_branches(repo_name):
  
    """Fetch branches for a given repository."""
    repo = g.get_repo(f"{repo_owner}/{repo_name}")
    branches = [branch.name for branch in repo.get_branches()]
    return branches

def merge_to_git(repo_name,source_branch,target_branch,file_name,file_content,commit_message='Added New File',pr_title='Added New Feature'):
    # Replace these with your actual values
    # GITHUB_ACCESS_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN')
    REPO_NAME = f"{repo_owner}/{repo_name}"  # Example: "user/repo"
    SOURCE_BRANCH = source_branch
    TARGET_BRANCH = target_branch
    FILE_PATH = file_name  # Path to the file to add
    FILE_CONTENT = file_content
    COMMIT_MESSAGE = commit_message
    PR_TITLE = pr_title

    PR_BODY = "This PR includes the implementation of the new feature."
    # Authenticate with GitHub
    g = Github(GITHUB_ACCESS_TOKEN)
    # Get the repository
    repo = g.get_repo(REPO_NAME)
    try:
        # Get the default branch SHA to base the new branch on
        base_branch = repo.get_branch(TARGET_BRANCH)
        base_sha = base_branch.commit.sha
        # Create the source branch if it doesn't exist
        try:
            repo.get_branch(SOURCE_BRANCH)
            print(f"Branch '{SOURCE_BRANCH}' already exists.")
        except:
            repo.create_git_ref(ref=f"refs/heads/{SOURCE_BRANCH}", sha=base_sha)
            print(f"Created branch '{SOURCE_BRANCH}'.")
        # Add or update the file
        try:
            # Check if the file exists
            file = repo.get_contents(FILE_PATH, ref=SOURCE_BRANCH)
            repo.update_file(
                path=FILE_PATH,
                message=COMMIT_MESSAGE,
                content=FILE_CONTENT,
                sha=file.sha,
                branch=SOURCE_BRANCH,
            )
            print(f"Updated file '{FILE_PATH}' on branch '{SOURCE_BRANCH}'.")
        except Exception as e:
            print(e)
            # If file does not exist, create it
            repo.create_file(
                path=FILE_PATH,
                message=COMMIT_MESSAGE,
                content=FILE_CONTENT,
                branch=SOURCE_BRANCH,
            )
            print(f"Added file '{FILE_PATH}' to branch '{SOURCE_BRANCH}'.")
        # Create a Pull Request
        pr = repo.create_pull(
            title=PR_TITLE,
            body=PR_BODY,
            head=SOURCE_BRANCH,
            base=TARGET_BRANCH,
        )
        print(f"Pull Request created successfully: {pr.html_url}")
    except Exception as e:
        print(f"Error: {e}")
col01,col02,col03=st.columns([2,4,2])
if st.session_state.screen == "login":
    with col02:
        col6,col7,col8=st.columns([2,4,2])
        with col7:
            st.image("Neuronix_Logo_BG_1.png",use_container_width=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        col11,col12,col13=st.columns([2,3,4])
         # Add a flag to track login attempts
        if "login_attempted" not in st.session_state:
            st.session_state.login_attempted = False
        with col11:
            if st.button("Login",use_container_width=True):
                user_data = st.session_state.user_data
                if username in user_data and user_data[username]["password"] == password:
                    st.session_state.current_user = username
                    st.session_state['authenticated']=True
                    st.session_state.screen = "welcome"
                    st.rerun()
                else:
                    st.session_state['authenticated']=False
                    st.session_state.login_attempted = True
                    st.rerun()
        with col12:
            if st.button("Register Here..."):
                set_screen("register")
        if st.session_state.login_attempted:
            st.error("Invalid username or password!")

# Registration Screen
elif st.session_state.screen == "register":
    with col02:
        col6,col7,col8=st.columns([2,4,2])
        with col7:
            st.image("Neuronix_Logo_BG_1.png",use_container_width=True)
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        email = st.text_input("Email")
        
        if st.button("Sign Up"):
            user_data = st.session_state.user_data
            if new_username in user_data:
                st.error("Username already exists!")
            else:
                user_data[new_username] = {"password": new_password, "email": email}
                save_user_data(user_data)
                st.session_state.user_data = user_data
                st.success("Registration successful! Please log in.")
                set_screen("login")
        with col03: 
            if st.button("◄ Go to Login"):
                set_screen("login")
if st.session_state.screen == "welcome":
    selection = option_menu(
    menu_title=None,  # Hide menu title
    options=[
        'Task Blueprint ➔', 
        'Code Genesis ➔', 
        'Code Auditor ➔', 
        'GitFlow Hub'
    ],  # Define your tabs
    default_index=0 if 'active_tab' not in st.session_state else [
        'Task Blueprint ➔', 
        'Code Genesis ➔', 
        'Code Auditor ➔', 
        'GitFlow Hub'
    ].index(st.session_state['active_tab']),
    orientation="horizontal",
    styles={
        "container": {
            "padding": "0!important",
            "background-color": "#f8f9fa",  
            "border-radius": "8px",        
            "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)",  
        },
        "icon": {"display": "none"},  
        "nav": {
            "background-color": "#f8f9fa",  
            "border-radius": "8px",        
            "padding": "5px",              
        },
        "nav-link": {
            "font-size": "12px",          
            "font-weight": "600",         
            "color": "#000000",           
            "padding": "12px 20px",       
            "margin": "2px",              
            "text-transform": "uppercase",
            "border-radius": "8px",       
            "background-color": "#ffffff",  
            "border": "1px solid #cccccc",  
            "--hover-color": "#e9ecef",   
        },
        "nav-link-selected": {
            "background-color": "#616161",  
            "color": "#ffffff",             
            "border": "1px solid #616161",  
        },
    },
    )
    if selection=='Task Blueprint ➔':
        #st.snow()
        with col3:
            # Create a div with a unique id to style this specific button
            if st.button("Logout", key="logout",use_container_width=True):
                set_screen("login")
        with col4:
            # Example user information
            user_name = st.session_state.current_user
            user_logo_url = "data:image/png;base64,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"
            # Display the user profile
            display_user_profile(user_name, user_logo_url)
        coltb1,coltb2=st.columns([6,4])
        with coltb1:
            task_req=st.text_area('**Define your requirement:**',placeholder='Start defining your requirement in english here...',height=250)
            #ticket_creation_prompt=f"""Given the following task description{task_req}, generate a dictionary containing the fields `title`, `description`, `priority`, and `estimated_hours`. The `title` should summarize the task in one sentence, the `description` should provide a detailed explanation of the task, the `priority` should be one of ['Low', 'Medium', 'High', 'Critical'], and `estimated_hours` should be an approximate number of hours to complete the task. The outpur format should be title:, description:,prioroty:,estimated_time:"""
            ticket_creation_prompt=f""""Given the following task description: {task_req}, generate a structured response containing the following fields:  
                                    - `title`: A concise summary of the task in one sentence.  
                                    - `description`: A detailed explanation of the task.(don't include estimate hours and priority in description)
                                    - `priority`: One of the following values based on task urgency: ['Normal','Low','High','Immediate'].  
                                    - `estimated_hours`: An approximate number of hours required to complete the task.  
                                    Return the result in this format (without any additional text or code):  
                                    ```
                                    title: [Insert title here]  
                                    description: Insert description here
                                    priority: [Insert priority here]  
                                    estimated_hours: [Insert estimated time here]
                                    don't include estimate hours and priority in description
                                    ```"""
            create_ticket=st.button('Create')
        with coltb2:
            if create_ticket:
                st.write('')
                with st.container(border=True):
                    response_1 = get_llama3_response(ticket_creation_prompt)
                    parsed_response = response_1
                    # Regular expressions to extract each field
                    title_match = re.search(r"title:\s*(.+)", parsed_response)
                    description_match = re.search(r"description:\s*(.+)", parsed_response)
                    priority_match = re.search(r"priority:\s*(.+)", parsed_response)
                    estimated_hours_match = re.search(r"estimated_hours:\s*(\d+)", parsed_response)

                    # Extract and clean the results
                    title = title_match.group(1).strip() if title_match else None
                    description = description_match.group(1).strip() if description_match else None
                    priority = priority_match.group(1).strip() if priority_match else None
                    estimated_hours = int(estimated_hours_match.group(1)) if estimated_hours_match else None

                    ticket_dtls = {
                        "Title": title,
                        "Description": description,
                        "Priority": priority,
                        "Estimated Hour(s)": estimated_hours
                    }
                    prir_id={'Low':7,'Normal':8,'High':9,'Immediate':10}
                    work_package_id = create_work_package(
                        subject=ticket_dtls['Title'],
                        description= ticket_dtls['Description'],
                        type_id=1,  # Replace with your actual type ID (e.g., Task)
                        status_id=1,  
                        priority_id=prir_id[ticket_dtls['Priority']],  # Replace with the appropriate priority ID
                        assignee_id="kancharlaganesh47@gmail.com",
                        estimated_hours=ticket_dtls['Estimated Hour(s)']
                    )
                    if work_package_id:
                        ticket_dtls['Ticket_ID']=work_package_id
                    order = {'Ticket_ID': 1, 'Title': 2, 'Description': 3, 'Priority': 4, 'Estimated Hour(s)': 5}
                    for key in sorted(ticket_dtls, key=lambda x: order[x]):
                        st.write(f":red[{key}]:-:blue[{ticket_dtls[key]}]")
    if selection=='Code Genesis ➔':
        # Place the Logout button inside col3 with a unique container
        with col3:
            # Create a div with a unique id to style this specific button
            if st.button("Logout", key="logout",use_container_width=True):
                st.session_state['authenticated']=False
                set_screen("login")
        with col4:
            # Example user information
            user_name = st.session_state.current_user
            user_logo_url = "data:image/png;base64,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"
            # Display the user profile
            display_user_profile(user_name, user_logo_url)
        colcg1,colcg2,colcg3=st.columns([1.5,5,3.5])
        with colcg1:
            selected_wp_id=st.selectbox('**Select Ticket ID**',get_all_work_package_ids())
        #st.title(f"Hello, {st.session_state.current_user}! Welcome to the app.")
        # Option menu for tabs
        with colcg2:
            st.write('')
            with st.container(border=True,height=50):
                st.write('**Ticket Title:**',get_all_work_package_title(selected_wp_id))
        with colcg3:
            selected_tab = st.radio('',['Prompt to Code','Enhance Code'],horizontal=True)
        if st.session_state.screen == "welcome":
            if selected_tab == "Prompt to Code":
                col45,col46=st.columns([8,2])
                with col46:
                    language=st.selectbox('',['Python','Java','Scala','Pyspark'])
                with col45:
                    prompt = st.text_area("Enter your prompt for code generation:",value=get_all_work_package_description(selected_wp_id))
                    if st.button("Generate Code", key="generate_code"):
                        if prompt:
                            code_generation_prompt=f"""Generate code based on the following user query using {language} language. If language is not provided ny user use only that language otherwise write code in python only.
                            Respond only with the code in a code block enclosed by ``` at the beginning and end. 
                            Avoid any preambles, introductions, or explanations outside the code. 
                            If needed, provide concise explanations within the code as comments, but do not add any additional text outside the code block.
                            User Query: {prompt}"""
                            # Call the function to get response from Llama 3 model
                            response = get_llama3_response(code_generation_prompt, task_type="generate")
                            #st.markdown(response,unsafe_allow_html=True)
                            response=response.replace('```python','')
                            response=response.replace('```java','')
                            response=response.replace('```','')
                            response=response.replace('````','')
                            update_work_package_status(selected_wp_id,7)
                            st.code(response)
                        else:
                            st.warning("Please enter a prompt to generate code...!")

            elif selected_tab == "Enhance Code":
                colec1,colec2,colec3=st.columns([4.85,0.30,4.85])
                with colec1:
                    code_input = st.text_area("Paste your code here to enhance:",height=150)
                    enhance_code_prompt=f"""If this is my code {code_input} analyze it to suggest an optimized version. The analysis includes:
                                        Recognizing the functionality and purpose of your code.
                                        Providing an optimized version of the code, aiming for reduced complexity, better readability, and performance.
                                        Highlighting key differences between your original code and the optimized version as comments.
                                        """
                with colec2:
                    for _ in range(6):
                        st.write('')
                    st.write('**or**')
                with colec3:
                    st.write('')
                    st.write('')
                    with st.container(border=True,height=150):
                        file_to_enhance= st.file_uploader('**Upload File to Enhance**:',type=['py','java'])
                if st.button("Enhance Code"):
                    if code_input and file_to_enhance:
                        st.error('Either upload a File or Paste your code..!')
                    elif code_input:
                        st.markdown(get_llama3_response(enhance_code_prompt))
                    elif file_to_enhance:
                        if file_to_enhance is not None:
                            content = file_to_enhance.read().decode("utf-8")
                            enhance_code_prompt=f"""If this is my code {content} analyze it to suggest an optimized version if this is my task_description {get_all_work_package_description(get_work_package_by_id)}. The analysis includes:
                                        Recognizing the functionality and purpose of your code.
                                        Providing an optimized version of the code, aiming for reduced complexity, better readability, and performance.
                                        Highlighting key differences between your original code and the optimized version as comments.
                                        """
                            st.markdown(get_llama3_response(enhance_code_prompt))
                    else:
                        st.warning("Please paste your code to get suggestions...!")
    if selection=='Code Auditor ➔':
        # Place the Logout button inside col3 with a unique container
        with col3:
            # Create a div with a unique id to style this specific button
            if st.button("Logout", key="logout",use_container_width=True):
                set_screen("login")
        with col4:
            # Example user information
            user_name = st.session_state.current_user
            user_logo_url = "data:image/png;base64,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"
            # Display the user profile
            display_user_profile(user_name, user_logo_url)
        colci1,colci2=st.columns([3,7])
        colci10,colci20=st.columns([3,7])
        colci11,colci22,colci33=st.columns([4,2,4])
        with colci1:
            selected_wp_id_ci=st.selectbox('**Select Ticket ID**',get_all_work_package_ids())
            with st.container(border=True,height=90):
                st.write('**Ticket Title:**',get_all_work_package_title(selected_wp_id_ci))
        with colci2:
            for _ in range(2):
                st.write('')
            with st.container(border=True,height=140):
                file_to_review= st.file_uploader('**Upload File to Review**:',type=['py','java','scala'])
        # with colci22:
        #     review_btn=st.button('Review Code',use_container_width=True)
        if file_to_review is not None:
            review_content = file_to_review.read().decode("utf-8")  # Assuming text file
            code_review_prompt=f"""
            "Please review the following code {review_content} in all possible aspects:  
            1. **Syntax:** Identify and highlight any issues or improvements related to the programming language's syntax.  
            2. **Semantics:** Assess the correctness and clarity of the logic, ensuring it aligns with the language's semantics.  
            3. **Code Quality:** Evaluate best practices such as modularity, readability, maintainability, and adherence to standards.  
            4. **Efficiency:** Check for computational and memory efficiency, suggesting optimizations where applicable.  
            5. **Alignment with Task:** Assess if the code fulfills the described task or objective effectively and my task description is provided here {get_all_work_package_description(selected_wp_id_ci)}
            For each of these dimensions, provide a detailed evaluation and assign a score out of 10. Conclude with an overall review score for the code (out of 50), based on the weighted sum of all dimensions."  
            """
            #st.markdown(get_llama3_response(code_review_prompt))
            review_response = get_llama3_response(code_review_prompt)
            update_work_package_status(selected_wp_id_ci,13)
            #st.markdown(review_response)
            # Expected dimensions
            expected_dimensions = ["Syntax", "Semantics", "Code Quality", "Efficiency", "Alignment with Task"]

            # Extract individual dimension scores
            pattern = r"(\w+(?: \w+)*):\s*(\d+)/10"  # Matches 'Dimension: Score/10'
            matches = re.findall(pattern, review_response)
            #st.write("Extracted Matches:", matches)

            # Assign scores to expected dimensions
            review_scores = {dim: 0 for dim in expected_dimensions}  # Initialize with default scores
            for idx, dim in enumerate(expected_dimensions):
                if idx < len(matches):  # Ensure there's a match for this dimension
                    review_scores[dim] = int(matches[idx][1])  # Assign score

            # Extract overall score
            overall_pattern = r"Overall\sScore:\s(\d+)/100"  # Matches 'Overall Score: xx/100'
            overall_match = re.search(overall_pattern, review_response)
            if overall_match:
                review_scores["Overall"] = int(overall_match.group(1))
            else:
                # Calculate overall score as the average of dimensions
                review_scores["Overall"] = int(sum(review_scores[dim] for dim in expected_dimensions) * 2)

            # Display results
            #st.write("Review Scores:", review_scores)
            if review_scores:
                # Display individual scores in colci1
                with colci10:
                    for dimension, score in review_scores.items():
                        if "Overall" not in dimension:
                            st.metric(label=f"{dimension} Score", value=f"{score}/10")

                # Display overall score as a pie chart in colci2
                with colci20:
                    pie_chart_data = {
                        "Dimension": [key for key in review_scores.keys() if "Overall" not in key],
                        "Score": [value for key, value in review_scores.items() if "Overall" not in key]
                    }

                    fig = px.pie(
                        pie_chart_data, 
                        names="Dimension", 
                        values="Score", 
                        title=f"Review Score: {review_scores['Overall']}/100",
                        hole=0.4
                    )
                    st.plotly_chart(fig)
            with st.expander('Detailed Review Explanation'):
                    st.markdown(review_response)
    if selection=='GitFlow Hub':
        # Place the Logout button inside col3 with a unique container
        with col3:
            # Create a div with a unique id to style this specific button
            if st.button("Logout", key="logout",use_container_width=True):
                set_screen("login")
        with col4:
            # Example user information
            user_name = st.session_state.current_user
            user_logo_url = "data:image/png;base64,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"
            # Display the user profile
            display_user_profile(user_name, user_logo_url)
        colgh0,colgh01,colgh02,colgh03=st.columns([2.5,1,4,2.5])
        with colgh01:
            selected_wp_id_gh=st.selectbox('**Select Ticket ID**',get_all_work_package_ids())
            with colgh02:
                st.write('')
                with st.container(border=True,height=60):
                    st.write('**Ticket Title:**',get_all_work_package_title(selected_wp_id_gh))
        colgh1,colgh2,colgh3,colgh31=st.columns(4)
        branches = fetch_branches(repo_name)
        
        with colgh1:
            repo_name = st.selectbox('**Select Repository:**', repo_name)
            
        with colgh2:
            source_branch = st.selectbox('**Select Source Branch:**', branches)

            
        with colgh3:
            target_branch=st.selectbox('**Select Target Branch:**',branches)

        colgh4,colgh5,colgh51=st.columns([2.5,5,2.5])
        with colgh31:
            file_name=st.text_input('**Enter File Name:**',value='new_file.txt',placeholder='Enter file name with extension (file.py)...')
        with colgh5:
            file_to_raise_pr= st.file_uploader('**Upload File to Review**:',type=['py','java','scala'],key='file_to_raise_pr')
        if file_to_raise_pr is not None:
            global file_content
            file_content=file_to_raise_pr.read().decode("utf-8")
        colgh6,colgh7,colgh8=st.columns([4,2,4])
        with colgh7:
            st.write('')
            if st.button('Deploy Code',use_container_width=True):
                merge_to_git(repo_name,source_branch,target_branch,file_name,file_content,commit_message='Added New File',pr_title=f'Added New Feature for Work Package {selected_wp_id_gh}')
                st.success('Code Deployed Successfully')
                start_backend(selected_wp_id_gh)
                # update_work_package_status(selected_wp_id_gh,12)
                st.balloons()
