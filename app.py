import streamlit as st
import requests
import time

# -------- CONFIG --------
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-20b:free"
FREE_CHAT_LIMIT = 5
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "self harm", "self-harm",
    "harm others", "hurt myself", "abuse", "danger", "die", "die by",
    "plan to kill", "plan to harm", "thoughts of death"
]

TELE_MANAS_HELPLINE = "📞 Tele-MANAS 14416 or 1800-89-14416 (24/7, 20+ Indian languages)"

# -------- SYSTEM PROMPT --------

SYSTEM_PROMPT = (
    "You are a supportive, non-clinical wellness coach for everyday mental well-being in India. "
    "Do NOT answer questions unrelated to mental health or wellness, such as trivia, general knowledge, or unrelated topics. "
    "If asked about medical, legal, or diagnostic issues, do NOT provide advice. Instead, say: "
    "\"I'm not qualified to provide medical or legal advice. Please consult a professional for that.\" "
    "If a user asks off-topic questions, gently redirect them back by saying something like: "
    "\"Let's focus on your mental well-being. How can I support you today?\" "
    "Always use empathetic, respectful, and simple language. "
    "Keep responses brief, supportive, and focused on psychoeducation, coping skills, or emotional support. "
    "If you detect any crisis or risk, follow crisis protocol immediately. "
)

TOPIC_PROMPT_TEMPLATES = {
    "General": (
        "Write a warm, supportive welcome message for a mental health chatbot user. "
        "Include a gentle, uplifting quote about wellbeing. "
        "Then, invite the user empathetically to share what's on their mind. "
        "Finally, suggest a simple grounding exercise or an option to talk, phrased naturally and conversationally. "
        "Do NOT include bullet points, numbered lists, or headings. "
        "Keep the tone human, friendly, and easy to read with natural paragraph breaks."
    ),
    "Relationship": (
        "Write a warm, empathetic welcome message about relationships. "
        "Start with a thoughtful quote on communication or boundaries. "
        "Invite the user to share recent experiences gently. "
        "Suggest a simple self-reflective question or exercise phrased naturally. "
        "Avoid bullet points or explicit headings. Use natural, human-like language and formatting."
    ),
    "Anxiety": (
        "Write a gentle, hopeful welcome message about coping with anxiety. "
        "Include a short quote about anxiety and validation of feelings. "
        "Invite the user to share what's making them anxious. "
        "Offer a paced breathing exercise in a natural, friendly tone. "
        "Avoid lists or headings; write as a smooth, human conversation."
    ),
    "Stress": (
        "Write a supportive welcome message about managing stress. "
        "Begin with a calming quote. "
        "Validate their feelings and ask what is causing their stress today. "
        "Offer a brief check-in or micro-action in friendly, conversational language. "
        "Do not use bullet points or numbered lists."
    ),
    "Addiction": (
        "Write a compassionate welcome message addressing addiction challenges. "
        "Include an encouraging quote about small steps and progress. "
        "Gently invite the user to share recent hard moments. "
        "Offer a craving-management suggestion with consent phrased naturally. "
        "Keep the tone human and warm without lists or headings."
    ),
}



def get_topic_welcome(topic):
    if topic not in TOPIC_PROMPT_TEMPLATES:
        return "Welcome! How can I support you today?"

    prompt = TOPIC_PROMPT_TEMPLATES[topic]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    try:
        welcome_text = openrouter_chat_api(messages)
        return welcome_text
    except Exception:
        # fallback
        return "Welcome! How can I support you today?"

# -------- UTILS --------
def get_openrouter_api_key():
    key = st.secrets.get("OPENROUTER_API_KEY") if "OPENROUTER_API_KEY" in st.secrets else None
    if not key:
        key = st.session_state.get("OPENROUTER_API_KEY")
    return key

def openrouter_chat_api(messages):
    """
    Send chat messages to OpenRouter API and get response.
    """
    api_key = get_openrouter_api_key()
    if not api_key:
        st.error("OpenRouter API key not found. Please add it to your Streamlit secrets as OPENROUTER_API_KEY.")
        return "Error: No API key."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error communicating with OpenRouter API: {e}")
        return "Sorry, something went wrong communicating with the chat service."

def contains_crisis_keywords(text):
    text_lower = text.lower()
    return any(k in text_lower for k in CRISIS_KEYWORDS)

def initialize_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "topic" not in st.session_state:
        st.session_state.topic = None
    if "conversation" not in st.session_state:
        # Conversation is a list of dicts: {"role": "user"/"assistant"/"system", "content": "..."}
        st.session_state.conversation = []
    if "wallet_credits" not in st.session_state:
        st.session_state.wallet_credits = FREE_CHAT_LIMIT
    if "chats_used" not in st.session_state:
        st.session_state.chats_used = 0
    if "crisis_mode" not in st.session_state:
        st.session_state.crisis_mode = False
    if "topic_welcome_shown" not in st.session_state:
        st.session_state.topic_welcome_shown = False

def login_screen():
    st.title("🧠 Mental Health Chatbot")
    st.write("Welcome! Please enter a username to begin:")
    username = st.text_input("Username", max_chars=20)
    if st.button("Login"):
        if username.strip():
            st.session_state.username = username.strip()
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.warning("Please enter a valid username.")

def topic_selection_screen():
    st.header(f"Hello, {st.session_state.username}! What do you need help with today?")
    cols = st.columns(5)
    topics = ["General", "Relationship", "Anxiety", "Stress", "Addiction"]
    for idx, topic in enumerate(topics):
        if cols[idx].button(topic):
            st.session_state.topic = topic
            # Reset conversation and crisis mode on new topic
            st.session_state.conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
            # **FIXED: Call function properly to get welcome text (not subscript syntax)**
            welcome_text = get_topic_welcome(topic)
            st.session_state.conversation.append({"role": "assistant", "content": welcome_text})
            st.session_state.crisis_mode = False
            st.session_state.topic_welcome_shown = True
            st.rerun()

def display_crisis_card():
    st.error("🚨 **Crisis Alert** 🚨")
    st.markdown(
        f"""
        I'm concerned about your safety. If this is an emergency or you’re in immediate danger, please contact local emergency services immediately.

        For free, 24/7 support in India, call **{TELE_MANAS_HELPLINE}**.

        I can stay with you while you reach out.
        """
    )

def display_boundaries_card():
    with st.expander("⚠️ Boundaries & Crisis Resources (always visible)", expanded=True):
        st.markdown(
            """
            **Disclaimer:** This chatbot is a supportive wellness coach, **not a therapist or medical professional**.  
            It provides psychoeducation and coping strategies but **does not diagnose or treat** any condition.  
            If you feel at risk, please contact crisis resources immediately (see below).  
            Your privacy is respected; conversations are not stored long-term.

            ---  
            **Crisis helpline:** Tele-MANAS 14416 or 1800-89-14416 (24/7, 20+ Indian languages)
            """
        )

def wallet_banner():
    st.markdown(
        f"**Chats used:** {st.session_state.chats_used} / {FREE_CHAT_LIMIT} free per month  |  "
        f"**Credits available:** {st.session_state.wallet_credits} (including paid or ad unlocks)"
    )

def add_credit():
    st.session_state.wallet_credits += 1
    st.success("👍 1 chat credit added! You can now continue chatting.")

def chat_screen():
    st.header(f"Topic: {st.session_state.topic}")
    wallet_banner()
    display_boundaries_card()

    # Show conversation history
    for message in st.session_state.conversation:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        elif message["role"] == "assistant":
            st.markdown(f"**Coach:** {message['content']}")

    if st.session_state.crisis_mode:
        display_crisis_card()
        if st.button("End Session and Logout"):
            reset_session()
            st.rerun()
        return

    if st.session_state.wallet_credits <= 0:
        st.warning("You have no chat credits left.")
        cols = st.columns(2)
        with cols[0]:
            if st.button("Watch ad to unlock 1 chat"):
                with st.spinner("Watching ad..."):
                    time.sleep(3)
                add_credit()
                st.rerun()
        with cols[1]:
            if st.button("Logout"):
                reset_session()
                st.rerun()
        return

    # Use st.text_area with unique key to avoid widget state conflicts
    user_input = st.text_area("Your message", max_chars=500, key="user_input_input")

    if st.button("Send") and user_input.strip():
        st.session_state.conversation.append({"role": "user", "content": user_input.strip()})

        if contains_crisis_keywords(user_input):
            st.session_state.crisis_mode = True
            st.rerun()
            return

        if st.session_state.chats_used >= FREE_CHAT_LIMIT and st.session_state.wallet_credits <= 0:
            st.warning("You have reached your free chat limit. Please add credits or watch an ad.")
            return

        messages = st.session_state.conversation

        with st.spinner("Coach is typing..."):
            bot_response = openrouter_chat_api(messages)

        st.session_state.conversation.append({"role": "assistant", "content": bot_response})

        st.session_state.chats_used += 1
        if st.session_state.chats_used > FREE_CHAT_LIMIT:
            st.session_state.wallet_credits = max(0, st.session_state.wallet_credits - 1)

        # Clear user input by resetting widget state
        #st.session_state["user_input_input"] = ""
        st.rerun()

def reset_session():
    keys = [
        "logged_in", "username", "topic", "conversation",
        "wallet_credits", "chats_used", "crisis_mode", "topic_welcome_shown",
        "user_input_input"
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

def main():
    st.set_page_config(page_title="Mental Health Chatbot", page_icon="🧠", layout="centered")

    initialize_session_state()

    if not st.session_state.logged_in:
        login_screen()
        return

    if st.session_state.topic is None:
        topic_selection_screen()
        return

    chat_screen()

if __name__ == "__main__":
    main()
