# streamlit_app.py
import streamlit as st
import random

# --- Helper Functions (no OpenAI) ---

def get_interview_question(role, domain, mode, prev_qas):
    # Hardcoded pool of example questions
    questions = [
        "Tell me about yourself.",
        "What are your strengths and weaknesses?",
        "Explain OOP concepts in Python.",
        "How would you handle conflict in a team?",
        "What is a REST API?",
        "Why do you want to join this company?",
    ]
    # Pick a random unused question
    asked = {qa["question"] for qa in prev_qas}
    available = [q for q in questions if q not in asked]
    return random.choice(available) if available else "No more questions!"

def evaluate_answer(role, domain, mode, question, answer):
    # Fake scoring logic
    score = random.randint(5, 9)
    feedback = "Good attempt, but could be more detailed."
    suggestions = "Add real-world examples and structure answers clearly."
    return {"feedback": feedback, "score": score, "suggestions": suggestions}

def summarize_session(qas):
    avg_score = sum(qa["score"] for qa in qas) / len(qas)
    return {
        "strengths": "Clear communication, good knowledge base.",
        "improvements": "Need more depth in answers, add examples.",
        "resources": "Practice mock interviews and review role-specific material.",
        "final_score": round(avg_score, 1)
    }

# --- Streamlit UI ---
st.title("Mock Interview Simulator (No OpenAI)")

if "qas" not in st.session_state:
    st.session_state.qas = []
if "step" not in st.session_state:
    st.session_state.step = 0
if "current_q" not in st.session_state:
    st.session_state.current_q = None

if st.session_state.step == 0:
    role = st.text_input("Job Role")
    domain = st.text_input("Domain (optional)")
    mode = st.selectbox("Interview Mode", ["Technical", "Behavioral"])
    if st.button("Start Interview") and role:
        st.session_state.role = role
        st.session_state.domain = domain
        st.session_state.mode = mode
        st.session_state.current_q = get_interview_question(role, domain, mode, [])
        st.session_state.step = 1
        st.experimental_rerun()

elif st.session_state.step <= 5:
    st.subheader(f"Question {st.session_state.step}")
    st.write(st.session_state.current_q)

    answer = st.text_area("Your Answer")
    if st.button("Submit Answer"):
        feedback = evaluate_answer(
            st.session_state.role,
            st.session_state.domain,
            st.session_state.mode,
            st.session_state.current_q,
            answer
        )
        st.session_state.qas.append({
            "question": st.session_state.current_q,
            "answer": answer,
            "feedback": feedback["feedback"],
            "score": feedback["score"],
            "suggestions": feedback["suggestions"]
        })
        st.session_state.step += 1
        if st.session_state.step <= 5:
            st.session_state.current_q = get_interview_question(
                st.session_state.role,
                st.session_state.domain,
                st.session_state.mode,
                st.session_state.qas
            )
        st.experimental_rerun()

else:
    st.subheader("Interview Summary")
    summary = summarize_session(st.session_state.qas)
    for i, qa in enumerate(st.session_state.qas, 1):
        st.markdown(f"**Q{i}: {qa['question']}**")
        st.write(f"Answer: {qa['answer']}")
        st.write(f"Feedback: {qa['feedback']}")
        st.write(f"Score: {qa['score']}/10")
        st.write(f"Suggestions: {qa['suggestions']}")
        st.write("---")
    st.success(f"**Final Score:** {summary['final_score']}/10")
    st.write("**Strengths:**", summary["strengths"])
    st.write("**Areas to Improve:**", summary["improvements"])
    st.write("**Suggested Resources:**", summary["resources"])
    if st.button("Restart"):
        for key in ["qas", "step", "current_q", "role", "domain", "mode"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()
