import streamlit as st
import chromadb
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import sqlite3

# 🔹 Configure Gemini API
genai.configure(api_key="AIzaSyBGcAWwCpxrzY3z9hayFz8qmHT4WDe2Gzg")
model_gemini = genai.GenerativeModel("gemini-1.5-flash")

# 🔹 Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 🔹 Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="faq_collection")

# 🔹 Connect to SQLite for user management & feedback
conn = sqlite3.connect("feedback.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables if not exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        user TEXT, query TEXT, response TEXT, rating INTEGER
    )
""")
conn.commit()

# 🔹 Sidebar Navigation
page = st.sidebar.radio("📌 Navigation", ["🔑 Login / Register", "💬 Chatbot", "🔒 Admin Panel"])

# 🔹 Login / Registration System
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if page == "🔑 Login / Register":
    st.title("🔑 Login or Register")

    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")

    if st.button("🔓 Login / Register"):
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user:
            # Existing user, check password
            if user[1] == password:
                st.session_state.logged_in_user = username
                st.success(f"✅ Welcome back, {username}!")
            else:
                st.error("❌ Incorrect password!")
        else:
            # New user, create account
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            st.session_state.logged_in_user = username
            st.success(f"🎉 Account created! Welcome, {username}!")

elif page == "💬 Chatbot":
    if not st.session_state.logged_in_user:
        st.warning("⚠️ Please log in first.")
        st.stop()

    st.title(f"💡 ML FAQ Chatbot - {st.session_state.logged_in_user}")

    user_query = st.text_input("📝 Ask a question:")

    if st.button("🔍 Get Answer") and user_query:
        query_embedding = model.encode(user_query).tolist()
        results = collection.query(query_embeddings=[query_embedding], n_results=1)

        context = results["metadatas"][0][0]["answer"] if results["documents"] else ""

        response = model_gemini.generate_content(f"Answer this based on: {context}\n\n{user_query}").text
        st.subheader("🤖 Answer:")
        st.write(response)

        # Store feedback entry per user
        cursor.execute("INSERT INTO feedback (user, query, response, rating) VALUES (?, ?, ?, ?)", 
                       (st.session_state.logged_in_user, user_query, response, 0))
        conn.commit()

    # ⭐ Feedback for the Current Query
    if user_query:
        st.write("### ⭐ Provide Feedback")
        rating = st.slider("Rate the response:", 1, 5, 3)

        if st.button("✅ Submit Feedback"):
            cursor.execute("UPDATE feedback SET rating=? WHERE user=? AND query=?", 
                           (rating, st.session_state.logged_in_user, user_query))
            conn.commit()
            st.success("🎉 Feedback submitted!")

elif page == "🔒 Admin Panel":
    if st.session_state.logged_in_user != "admin":
        st.warning("⚠️ Admin access only. Please log in as admin.")
        st.stop()

    st.title("🔒 Admin Panel")

    # Fetch Top & Bottom Feedbacks
    cursor.execute("SELECT user, query, response, rating FROM feedback ORDER BY rating DESC LIMIT 4")
    top_feedbacks = cursor.fetchall()

    cursor.execute("SELECT user, query, response, rating FROM feedback ORDER BY rating ASC LIMIT 4")
    bottom_feedbacks = cursor.fetchall()

    # 🎖 Top 4 Feedbacks Section
    st.markdown("## 🏆 Top 4 Feedbacks")
    if top_feedbacks:
        for idx, (user, q, r, rt) in enumerate(top_feedbacks, start=1):
            with st.expander(f"🌟 #{idx} - {rt}⭐ Rating (User: {user})"):
                st.markdown(f"**🔹 Question:** {q}")
                st.markdown(f"**🔹 Answer:** {r}")
    else:
        st.info("No feedback available.")

    # ⚠️ Bottom 4 Feedbacks Section
    st.markdown("## ❌ Bottom 4 Feedbacks")
    if bottom_feedbacks:
        for idx, (user, q, r, rt) in enumerate(bottom_feedbacks, start=1):
            with st.expander(f"🚨 #{idx} - {rt}⭐ Rating (User: {user})"):
                st.markdown(f"**🔹 Question:** {q}")
                st.markdown(f"**🔹 Answer:** {r}")
    else:
        st.info("No feedback available.")
