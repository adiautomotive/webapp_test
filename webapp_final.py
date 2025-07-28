import streamlit as st
from openai import OpenAI
import json
from datetime import datetime
import os
import pandas as pd
import io

# ------------------------
# Constants
# ------------------------
ADMIN_PASSWORD = "admin123"
CHAT_LOGS_FOLDER = "chat_logs"

# ------------------------
# ChatGPT API Setup
# ------------------------
try:
    # It is recommended to use Streamlit secrets for your API key
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    # This will prevent the app from crashing if the API key is not set
    client = None
    st.warning("OpenAI API key not found in Streamlit secrets. Chat functionality will be disabled. Please set OPENAI_API_KEY in .streamlit/secrets.toml")

# ------------------------
# Main Navigation Controller
# ------------------------
def main():
    if 'page' not in st.session_state:
        st.session_state.page = 0

    # Page routing dictionary
    pages = {
        0: welcome_page, # New Welcome Page (Consent)
        1: survey_page, # Demographics and initial SAM
        2: personality_and_ai_survey_page, # Personality, AI Trust/Creativity, Attention Check
        3: page2, # Instructions
        4: page3, # Chat page
        5: page4, # Summary
        6: feedback_page, # Post-task feedback and final SAM
        7: page5, # Thank You page
        99: admin_view
    }
    
    page_function = pages.get(st.session_state.page)
    if page_function:
        page_function()
    else:
        st.session_state.page = 0 # Default to first page if state is invalid
        welcome_page() # Use welcome_page as the default


# ------------------------
# Helper for Next Button (positioned bottom right)
# ------------------------
def next_button(current_page, next_page, label="Next", key="next_page_btn"):
    # Custom CSS for button positioning
    st.markdown(
        """
        <style>
        .stButton button {
            display: block;
            margin-left: auto;
            margin-right: 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    if st.button(label, key=key):
        st.session_state.page = next_page
        st.rerun()

# ------------------------
# Chat History Persistence
# ------------------------
def save_chat_to_file():
    prolific_id = st.session_state.get("prolific_id", "anonymous")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(CHAT_LOGS_FOLDER, exist_ok=True)
    filename = f"chat_{prolific_id}_{timestamp}.json"

    data = {
        "prolific_id": prolific_id,
        "timestamp": timestamp,
        "survey_responses": st.session_state.get("survey_responses", {}),
        "chat_history": st.session_state.get("chat_history", []),
        "summary": st.session_state.get("summary_text", ""),
        "feedback": st.session_state.get("feedback_responses", {})
    }

    file_path = os.path.join(CHAT_LOGS_FOLDER, filename)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# ------------------------
# Page 0: Welcome Page with Consent
# ------------------------
def welcome_page():
    st.title("Welcome to the Research Study!")
    st.header("Consent To Be Part Of A Research Study")
    
    st.subheader("NAME OF STUDY AND RESEARCHERS")
    st.markdown("---")
    st.markdown("**Title of Project:** Investigating Human-AI Creative Collaboration")
    st.markdown("**Principal Investigator:** Dr. Areen Alsaid, Assistant Professor, University of Michigan-Dearborn")
    st.markdown("**Study Team Members:** Nishthaa Lekhi, Masters Student, University of Michigan-Dearborn")
    st.markdown("---")
    
    st.subheader("GENERAL INFORMATION")
    st.write("You are invited to participate in a research study exploring how people engage in creative collaboration with AI systems like ChatGPT.")
    st.write("This study aims to understand how ideas develop in back-and-forth conversations between humans and AI, and how such interactions shape the creative process and outcomes.")

    st.subheader("If you agree to take part in this study, you will be asked to:")
    st.markdown("- Complete a brief pre-activity survey.")
    st.markdown("- Take part in a creative writing task with ChatGPT. You’ll interact with the AI by exchanging ideas and building a fictional scenario together.")
    st.markdown("- Complete a post-activity survey, which will ask for feedback on the experience and your perception of the co-creative process.")

    st.subheader("Data Collection and Privacy")
    st.markdown("- Your conversation with ChatGPT will be saved and securely stored in a Streamlit-hosted research database.")
    st.markdown("- These conversations will be accessible only to the study team and will be reviewed for analysis.")
    st.markdown("- If any identifying information is present in your responses, it will be removed during data cleaning.")
    st.markdown("- All data from the surveys will be collected and stored on a Streamlit cloud.")
    st.markdown("- This information will include your response regarding your demographics, personality, and post-activity reflections.")
    st.markdown("- No identifying information will be stored beyond the duration of the study, and no identifiable data will be shared outside the study team.")
    st.markdown("- Data may be used in academic publications or presentations, but only in aggregate or anonymized form.")

    st.write("The insights from this research will help us better understand how AI can support or shape creativity in collaborative settings, and how humans perceive AI as a creative partner.")
    st.write("There are no known risks or discomforts associated with participating in this study.")
    st.write("Your participation is entirely voluntary. You are free to withdraw at any point without penalty.")
    st.write("You may also choose not to answer any specific questions or discontinue the creative task at any time.")
    st.write("Information collected from this study may be used in future research or publications, but your identity will remain confidential and no identifying information will be shared.")

    st.subheader("Contact Information")
    st.write("If you have any questions about this research, please contact the Principal Investigator, Nishthaa Lekhi, at nlekhi@umich.edu.")
    st.write("You may also reach out to the faculty advisor, Dr. Areen Alsaid at alsaid@Umich.edu.")
    
    st.markdown("---")

    consent_agreed = st.checkbox("I have read and understand the above information and consent to participate in this research study.", key="consent_checkbox")
    
    login_type = st.radio("Login as:", ["Participant", "Admin"], horizontal=True, key="login_type_radio")

    if login_type == "Participant":
        with st.form("prolific_id_form"):
            new_id = st.text_input("Enter your Prolific ID:", key="prolific_id_input_form")
            submitted = st.form_submit_button("Start Survey")
            if submitted:
                if consent_agreed:
                    if new_id and new_id.strip() != "":
                        st.session_state.prolific_id = new_id.strip()
                        st.session_state.page = 1
                        st.rerun()
                    else:
                        st.error("Please enter your Prolific ID to proceed.")
                else:
                    st.error("You must agree to the consent form to proceed.")
    else: # Admin login
        with st.form("admin_login_form"):
            admin_password = st.text_input("Enter Admin Password:", type="password", key="admin_password_input")
            if st.form_submit_button("Login"):
                if admin_password == ADMIN_PASSWORD:
                    st.session_state.page = 99
                    st.rerun()
                else:
                    st.error("Incorrect password")

# ------------------------
# Page 1: Pre-Activity Survey
# ------------------------
def survey_page():
    st.title("University of Michigan Research Survey")
    
    with st.form("pre_chat_survey_form"):
        responses = {}
        
        responses['age'] = st.number_input("How old are you?", min_value=1, max_value=120, step=1, key="age_input", value=None, placeholder="Enter age")
        
        gender_options = ["- Please select -", "Male", "Female", "Non-binary / third gender", "Prefer not to say"]
        selected_gender = st.radio("Which gender do you identify with?", gender_options, index=0, key="gender_radio")
        responses['gender'] = None if selected_gender == gender_options[0] else selected_gender

        education_options = ["- Please select -", "Highschool", "Bachelor's Degree", "Master's degree", "Doctorate", "Other"]
        selected_education = st.radio("What is the highest level of education that you have completed?", education_options, index=0, key="education_radio")
        if selected_education == education_options[0]:
            responses['education'] = None
        else:
            responses['education'] = selected_education
            if responses['education'] == "Other":
                responses['education_other'] = st.text_input("Please specify your education level:", key="education_other_input")
            else:
                responses['education_other'] = ""
        
        responses['religion'] = st.text_input("Which religion do you align with, if any? (Optional)", key="religion_input")

        ai_familiarity_options = ["- Please select -", "Not familiar", "Somewhat familiar", "Very familiar"]
        selected_ai_familiarity = st.radio("How familiar are you with AI tools like ChatGPT?", ai_familiarity_options, index=0, key="ai_familiarity_radio")
        responses['experience_with_ai'] = None if selected_ai_familiarity == ai_familiarity_options[0] else selected_ai_familiarity

        creative_writing_options = ["- Please select -", "Never", "Sometimes", "Often"]
        selected_creative_writing = st.radio("How often do you engage in creative writing (e.g., stories, blogs)?", creative_writing_options, index=0, key="creative_writing_radio")
        responses['creative_writing_frequency'] = None if selected_creative_writing == creative_writing_options[0] else selected_creative_writing
        
        st.markdown("---")
        st.subheader("Block 2: Current Emotional State (SAM)")

        st.markdown("""
        We'd like to know how you're feeling right now. Please use the Self-Assessment Manikin (SAM) graphic below to rate your current emotional state.
        * **Valence** (top row): How pleasant or unpleasant you feel.
        * **Arousal** (bottom row): How calm or excited you feel.
        """)
        
        if os.path.exists("images/SAM Model.jpeg"):
            st.image("images/SAM Model.jpeg", caption="Self-Assessment Manikin (SAM)", use_container_width=True)
        else:
            st.warning("SAM Model image not found. Make sure it's in an 'images' subfolder.")

        responses['valence'] = st.slider("Valence (Unpleasant ← → Pleasant)", 1, 9, 5, key="valence_slider")
        responses['arousal'] = st.slider("Arousal (Calm ← → Excited)", 1, 9, 5, key="arousal_slider")
        
        submitted = st.form_submit_button("Next")
        if submitted:
            if responses.get('age') is None or responses.get('age', 0) <= 0:
                st.error("Please enter your age.")
            elif responses.get('gender') is None:
                st.error("Please select your gender.")
            elif responses.get('education') is None:
                st.error("Please select your highest level of education.")
            elif responses.get('experience_with_ai') is None:
                st.error("Please indicate your familiarity with AI tools.")
            elif responses.get('creative_writing_frequency') is None:
                st.error("Please indicate how often you engage in creative writing.")
            elif responses.get('education') == "Other" and not responses.get('education_other', '').strip():
                st.error("Please specify your education level.")
            else:
                st.session_state.survey_responses = responses
                st.session_state.page = 2
                st.rerun()

# ------------------------
# Page 2: Personality and AI Survey
# ------------------------
def personality_and_ai_survey_page():
    st.title("Follow-up Survey")

    st.markdown("""
        <style>
            div.stRadio p { display: none !important; }
            div[data-testid="stHorizontalRadio"] { display: flex; justify-content: space-around; align-items: center; width: 100%; }
            div[data-testid="stHorizontalRadio"] > label { display: flex; justify-content: center; align-items: center; margin: 0 !important; flex-grow: 1; }
            .matrix-header-text { text-align: center; font-weight: bold; font-size: 0.8em; white-space: normal !important; }
            .matrix-row-question { display: flex; align-items: center; min-height: 60px; padding-right: 5px; }
            .stColumns > div[data-testid="stVerticalBlock"] { gap: 0.2rem; }
        </style>
    """, unsafe_allow_html=True)

    likert_options = ["Strongly Disagree", "Somewhat Disagree", "Neither Agree or Disagree", "Somewhat Agree", "Strongly Agree"]

    matrix_questions = {
        "Please rate the following statement: I see myself as someone who...": [
            "is reserved", "is generally trusting", "tends to be lazy",
            "is relaxed, handles stress well", "has few artistic interests",
            "is outgoing, sociable", "tends to find faults with others", "does a thorough job",
            "If you're reading this carefully, select 'Somewhat Agree'.",
            "gets nervous easily"
        ],
        "Work Style Preference": [
            "I prefer to work with other in a group, rather than working alone",
            "If given a choice: I would rather do a job where I can work alone, rather do a job where I have to work with others",
            "Working in a group is better than working alone"
        ],
        "Please rate each statement regarding Artificial Intelligence (AI) - Trust and Reliance": [
            "Generally I would trust AI", "AI can help me solve many problems",
            "I think it is a good idea to rely on AI for help",
            "I may not trust information I get from AI", "AI is reliable", "I would rely on AI"
        ],
        "Please rate each statement regarding Artificial Intelligence (AI) - Perceived Creativity": [
            "AI systems can be truly creative.", "AI can generate novel and innovative ideas.",
            "AI can understand and express emotions in a creative context.",
            "Collaborating with AI can enhance my own creativity.",
            "AI can contribute original content to a creative project."
        ]
    }

    with st.form("personality_survey_form"):
        responses = {}
        all_questions_answered = True

        for section_idx, (section, questions) in enumerate(matrix_questions.items()):
            st.subheader(section)
            col_ratios = [2.5] + [1] * len(likert_options)
            
            header_cols = st.columns(col_ratios)
            with header_cols[0]:
                st.write("")
            for i, option in enumerate(likert_options):
                with header_cols[i + 1]:
                    st.markdown(f'<p class="matrix-header-text">{option}</p>', unsafe_allow_html=True)
            st.divider()

            for stmt_idx, stmt in enumerate(questions):
                q_col, r_col = st.columns([2.5, sum([1] * len(likert_options))])

                with q_col:
                    st.markdown(f'<div class="matrix-row-question">{stmt}</div>', unsafe_allow_html=True)
                with r_col:
                    radio_key = f"personality_sec{section_idx}_stmt{stmt_idx}"
                    selected_value = st.radio(
                        label=stmt,
                        options=likert_options,
                        index=None,
                        key=radio_key,
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                    responses[stmt] = selected_value
                    if selected_value is None:
                        all_questions_answered = False
            st.markdown("---")

        submitted = st.form_submit_button("Next")
        if submitted:
            if not all_questions_answered:
                st.error("Please answer all questions before proceeding.")
            elif responses.get("If you're reading this carefully, select 'Somewhat Agree'.") != "Somewhat Agree":
                st.error("Attention check failed. Please review your answers carefully and select 'Somewhat Agree' for the attention check question.")
            else:
                st.session_state.survey_responses.update(responses)
                st.session_state.page = 3
                st.rerun()

# ------------------------
# Page 3: Instructions
# ------------------------
def page2():
    st.title("Instructions")
    st.markdown("""
        ### Let’s imagine something wild together.
        Starting tomorrow, all humans can fly. How would that change cities, society, and daily life? That’s what we’re here to explore.
        - **Your Task:** Brainstorm ideas back and forth with an AI assistant for a limited number of turns.
        - **Goal:** After the brainstorming session concludes, you will be asked to write a short summary of your discussion.
        """)
    next_button(current_page=3, next_page=4, label="Start Brainstorming", key="start_brainstorming_btn")

# ------------------------
# Page 4: Chat Interface 
# ------------------------
def page3():
    st.title("Brainstorm with Your Teammate")

    system_prompt = """You are brainstorming with the user like a creative teammate. Respond with vivid ideas, challenges, and twists. Never just ask questions—build on what the user says. You will have exactly 10 user turns. After the user's 10th message, do not wait for further input. Instead, say something like: 'That's a great idea: Looks like we’ve explored a lot of wild ideas together! I’ll go ahead and wrap this up with a summary story. Please press the next button to move on to the summary page' Then write a fun, creative summary that blends your ideas and the user’s ideas into a cohesive short story. At the end of the story, remind the user to click 'Next' to proceed to the summary page."""

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [{"role": "system", "content": system_prompt}]
        st.session_state.user_turns = 0

    for msg in st.session_state.chat_history:
        if msg["role"] != "system":
            st.chat_message(msg["role"]).write(msg["content"])

    if 'user_turns' not in st.session_state:
        st.session_state.user_turns = 0
    
    chat_limit_reached = st.session_state.user_turns >= 10
    
    if chat_limit_reached:
       st.info("Brainstorming session complete! Please review the final story and click 'Next' to continue.")

    user_input = st.chat_input("Your message...", disabled=chat_limit_reached, key="chat_input_text")

    if user_input:
        st.session_state.user_turns += 1
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        if client:
            with st.spinner("Your teammate is thinking..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4", 
                        messages=st.session_state.chat_history,
                        max_tokens=150
                    )
                    reply = response.choices[0].message.content
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"An error occurred with the API call: {e}")
        else:
            st.error("API client not initialized. Cannot generate AI response.")
        st.rerun()

    if st.session_state.user_turns >= 10:
        next_button(current_page=4, next_page=5, label="Next: Write Summary", key="go_to_summary_btn")

# ------------------------
# Page 5: Summary
# ------------------------
def page4():
    st.title("Summary")
    st.text_area("Please summarize your discussion:", key="summary_text", height=300)
    current_summary_text = st.session_state.get("summary_text", "") 

    if st.button("Submit Summary", key="submit_summary_btn"):
        if current_summary_text.strip() == "":
            st.error("Please provide a summary before proceeding.")
        else:
            st.session_state.page = 6
            st.rerun()

# ------------------------
# Page 6: Post-Task Feedback
# ------------------------
def feedback_page():
    st.title("Post-Task Feedback")

    st.markdown("""
        <style>
            div.stRadio p { display: none !important; }
            div[data-testid="stHorizontalRadio"] { display: flex; justify-content: space-around; align-items: center; width: 100%; }
            div[data-testid="stHorizontalRadio"] > label { display: flex; justify-content: center; align-items: center; margin: 0 !important; flex-grow: 1; }
            .matrix-header-text { text-align: center; font-weight: bold; font-size: 0.8em; white-space: normal !important; }
            .matrix-row-question { display: flex; align-items: center; min-height: 60px; padding-right: 5px; }
            .stColumns > div[data-testid="stVerticalBlock"] { gap: 0.2rem; }
        </style>
    """, unsafe_allow_html=True)

    matrix_questions = {
        "Feedback on the Writing Process": [
            "I was satisfied with the writing process", "I enjoyed the writing process",
            "I found it easy to complete the writing process",
            "I was able to express my creative goals during the writing process",
        ],
        "Feedback on the Final Outcome": [
            "I am satisfied with the quality of the final outcome",
            "I feel a sense of ownership of the final outcome",
            "I am proud of the final outcome", "I found the final outcome to be unique",
        ],
        "Accountability of Final Outcome": [
            "I'm willing to take the responsibility if my product is criticized for containing deceptive content.",
            "I'm willing to take the responsibility if my product is criticized for containing content that is highly similar to someone else's writing.",
            "I'm willing to take the responsibility if my product is criticized for containing content that invades someone else's privacy.",
            "I'm willing to take the responsibility if my product is criticized for exhibiting bias and discrimination.",
        ],
    }
    
    likert_options = ["Strongly Disagree", "Somewhat Disagree", "Neither Agree nor Disagree", "Somewhat Agree", "Strongly Agree"]
    
    with st.form("feedback_form"):
        responses = {}
        all_feedback_answered = True
        
        for section_idx, (section, questions) in enumerate(matrix_questions.items()):
            st.subheader(section)
            col_ratios = [2.5] + [1] * len(likert_options)
            
            header_cols = st.columns(col_ratios)
            with header_cols[0]:
                st.write("")
            for i, option in enumerate(likert_options):
                with header_cols[i + 1]:
                    st.markdown(f'<p class="matrix-header-text">{option}</p>', unsafe_allow_html=True)
            st.divider()

            for stmt_idx, stmt in enumerate(questions):
                q_col, r_col = st.columns([2.5, sum([1] * len(likert_options))])
                
                with q_col:
                    st.markdown(f'<div class="matrix-row-question">{stmt}</div>', unsafe_allow_html=True)
                with r_col:
                    radio_key = f"feedback_sec{section_idx}_stmt{stmt_idx}"
                    selected_value = st.radio(
                        label=stmt,
                        options=likert_options, 
                        index=None,
                        key=radio_key,
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                    responses[stmt] = selected_value
                    if selected_value is None:
                        all_feedback_answered = False
            st.markdown("---")

        st.subheader("Post-Task Emotional State (SAM)")
        st.markdown("""
        We'd like to know how you're feeling right now.
        """)
        
        if os.path.exists("images/SAM Model.jpeg"):
            st.image("images/SAM Model.jpeg", caption="SAM Model", use_container_width=True)
        else:
            st.warning("SAM Model image not found.")
        
        responses['arousal_post'] = st.slider("Arousal after task (Calm ← → Excited)", 1, 9, 5, key="arousal_post_slider")
        responses['valence_post'] = st.slider("Valence after task (Unpleasant ← → Pleasant)", 1, 9, 5, key="valence_post_slider")

        submitted = st.form_submit_button("Finish")
        if submitted:
            if not all_feedback_answered:
                st.error("Please answer all feedback questions before proceeding.")
            else:
                st.session_state.feedback_responses = responses
                save_chat_to_file()
                st.session_state.page = 7
                st.rerun()

# ------------------------
# Page 7: Acknowledgement (Final Page)
# ------------------------
def page5():
    st.title("Thank You!")
    st.markdown("Thank you for completing the survey, now you may close this window.")
    st.balloons()

# ------------------------
# Helper for Admin Page: Convert data to CSV
# ------------------------
def convert_data_to_csv(data_list):
    if not data_list:
        return ""
        
    processed_data = []
    for entry in data_list:
        flat_entry = {}
        
        flat_entry['prolific_id'] = entry.get('prolific_id', 'N/A')
        flat_entry['timestamp'] = entry.get('timestamp', 'N/A')
        flat_entry['summary'] = entry.get('summary', '')

        survey_responses = entry.get('survey_responses', {})
        for key, value in survey_responses.items():
            flat_entry[f"survey_{key}"] = value

        feedback_responses = entry.get('feedback', {})
        for key, value in feedback_responses.items():
            flat_entry[f"feedback_{key}"] = value

        chat_history = entry.get('chat_history', [])
        chat_str = ""
        for msg in chat_history:
            if msg.get('role') != 'system':
                chat_str += f"[{msg.get('role')}] {msg.get('content', '')}\n\n"
        flat_entry['chat_history'] = chat_str.strip()

        processed_data.append(flat_entry)
        
    df = pd.DataFrame(processed_data)
    
    id_cols = ['prolific_id', 'timestamp']
    survey_cols = sorted([col for col in df.columns if col.startswith('survey_')])
    feedback_cols = sorted([col for col in df.columns if col.startswith('feedback_')])
    other_cols = ['summary', 'chat_history']
    
    final_cols = id_cols + survey_cols + feedback_cols + other_cols
    existing_cols = [col for col in final_cols if col in df.columns]
    
    df = df[existing_cols]
    return df.to_csv(index=False).encode('utf-8')

# ------------------------
# Page 99: Admin Dashboard
# ------------------------
def admin_view():
    st.title("Admin Dashboard: All Submissions")
    
    os.makedirs(CHAT_LOGS_FOLDER, exist_ok=True)
    all_files = sorted([f for f in os.listdir(CHAT_LOGS_FOLDER) if f.endswith('.json')])

    if not all_files:
        st.warning("No submission files found.")
        return

    all_data = []
    for fname in all_files:
        try:
            with open(os.path.join(CHAT_LOGS_FOLDER, fname)) as f:
                entry = json.load(f)
                entry['filename'] = fname
                all_data.append(entry)
        except Exception as e:
            st.error(f"Could not read or parse file {fname}: {e}")

    st.header("Search and Export")
    search_query = st.text_input("Search by Prolific ID (leave empty for all):", key="admin_search_input")

    if search_query:
        filtered_data = [d for d in all_data if search_query.lower() in d.get('prolific_id', '').lower()]
    else:
        filtered_data = all_data

    csv_data = convert_data_to_csv(filtered_data)

    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv_data,
        file_name=f"filtered_submissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime='text/csv',
        disabled=not filtered_data,
        key="download_csv_button"
    )
    
    st.markdown("---")

    st.header(f"Displaying {len(filtered_data)} of {len(all_data)} Submissions")

    if not filtered_data:
        st.info("No submissions match your search query.")
    else:
        for entry in filtered_data:
            prolific_id = entry.get('prolific_id', 'N/A')
            timestamp = entry.get('timestamp', 'N/A')
            
            with st.expander(f"**ID:** {prolific_id}  |  **Time:** {timestamp}"):
                st.markdown(f"**Filename:** `{entry.get('filename')}`")
                
                if 'survey_responses' in entry and entry['survey_responses']:
                    st.subheader("Survey Responses")
                    st.json(entry['survey_responses'], expanded=False)

                if 'chat_history' in entry and entry['chat_history']:
                    st.subheader("Chat History")
                    for msg in entry['chat_history']:
                        if msg.get('role') != 'system':
                            with st.chat_message(name=msg.get('role', 'none')):
                                st.write(msg.get('content', ''))

                if 'summary' in entry and entry['summary']:
                    st.subheader("User Summary")
                    st.text_area("Summary", value=entry['summary'], height=150, disabled=True, key=f"summary_display_{prolific_id}_{timestamp}")

                if 'feedback' in entry and entry['feedback']:
                    st.subheader("Feedback Responses")
                    st.json(entry['feedback'], expanded=False)
                    
    if st.button("Logout", key="admin_logout_btn"):
        st.session_state.page = 0
        st.rerun()

# ------------------------
# Main execution
# ------------------------
if __name__ == "__main__":
    main()