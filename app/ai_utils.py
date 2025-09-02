import os
import google.generativeai as genai
from bs4 import BeautifulSoup # To clean HTML from diary entries

def generate_task_summary(tasks):
    # ... (this function remains the same)
    try:
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-flash')
        task_list_str = ""
        for task in tasks:
            status = "Completed" if task.get('completed') else "Pending"
            priority = task.get('priority', {}).get('level', 'N/A')
            task_list_str += f"- {task['content']} (Priority: {priority}, Status: {status})\n"
        if not task_list_str:
            return "You have no tasks right now. A great time to plan your next move!"
        prompt = f"""
        You are a helpful and encouraging student productivity assistant.
        Based on the following list of tasks for a student, generate a short, motivating, one-paragraph summary (2-3 sentences max) for their dashboard.
        Be friendly and positive. Mention the number of pending tasks and highlight the high-priority ones if they exist.
        Here are the tasks:
        {task_list_str}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI summary generation failed: {e}")
        return "Focus on your next task and make today productive!"

# --- UPDATED CHAT FUNCTION ---
def get_ai_chat_response(question, user_notes, user_tasks, user_diary_entries):
    """
    Generates a conversational response using notes, tasks, AND diary entries as context.
    """
    try:
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Format context into strings for the prompt
        notes_context = "\n".join([f"- Title: {note['title']}\n  Content: {note['content']}" for note in user_notes])
        tasks_context = "\n".join([f"- {task['content']} (Priority: {task.get('priority', {}).get('level', 'N/A')})" for task in user_tasks if not task.get('completed')])
        
        # Format and clean diary entries (remove HTML tags)
        diary_context = ""
        for entry in user_diary_entries:
            soup = BeautifulSoup(entry['content'], 'html.parser')
            clean_content = soup.get_text(separator="\n")
            entry_date = entry['timestamp'].strftime('%B %d, %Y')
            diary_context += f"- Entry from {entry_date}:\n{clean_content}\n"

        if not notes_context: notes_context = "No notes provided."
        if not tasks_context: tasks_context = "No pending tasks."
        if not diary_context: diary_context = "No recent diary entries provided."

        prompt = f"""
        You are the Student Companion AI. Your role is to be a helpful, encouraging, and intelligent assistant for a student.
        Use the provided context from the student's own notes, task list, and recent diary entries to answer their questions.
        If the question is about their feelings, mood, or past events, refer to the diary entries respectfully.
        If the question is about their work, refer to the notes and tasks.
        If the question is general, answer it as a helpful AI.
        Keep your answers concise and supportive.

        --- CONTEXT: Student's Notes ---
        {notes_context}
        
        --- CONTEXT: Student's Pending Tasks ---
        {tasks_context}

        --- CONTEXT: Student's Recent Diary Entries ---
        {diary_context}

        --- STUDENT'S QUESTION ---
        {question}

        Your Answer:
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI chat response generation failed: {e}")
        return "Sorry, I'm having trouble connecting to my brain right now. Please try again in a moment."