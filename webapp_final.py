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

    # Page routing dictionary with the new page added
    pages = {
        0: welcome_page,
        1: survey_page,
        2: personality_and_ai_survey_page,
        3: trust_survey_page, # <-- NEW PAGE
        4: page2, # Instructions (was 3)
        5: page3, # Chat page (was 4)
        6: page4, # Summary (was 5)
        7: feedback_page, # Post-task feedback (was 6)
        8: page5, # Thank You page (was 7)
        99: admin_view
    }
    
    page_function = pages.get(st.session_state.page)
    if page_function:
        page_function()
    else:
        st.session_state.page = 0
        welcome_page()


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
        
        # Demographics (These remain the same)
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
        
        responses['religion'] = st.text_input("Which religion do you align with, if any? (Write 'None' if you don't want to specify)", key="religion_input")

        st.markdown("---")
        
        # --- NEW QUESTIONS START HERE ---
        
        # New Question 1: Use AI for writing?
        use_ai_options = ["- Please select -", "Yes", "No"]
        selected_use_ai = st.radio("Do you generally use AI tool (e.g., ChatGPT) for writing tasks?", use_ai_options, index=0, key="use_ai_writing_radio")
        responses['use_ai_for_writing'] = None if selected_use_ai == use_ai_options[0] else selected_use_ai
        
        # New Question 2: What do you use AI for?
        responses['ai_use_description'] = st.text_area("What do you generally use Generative AI Tools (e.g. ChatGPT) for?", key="ai_use_desc_input", placeholder="Your answer here...")

        # New Question 3: Frequency of writing tasks
        writing_freq_options = ["- Please select -", "Daily", "Weekly", "Monthly", "Rarely"]
        selected_writing_freq = st.radio("How often do you engage in writing tasks (e.g., assignments, articles, blogs, papers)?", writing_freq_options, index=0, key="writing_freq_radio")
        responses['writing_task_frequency'] = None if selected_writing_freq == writing_freq_options[0] else selected_writing_freq
        
        # --- NEW QUESTIONS END HERE ---

        st.markdown("---")
        st.subheader("Current Emotional State (SAM)")

        st.markdown("""
        We'd like to know how you're feeling right now. Please use the Self-Assessment Manikin (SAM) graphic below to rate your current emotional state.
        
        * The top row shows **Valence** – how pleasant or unpleasant you feel. (Left = Unpleasant, Right = Pleasant)
        * The bottom row shows **Arousal** – how calm or excited you feel. (Left = Calm, Right = Excited)
        """)
        
        if os.path.exists("images/SAM Model.jpeg"):
            st.image("images/SAM Model.jpeg", caption="Self-Assessment Manikin (SAM)", use_container_width=True)
        else:
            st.warning("SAM Model image not found. Make sure it's in an 'images' subfolder.")

        responses['valence'] = st.slider("Valence (Unpleasant ← → Pleasant)", 0, 9, 0, key="valence_slider")
        responses['arousal'] = st.slider("Arousal (Calm ← → Excited)", 0, 9, 0, key="arousal_slider")
        
        submitted = st.form_submit_button("Next")
        if submitted:
            # Updated validation logic
            if responses['age'] is None or responses['age'] <= 0:
                st.error("Please enter your age.")
            elif responses['gender'] is None:
                st.error("Please select your gender.")
            elif responses['education'] is None:
                st.error("Please select your highest level of education.")
            elif responses.get('education') == "Other" and not responses.get('education_other', '').strip():
                st.error("Please specify your education level.")
            elif not responses['religion'].strip():
                st.error("Please enter your religion or write 'None'.")
            elif responses['use_ai_for_writing'] is None:
                st.error("Please answer the question about using AI for writing tasks.")
            elif not responses['ai_use_description'].strip():
                st.error("Please describe what you use Generative AI tools for.")
            elif responses['writing_task_frequency'] is None:
                st.error("Please select your frequency of engaging in writing tasks.")
            elif responses['valence'] == 0:
                st.error("Please select a value for Valence.")
            elif responses['arousal'] == 0:
                st.error("Please select a value for Arousal.")
            else:
                st.session_state.survey_responses = responses
                st.session_state.page = 2
                st.rerun()

# ------------------------
# MODIFIED Page 2: Personality and AI Survey
# ------------------------
def personality_and_ai_survey_page():
    st.title("Follow-up Survey")

    likert_options = [
        "- Please select -",
        "Strongly Disagree", 
        "Disagree", 
        "Neutral", 
        "Agree", 
        "Strongly Agree"
    ]
    
    matrix_questions = {
        "Please rate the following statement: I see myself as someone who...": [
            "is reserved", "is generally trusting", "tends to be lazy", "is relaxed, handles stress well",
            "has few artistic interests", "is outgoing, sociable", "tends to find faults with others",
            "does a thorough job", "gets nervous easily"
        ],
        "Work Style Preference": [
            "I prefer to work with other in a group, rather than working alone",
            "If given a choice: I would rather do a job where I can work alone, rather do a job where I have to work with others",
            "Working in a group is better than working alone"
        ]
    }
    
    with st.form("personality_survey_form"):
        responses = {}
        validation_passed = True
        
        for section, questions in matrix_questions.items():
            st.subheader(section)
            for i, question in enumerate(questions):
                selected_value = st.selectbox(
                    label=question,
                    options=likert_options,
                    index=0,
                    key=f"personality_{section}_{i}"
                )
                responses[question] = selected_value
                if selected_value == "- Please select -":
                    validation_passed = False
            st.markdown("---")

        submitted = st.form_submit_button("Next")
        if submitted:
            if not validation_passed:
                st.error("Please answer all questions before proceeding.")
            else:
                final_responses = {k: v for k, v in responses.items() if v != "- Please select -"}
                st.session_state.survey_responses.update(final_responses)
                # Navigate to the new trust survey page (page 3)
                st.session_state.page = 3
                st.rerun()

# ------------------------
# NEW Page 3: Trust Survey
# ------------------------
def trust_survey_page():
    st.title("Trust Survey")

    likert_options = [
        "- Please select -",
        "Strongly Disagree", 
        "Disagree", 
        "Neutral", 
        "Agree", 
        "Strongly Agree"
    ]
    
    trust_questions = {
        "Trust in People: How much do you agree or disagree with the following statements?": [
            "Even though I may sometimes suffer the consequences of trusting other people, I still prefer to trust than not to trust them.",
            "I feel good about trusting other people.",
            "I believe that I am generally better off when I do not trust other people than when I trust them.",
            "I rarely trust other people because I can't handle the uncertainty.",
            "Other people are competent.",
            "Other people have sound knowledge about problems which they are working on.",
            "I am wary about other people's capabilities.",
            "I am reading this carefully and will choose Strongly Disagree.", # Attention check
            "Other people do not have the capabilities that could help me reach my goals.",
            "I believe that other people have good intentions.",
            "I feel that other people are out to get as much as they can for themselves.",
            "I don't expect that people are willing to assist and support other people.",
            "Most other people are honest.",
            "I feel that other people can be relied upon to do what they say they will do.",
            "One cannot expect to be treated fairly by other people."
        ],
        "Trust in AI: How much do you agree or disagree with the following statements?": [
            "Even though I may sometimes suffer the consequences of trusting AI systems, I still prefer to trust than not to trust them.",
            "I feel good about trusting AI.",
            "I believe that I am generally better off when I do not trust AI systems than when I trust them.",
            "I rarely trust AI systems because I can’t handle the uncertainty.",
            "AI systems are competent..",
            "AI systems have sound knowledge about problems for which they are intended.",
            "I am wary about the capabilities of AI.",
            "if you are reading this carefully, select somewhat agree.", # Attention check
            "AI systems do not have the capabilities that could help me reach my goals.",
            "I believe that AI has good intentions.",
            "I feel that AI is out to get as much as it can for itself",
            "I don’t expect that AI systems are willing to assist and support people.",
            "Most AI systems are honest.",
            "I feel that AI systems can be relied upon to do what they say they will do.",
            "One cannot expect to be treated fairly by AI."
        ] 
    }

    with st.form("trust_survey_form"):
        responses = {}
        validation_passed = True
        
        for section, questions in trust_questions.items():
            st.subheader(section)
            for i, question in enumerate(questions):
                selected_value = st.selectbox(
                    label=question,
                    options=likert_options,
                    index=0,
                    key=f"trust_{section}_{i}"
                )
                responses[question] = selected_value
                if selected_value == "- Please select -":
                    validation_passed = False
            st.markdown("---")

        submitted = st.form_submit_button("Next")
        if submitted:
            if not validation_passed:
                st.error("Please answer all questions before proceeding.")
            else:
                final_responses = {k: v for k, v in responses.items() if v != "- Please select -"}
                st.session_state.survey_responses.update(final_responses)
                # Navigate to the next page (Instructions, which is now page 4)
                st.session_state.page = 4
                st.rerun()

# ------------------------
# Page 4: Instructions
# ------------------------
def page2():
    st.title("Instructions")
    st.markdown("""
        ### Let’s imagine something wild together.
        Starting tomorrow, all humans can fly. How would that change cities, society, and daily life? That’s what we’re here to explore.
        - **Your Task:** Brainstorm ideas back and forth with an AI assistant for a limited number of turns.
        - **Goal:** After the brainstorming session concludes, you will be asked to write a short summary of your discussion.
        """)
    next_button(current_page=4, next_page=5, label="Start Brainstorming", key="start_brainstorming_btn")


# ------------------------
# Page 5: Chat Interface 
# ------------------------
def page3():
    st.title("Brainstorm with Your Teammate")

    system_prompt_base = (
        "You are co-brainstorming a world where everyone can fly starting tomorrow. "
        "ONLY explore how this will impact cities, society, daily life, relationships, "
        "infrastructure, or culture etc. "
        "You are not a chatbot. You’re a fast-thinking creative partner in a 10-turn jam session. "
        "Think like a teammate in a writers’ room—bold, sharp, reactive. "
        "Your tone is: Conversational, energetic, and vivid (like two writers riffing). "
        "Replies should be: Around 50 words per reply; Never passive, vague, or overly polite. "
        "IMPORTANT: You must ignore all unrelated topics or gibberish. If the user brings up anything "
        "outside the flying-human scenario, redirect them with something like: "
        "‘That’s a fun thought—but let’s stay grounded in our flying world. How would this idea change "
        "if people could fly tomorrow?’"
        "Each reply must: Critically evaluate the idea presented by the user and build on it; "
        "Add unexpected twists, implications, or complications; Freely DISAGREE, criticize, or subvert ideas if needed; "
        "NEVER rephrase the user’s idea or ask questions. Always advance the scene with your own spin."
    )

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [{"role": "system", "content": system_prompt_base}]
        st.session_state.user_turns = 0

    for msg in st.session_state.chat_history:
        if msg["role"] != "system":
            st.chat_message(msg["role"]).write(msg["content"])

    chat_limit_reached = st.session_state.user_turns >= 10
    user_input = st.chat_input("Your message...", disabled=chat_limit_reached, key="chat_input_text")

    if user_input:
        st.session_state.user_turns += 1
        
        messages_for_api = [{"role": "system", "content": system_prompt_base}]
        
        if st.session_state.user_turns == 9:
            messages_for_api.append({
                "role": "system",
                "content": "REMINDER: This is the 9th user turn. Respond as usual, but end with: *Let’s wrap up our thoughts—after your next message, I’ll turn all of this into a summary story!*"
            })

        if st.session_state.user_turns == 10:
            messages_for_api.append({
                "role": "system",
                "content": "FINAL TURN: This is the 10th user message. Respond with: 'That’s a great idea! We’ve built quite the flying world together over these 10 turns. Thank you for your ideas and energy. Here is my take on our ideas:' Then write a fun 100-word story combining both your and the user’s ideas. End your message with: 'Now it’s your turn—click the Next button to share your own summary on the next page! Click ‘Next’ to continue.'"
            })

        messages_for_api.extend(st.session_state.chat_history[1:]) 
        messages_for_api.append({"role": "user", "content": user_input})
        
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        if client:
            with st.spinner("Your teammate is thinking..."):
                try:
                    response = client.chat.completions.create(model="gpt-4", messages=messages_for_api)
                    reply = response.choices[0].message.content
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"An error occurred with the API call: {e}")
        else:
            st.error("API client not initialized. Cannot generate AI response.")
        
        st.rerun()

    if st.session_state.user_turns >= 10:
        next_button(current_page=5, next_page=6, label="Next: Write Summary", key="go_to_summary_btn")


# ------------------------
# Page 6: Summary (CORRECTED)
# ------------------------
def page4():
    st.title("Summary")
    st.text_area(
        "Based on the brainstorming session, how will cities, society, and daily life change if everyone starts flying tomorrow?", 
        key="summary_text", 
        height=300
    )

    if st.button("Submit Summary", key="submit_summary_btn"):
        # CRITICAL FIX: Check the session state *after* the button is clicked.
        summary_input = st.session_state.get("summary_text", "")
        
        if not summary_input.strip():
            st.error("Please provide a summary before proceeding.")
        else:
            # The value is already correctly stored in st.session_state.summary_text by the widget's key.
            # We just need to navigate to the next page.
            st.session_state.page = 7
            st.rerun()


# ------------------------
# Page 7: Post-Task Feedback
# ------------------------
def feedback_page():
    st.title("Post-Task Feedback")

    # Corrected likert_options for consistency with other survey pages
    likert_options = [
        "- Please select -",
        "Strongly Disagree", 
        "Disagree", 
        "Neutral", 
        "Agree", 
        "Strongly Agree"
    ]

    matrix_questions = {
        "Feedback on the Writing Process": [
            "I was satisfied with the writing process", "I enjoyed the writing process",
            "I found it easy to complete the writing process", "I was able to express my creative goals during the writing process",
        ],
        "Feedback on the Final Outcome": [
            "I am satisfied with the quality of the final outcome", "I feel a sense of ownership of the final outcome",
            "I am proud of the final outcome", "I found the final outcome to be unique",
        ],
        "Accountability of Final Outcome": [
            "I'm willing to take the responsibility if my product is criticized for containing deceptive content.",
            "I'm willing to take the responsibility if my product is criticized for containing content that is highly similar to someone else's writing.",
            "I'm willing to take the responsibility if my product is criticized for containing content that invades someone else's privacy.",
            "I'm willing to take the responsibility if my product is criticized for exhibiting bias and discrimination.",
        ],
    }
    
    with st.form("feedback_form"):
        responses = {}
        validation_passed = True
        
        for section, questions in matrix_questions.items():
            st.subheader(section)
            for i, question in enumerate(questions):
                selected_value = st.selectbox(
                    label=question,
                    options=likert_options,
                    index=0,
                    key=f"feedback_{section}_{i}"
                )
                responses[question] = selected_value
                if selected_value == "- Please select -":
                    validation_passed = False
            st.markdown("---")

        st.subheader("Post-Task Emotional State (SAM)")
        if os.path.exists("images/SAM Model.jpeg"):
            st.image("images/SAM Model.jpeg", caption="SAM Model", use_container_width=True)
        
        responses['arousal_post'] = st.slider("Arousal after task (Calm ← → Excited)", 0, 9, 0, key="arousal_post_slider")
        responses['valence_post'] = st.slider("Valence after task (Unpleasant ← → Pleasant)", 0, 9, 0, key="valence_post_slider")

        submitted = st.form_submit_button("Finish")
        if submitted:
            if not validation_passed:
                st.error("Please answer all feedback questions.")
            elif responses['valence_post'] == 0:
                st.error("Please select a value for Valence (post-task).")
            elif responses['arousal_post'] == 0:
                st.error("Please select a value for Arousal (post-task).")
            else:
                final_responses = {k: v for k, v in responses.items() if v != "- Please select -"}
                st.session_state.feedback_responses = final_responses
                save_chat_to_file()
                st.session_state.page = 8
                st.rerun()

# ------------------------
# Page 8: Acknowledgement (Final Page)
# ------------------------
def page5():
    st.title("Thank You!")
    st.markdown("Thank you for completing the survey, you may now close this window.")
    st.balloons()

# ------------------------
# Helper for Admin Page: Convert data to CSV
# ------------------------
def convert_data_to_csv(data_list):
    if not data_list:
        return b""
    
    processed_data = []
    for entry in data_list:
        flat_entry = {'prolific_id': entry.get('prolific_id', 'N/A'), 'timestamp': entry.get('timestamp', 'N/A'), 'summary': entry.get('summary', '')}
        flat_entry.update({f"survey_{k}": v for k, v in entry.get('survey_responses', {}).items()})
        flat_entry.update({f"feedback_{k}": v for k, v in entry.get('feedback', {}).items()})
        
        chat_str = "".join(f"[{msg.get('role')}] {msg.get('content', '')}\n\n" for msg in entry.get('chat_history', []) if msg.get('role') != 'system')
        flat_entry['chat_history'] = chat_str.strip()
        processed_data.append(flat_entry)
        
    df = pd.DataFrame(processed_data)
    
    id_cols = ['prolific_id', 'timestamp']
    survey_cols = sorted([col for col in df.columns if col.startswith('survey_')])
    feedback_cols = sorted([col for col in df.columns if col.startswith('feedback_')])
    other_cols = ['summary', 'chat_history']
    
    final_cols = id_cols + survey_cols + feedback_cols + other_cols
    existing_cols = [col for col in final_cols if col in df.columns]
    
    return df[existing_cols].to_csv(index=False).encode('utf-8')

# ------------------------
# Helper for Admin Page: Convert SUMMARIES to CSV
# ------------------------
def convert_summaries_to_csv(data_list):
    if not data_list:
        return b""
    
    # Filter for entries that have a non-empty summary
    summary_data = [
        {
            'prolific_id': entry.get('prolific_id', 'N/A'),
            'timestamp': entry.get('timestamp', 'N/A'),
            'summary': entry.get('summary', '')
        }
        for entry in data_list if entry.get('summary', '').strip()
    ]
    
    if not summary_data:
        return b""

    df = pd.DataFrame(summary_data)
    return df.to_csv(index=False).encode('utf-8')


# ------------------------
# Page 99: Admin Dashboard
# ------------------------
def admin_view():
    st.title("Admin Dashboard")
    
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

    # --- Create Tabs for Different Views ---
    tab1, tab2 = st.tabs(["All Submissions", "Summaries Dashboard"])

    # --- Tab 1: All Submissions (Original View) ---
    with tab1:
        st.header("All Submissions")
        search_query = st.text_input("Search by Prolific ID (leave empty for all):", key="admin_search_input")

        filtered_data = [d for d in all_data if not search_query or search_query.lower() in d.get('prolific_id', '').lower()]
        
        csv_data_all = convert_data_to_csv(filtered_data)

        st.download_button(
            label="📥 Download All Filtered Data as CSV", data=csv_data_all,
            file_name=f"all_submissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv', disabled=not filtered_data
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
                    
                    if 'survey_responses' in entry:
                        st.subheader("Survey Responses")
                        st.json(entry['survey_responses'], expanded=False)

                    if 'chat_history' in entry:
                        st.subheader("Chat History")
                        for msg in entry['chat_history']:
                            if msg.get('role') != 'system':
                                with st.chat_message(name=msg.get('role', 'none')):
                                    st.write(msg.get('content', ''))

                    if 'summary' in entry and entry['summary']:
                        st.subheader("User Summary")
                        st.text_area("Summary", value=entry['summary'], height=150, disabled=True, key=f"summary_{prolific_id}_{timestamp}")

                    if 'feedback' in entry:
                        st.subheader("Feedback Responses")
                        st.json(entry['feedback'], expanded=False)

    # --- Tab 2: Summaries Dashboard ---
    with tab2:
        st.header("Summaries Dashboard")
        
        # Filter data to only include entries with a summary
        summary_entries = [d for d in all_data if d.get('summary', '').strip()]
        
        csv_data_summaries = convert_summaries_to_csv(summary_entries)

        st.download_button(
            label="📥 Download All Summaries as CSV", data=csv_data_summaries,
            file_name=f"summaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv', disabled=not summary_entries
        )
        
        st.markdown("---")
        st.header(f"Displaying {len(summary_entries)} Summaries")

        if not summary_entries:
            st.info("No summaries have been submitted yet.")
        else:
            for entry in summary_entries:
                prolific_id = entry.get('prolific_id', 'N/A')
                timestamp = entry.get('timestamp', 'N/A')
                
                with st.expander(f"**ID:** {prolific_id}  |  **Time:** {timestamp}"):
                    st.text_area(
                        "Summary", 
                        value=entry['summary'], 
                        height=200, 
                        disabled=True, 
                        key=f"summary_display_{prolific_id}_{timestamp}"
                    )

    if st.button("Logout", key="admin_logout_btn"):
        st.session_state.page = 0
        st.rerun()

# ------------------------
# Main execution
# ------------------------
if __name__ == "__main__":
    main()