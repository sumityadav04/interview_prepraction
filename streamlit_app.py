# app.py

import os
from openai import OpenAI
from flask import Flask, render_template, request, session, redirect, url_for
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# --- Helper Functions ---

def get_interview_question(role, domain, mode, prev_qas):
    # Prompt for next question
    prompt = f"""You are an expert interviewer for {role} ({domain if domain else 'General'}).
Interview mode: {mode}.
Ask a new, relevant question for this role and mode.
Do not repeat previous questions.
Previous Q&A: {prev_qas if prev_qas else 'None'}.
Return only the question."""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=100,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def evaluate_answer(role, domain, mode, question, answer):
    # Prompt for evaluation
    prompt = f"""You are an expert interviewer for {role} ({domain if domain else 'General'}).
Interview mode: {mode}.
Question: {question}
Candidate's answer: {answer}
Evaluate the answer for clarity, correctness, completeness, and (if behavioral) use of real-world examples, or (if technical) technical accuracy.
Give feedback, a score out of 10, and suggestions for improvement.
Respond in JSON: {{"feedback": "...", "score": 7, "suggestions": "..."}}"""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=200,
        temperature=0.7,
    )
    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"feedback": "Could not parse feedback.", "score": 0, "suggestions": ""}


def summarize_session(qas):
    # Prompt for summary
    prompt = f"""You are an expert interviewer.
Given this interview Q&A and feedback: {qas}
Summarize the candidate's strengths, areas to improve, and suggest resources.
Give a final score out of 10.
Respond in JSON: {{"strengths": "...", "improvements": "...", "resources": "...", "final_score": 8}}"""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=200,
        temperature=0.7,
    )
    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"strengths": "", "improvements": "", "resources": "", "final_score": 0}


# --- Routes ---

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session['role'] = request.form['role']
        session['domain'] = request.form.get('domain', '')
        session['mode'] = request.form['mode']
        session['qas'] = []
        session['current_q'] = get_interview_question(session['role'], session['domain'], session['mode'], [])
        session['step'] = 1
        return redirect(url_for('interview'))
    return render_template("index.html")


@app.route("/interview", methods=["GET", "POST"])
def interview():
    if 'current_q' not in session:
        return redirect(url_for('index'))
    
    feedback = None
    step = session.get('step', 1)  # prevent KeyError
    
    if request.method == "POST":
        user_answer = request.form['answer']
        eval_result = evaluate_answer(session['role'], session['domain'], session['mode'], session['current_q'], user_answer)
        
        session['qas'].append({
            "question": session['current_q'],
            "answer": user_answer,
            "feedback": eval_result.get("feedback", ""),
            "score": eval_result.get("score", 0),
            "suggestions": eval_result.get("suggestions", "")
        })
        
        feedback = eval_result
        step += 1
        session['step'] = step
        
        if step > 5:  # after 5 questions go to summary
            return redirect(url_for('summary'))
        
        session['current_q'] = get_interview_question(session['role'], session['domain'], session['mode'], session['qas'])
    
    return render_template("interview.html", question=session['current_q'], feedback=feedback, step=step)


@app.route("/summary")
def summary():
    summary_data = summarize_session(session['qas'])
    return render_template("summary.html", qas=session['qas'], summary=summary_data)


# --- Run the app ---
if __name__ == "__main__":
    app.run(debug=True)
