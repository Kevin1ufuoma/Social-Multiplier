import streamlit as st
import os
from groq import Groq
from supabase import create_client
from dotenv import load_dotenv

# 1. INITIALIZE & SECURE KEYS
load_dotenv()

def get_secrets():
    # 1. Try reading local hidden .env file first
    secrets = {
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY")
    }
    
    # 2. If not found locally, look at Streamlit Cloud secrets (production)
    if not secrets["GROQ_API_KEY"]:
        try:
            secrets["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
            secrets["SUPABASE_URL"] = st.secrets["SUPABASE_URL"]
            secrets["SUPABASE_KEY"] = st.secrets["SUPABASE_KEY"]
        except Exception:
            pass
    return secrets

config = get_secrets()

# Configure the browser tab
st.set_page_config(page_title="AI Content Multiplier", layout="wide")

# App Header
st.title("🚀 AI Social Media Content Multiplier")
st.caption("Transform a single piece of long-form content into optimized posts across networks.")

# Create two columns: Left for inputs, Right for outputs
col1, col2 = st.columns(2)

with col1:
    st.header("📝 Seed Content Input")
    
    # Text box for pasting content
    seed_text = st.text_area(
        "Paste your long-form text, article, or video script here:",
        height=250,
        placeholder="Type or paste your content here..."
    )
    
    st.write("---")
    st.header("🎯 Target Platforms")
    
    # Checkboxes to select channels
    use_linkedin = st.checkbox("LinkedIn Post (Professional, value-driven)", value=True)
    use_twitter  = st.checkbox("X / Twitter Thread (Punchy, short hooks)", value=True)
    use_threads  = st.checkbox("Instagram Threads (Narrative, conversational)")
    
    # Generation Button
    generate_btn = st.button("Multiply Content ✨", type="primary", use_container_width=True)

with col2:
    st.header("✨ Generated Outputs")
    
    if generate_btn:
        # Basic validation checks
        if not config["GROQ_API_KEY"] or not config["SUPABASE_URL"] or not config["SUPABASE_KEY"]:
            st.error("❌ Missing configuration keys! Check that GROQ_API_KEY, SUPABASE_URL, and SUPABASE_KEY are in your .env file.")
        elif not seed_text.strip():
            st.warning("⚠️ Please enter some text in the input box first!")
        elif not (use_linkedin or use_twitter or use_threads):
            st.warning("⚠️ Please select at least one target platform checkbox!")
        else:
            with st.spinner("🧠 Groq AI is multiplying your content & syncing to Supabase..."):
                try:
                    # Initialize clients
                    groq_client = Groq(api_key=config["GROQ_API_KEY"])
                    supabase_client = create_client(config["SUPABASE_URL"], config["SUPABASE_KEY"])
                    
                    # Create dynamic tabs
                    tabs_to_create = []
                    if use_linkedin: tabs_to_create.append("💼 LinkedIn")
                    if use_twitter:  tabs_to_create.append("🐦 X / Twitter")
                    if use_threads:  tabs_to_create.append("🧵 Threads")
                    
                    ui_tabs = st.tabs(tabs_to_create)
                    tab_index = 0
                    
                    # Keep track of generated texts to save to our database
                    saved_outputs = {"linkedin": None, "twitter": None, "threads": None}
                    
                    # Helper function to request AI output quickly
                    def generate_post(system_instruction):
                        response = groq_client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": seed_text}
                            ],
                            model="qwen/qwen3.8-27b",
                        )
                        # FIX: Added [0] to grab the first choice element out of the list container
                        return response.choices[0].message.content


                    # --- GENERATE LINKEDIN ---
                    if use_linkedin:
                        with ui_tabs[tab_index]:
                            linkedin_prompt = (
                                "You are a professional LinkedIn growth expert. Rewrite the text into a high-value corporate post. "
                                "Use clean paragraph line breaks, an engaging professional hook, bullet points, and 2-3 hashtags."
                            )
                            saved_outputs["linkedin"] = generate_post(linkedin_prompt)
                            st.success("LinkedIn Variant Ready!")
                            st.write(saved_outputs["linkedin"])
                        tab_index += 1

                    # --- GENERATE X / TWITTER ---
                    if use_twitter:
                        with ui_tabs[tab_index]:
                            twitter_prompt = (
                                "You are a ghostwriter for high-traffic tech/business X accounts. "
                                "Break down the input into a multi-post thread (numbered 1/, 2/, 3/, etc.). "
                                "Keep each numbered statement concise, bold, and under 280 characters. No hashtags."
                            )
                            saved_outputs["twitter"] = generate_post(twitter_prompt)
                            st.success("X Thread Variant Ready!")
                            st.write(saved_outputs["twitter"])
                        tab_index += 1

                    # --- GENERATE THREADS ---
                    if use_threads:
                        with ui_tabs[tab_index]:
                            threads_prompt = (
                                "You are an expert community manager for Instagram Threads. "
                                "Convert the source text into an informal, authentic, storytelling thread. "
                                "End with an open-ended question to spark replies."
                            )
                            saved_outputs["threads"] = generate_post(threads_prompt)
                            st.success("Threads Variant Ready!")
                            st.write(saved_outputs["threads"])
                    
                    # --- SAVE DATA TO SUPABASE ---
                    data_to_insert = {
                        "seed_text": seed_text,
                        "linkedin_output": saved_outputs["linkedin"],
                        "twitter_output": saved_outputs["twitter"],
                        "threads_output": saved_outputs["threads"]
                    }
                    
                    # Push row to Supabase
                    supabase_client.table("content_history").insert(data_to_insert).execute()
                    st.info("💾 Content logged successfully to Supabase history!")
                            
                except Exception as e:
                    st.error(f"An error occurred: {e}")
    else:
        st.write("Your multi-channel content variations will appear here once you click generate.")
