from flask import Flask, render_template, request, redirect, url_for
import csv
from datetime import datetime
import os
import pandas as pd
import matplotlib.pyplot as plt
import json

app = Flask(__name__)

# File to store selected questions for each child
CHILD_QUESTIONS_FILE = "child_questions.json"

# Ensure the file exists (creates an empty JSON if it doesn't exist)
if not os.path.exists(CHILD_QUESTIONS_FILE):
    with open(CHILD_QUESTIONS_FILE, "w") as f:
        json.dump({}, f)

# Predefined question groups and their questions
PREDEFINED_QUESTIONS = {
    "Behavior and Emotions": [
        "On a scale of 1–5, how stable was your child’s mood today?",
        "How many emotional outbursts did your child have today?",
        "How many meltdowns occurred today?",
        "How many instances of aggression occurred today?",
        "How many minutes did the longest meltdown last?",
        "On a scale of 1–5, how intense was the most severe meltdown?",
        "How many times did your child direct aggression toward others?",
        "How many times did your child direct aggression toward themselves?"
    ],
    "Daily Activities": [
        "How many hours did your child sleep last night?",
        "What time did your child wake up?",
        "What time did your child fall asleep?",
        "How many naps did your child take today?",
        "How many minutes did your child nap today?",
        "On a scale of 1–5, how well did your child eat today?",
        "How many meals/snacks did your child eat today?",
        "How many new foods did your child try today?",
        "How many minutes/hours did your child spend on screens today?",
        "How many minutes of physical activity did your child get today?",
        "On a scale of 1–5, how engaged was your child in physical activities?"
    ],
    "Sensory Concerns": [
        "How many sensory-related behaviors occurred today?",
        "How many times did your child react strongly to sensory input today?",
        "On a scale of 1–5, how sensitive was your child to sensory input today?",
        "How many times did your child engage in sensory-seeking behaviors today?",
        "How many minutes did your child spend in sensory play today?",
        "How many times did your child show sensitivity to touch today?"
    ],
    "Cognitive and Academic Performance": [
        "On a scale of 1–5, how well was your child able to focus on tasks today?",
        "How many times did your child lose focus during structured activities?",
        "How many minutes of focused activity was your child able to sustain at one time?",
        "How many tasks did your child complete today?",
        "How many learning-related frustrations did your child express today?",
        "How many minutes did your child spend on schoolwork or learning activities today?"
    ],
    "Health and Medical": [
        "How many times did your child complain about physical discomfort today?",
        "How many times did your child wake up during the night?",
        "How long did it take (in minutes) for your child to fall asleep?",
        "How many doses of medication were administered today?",
        "How many side effects were observed today (e.g., drowsiness, appetite loss)?",
        "How many seizures or unusual movements occurred today?",
        "On a scale of 1–5, how severe were your child’s symptoms today?"
    ],
    "Parent and Caregiver Observations": [
        "On a scale of 1–5, how stressed did you feel today while caring for your child?",
        "How many minutes did you spend on self-care today?",
        "How many positive interactions did you have with your child today (e.g., hugs, playing together)?",
        "What was the most challenging part of caring for your child today?",
        "What was the most positive part of your child’s day today?"
    ]
}

# File to store the journal entries
CSV_FILE = "child_journal.csv"

# Questions for the daily journal
QUESTIONS = [
    "How many meltdowns did your child have today?",
    "Did any meltdowns involve damaging property?",
    "Did any meltdowns involve hurting themselves or others?",
    "What led up to these meltdowns?",
    "On a scale from 1-5, how well did your child eat today?",
    "What time did they wake up?",
    "What time did they fall asleep?",
    "How many hours of sleep did they have last night?",
    "How many hours did they nap?",
    "Did they seem rested this morning?",
]

def initialize_csv():
    """Ensure the CSV file exists and add missing headers."""
    headers = ["Date/Time", "Child Name"] + QUESTIONS

    if os.path.exists(CSV_FILE):
        # Read existing headers
        with open(CSV_FILE, mode="r", newline="") as file:
            reader = csv.reader(file)
            existing_headers = next(reader, [])

        # Add missing headers
        for header in headers:
            if header not in existing_headers:
                existing_headers.append(header)

        # Rewrite the CSV with updated headers
        rows = list(reader)  # Save existing rows
        with open(CSV_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(existing_headers)  # Write updated headers
            writer.writerows(rows)  # Write back existing rows
    else:
        # Create a new file with the correct headers
        with open(CSV_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

def save_to_csv(child_name, responses):
    """Save the responses to a CSV file without overwriting existing data."""
    initialize_csv()  # Ensure headers are up-to-date

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Load existing data
    updated = False
    rows = []
    with open(CSV_FILE, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        for row in reader:
            # Update the current child's entry if it matches the timestamp
            if row["Child Name"] == child_name and row["Date/Time"] == now:
                for i, question in enumerate(QUESTIONS):
                    row[question] = responses[i] if i < len(responses) else row.get(question)
                updated = True
            rows.append(row)

    # If not updated, add a new row
    if not updated:
        new_row = {header: "" for header in headers}
        new_row["Date/Time"] = now
        new_row["Child Name"] = child_name
        for i, question in enumerate(QUESTIONS):
            new_row[question] = responses[i] if i < len(responses) else ""
        rows.append(new_row)

    # Write updated data back to the file
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

def get_existing_children():
    """Get all child names from child_questions.json."""
    if not os.path.exists(CHILD_QUESTIONS_FILE):
        return []
    with open(CHILD_QUESTIONS_FILE, "r") as f:
        child_questions = json.load(f)
    return sorted(child_questions.keys())

@app.route('/data_entry', methods=["GET", "POST"])
def data_entry():
    """Display the form for entering daily responses."""
    # Get the list of all children
    children = get_existing_children()
    print(f"Children: {children}")  # Debugging

    # Determine the selected child
    if request.method == "POST":
        # Get the selected child from the form
        selected_child = request.form.get("child_name", "").strip()
    else:
        # Get the selected child from query parameters or default to the first child
        selected_child = request.args.get("child", children[0] if children else "")
    print(f"Selected child: {selected_child}")  # Debugging

    # Load the child-specific questions from the JSON file
    questions = []
    if selected_child:
        with open(CHILD_QUESTIONS_FILE, "r") as f:
            child_questions = json.load(f)
        questions = child_questions.get(selected_child, [])
        print(f"Questions for {selected_child}: {questions}")  # Debugging

    return render_template(
        "data_entry.html",
        children=children,
        selected_child=selected_child,
        questions=questions,
        enumerate=enumerate
    )

@app.route('/submit', methods=["POST"])
def submit():
    """Handle the form submission."""
    child_name = request.form.get("child_name", "").strip()

    # Load questions for the selected child
    with open(CHILD_QUESTIONS_FILE, "r") as f:
        child_questions = json.load(f)
    questions = child_questions.get(child_name, [])

    # Process responses
    responses = []
    for i, question in enumerate(questions):
        response = request.form.get(f"q{i}", "").strip()
        if question.lower().startswith("did"):
            # Convert Yes/No responses to integers
            response = int(response) if response in ["1", "0"] else None
        elif question.lower().startswith("on a scale of 1–5"):
            # Ensure rating is within 1–5
            response = int(response) if response.isdigit() and 1 <= int(response) <= 5 else None
        responses.append(response)

    # Save the responses
    save_to_csv(child_name, responses)

    return redirect(url_for("thank_you"))
    
@app.route('/thank_you')
def thank_you():
    """Display a thank-you message."""
    return "Thank you! Your responses have been saved."

@app.route('/trends')
def view_trends():
    """Generate and display trends."""
    if not os.path.exists(CSV_FILE):
        return "No data available to visualize."
    df = pd.read_csv(CSV_FILE)
    df["Date/Time"] = pd.to_datetime(df["Date/Time"])
    df["Date"] = df["Date/Time"].dt.date
    meltdowns_per_day = df.groupby("Date")["How many meltdowns did your child have today?"].sum()
    plt.figure(figsize=(8, 5))
    meltdowns_per_day.plot(kind="bar", color="skyblue", title="Meltdowns Per Day")
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Number of Meltdowns", fontsize=12)
    plt.xticks(rotation=30, fontsize=10)
    plt.tight_layout()
    img_path = "static/trends.png"
    plt.savefig(img_path)
    plt.close()
    return f'<h1>Trends</h1><img src="/{img_path}" alt="Trends" style="max-width: 100%; height: auto;">'

    @app.route('/dashboard', methods=["GET", "POST"])
    def dashboard():
        print("Dashboard route reached")  # Debugging

        if not os.path.exists(CSV_FILE):
            print("CSV file not found.")
            return "No data available to visualize"

    # Read the CSV file
    try:
        df = pd.read_csv(CSV_FILE)
        print("CSV Data:\n", df.head())  # Debug: Show the first few rows of the CSV
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return f"Error reading CSV: {e}"

    # Ensure datetime conversion
    try:
        df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
        df["Date"] = df["Date/Time"].dt.date
        print("Parsed Date/Time Column:\n", df["Date/Time"])  # Debug: Show parsed dates
    except Exception as e:
        print(f"Error parsing dates: {e}")
        return f"Error parsing dates: {e}"

    # Strip whitespace from the Child Name column
    df["Child Name"] = df["Child Name"].str.strip()
    print("Child Name Column:\n", df["Child Name"].unique())  # Debug: Show unique child names

    # Get unique child names
    child_names = sorted(df["Child Name"].dropna().unique())

    # Get the selected child from the form or show data for all children
    selected_child = request.form.get("child_name")  # Form data (POST)
    if not selected_child:  # If no POST data, check query parameters (GET)
        selected_child = request.args.get("child_name", "All")
    print("Selected Child:", selected_child)  # Debug: Show selected child

    # Filter the dataframe based on the selected child
    if selected_child == "All":
        filtered_df = df
    else:
        filtered_df = df if not selected_child or selected_child == "All" else df[df["Child Name"] == selected_child]
        print(f"Filtered Data for {selected_child}:\n", filtered_df)  # Debugging

    # Handle empty data for filtered children
    if filtered_df.empty:
        print(f"No data available for {selected_child}.")
        return render_template(
            "dashboard.html",
            children=child_names,
            selected_child=selected_child,
            charts=[]
        )

    # Dynamically find questions for the child
    with open(CHILD_QUESTIONS_FILE, "r") as f:
        child_questions = json.load(f)

    questions = []
    if selected_child and selected_child in child_questions:
        questions = child_questions[selected_child]
    elif not selected_child or selected_child == "All":
        questions = list(df.columns)[2:]  # Use all questions in the dataset for "All"

    print("Selected Questions:", questions)  # Debug: Show questions for the child

    # Generate bar charts for numeric columns (e.g., rating questions)
    charts = []
    for question in questions:
        if question in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[question]):
            chart_path = f"static/{'_'.join(question.split())}_chart.png"
            filtered_df.groupby("Date")[question].mean().plot(kind="bar", title=question, figsize=(8, 5), color="skyblue")
            plt.xlabel("Date")
            plt.ylabel("Average")
            plt.xticks(rotation=30)
            plt.tight_layout()
            plt.savefig(chart_path)
            plt.close()
            charts.append({"title": question, "path": chart_path})
            print(f"Generated chart for {question}: {chart_path}")  # Debug: Confirm chart generation

    return render_template(
        "dashboard.html",
        children=child_names,
        selected_child=selected_child,
        charts=charts
    )

@app.route('/')
def index():
    """Main page to list children and manage questions."""
    with open(CHILD_QUESTIONS_FILE, "r") as f:
        child_questions = json.load(f)
    children = list(child_questions.keys()) if child_questions else []
    return render_template("index.html", children=children)

@app.route('/add_child', methods=["POST"])
def add_child():
    """Add a new child to the system."""
    child_name = request.form.get("child_name").strip()
    with open(CHILD_QUESTIONS_FILE, "r") as f:
        child_questions = json.load(f)
    if child_name not in child_questions:
        child_questions[child_name] = []
    with open(CHILD_QUESTIONS_FILE, "w") as f:
        json.dump(child_questions, f)
    return redirect(url_for("index"))

@app.route('/select_questions/<child_name>', methods=["GET", "POST"])
def select_questions(child_name):
    """Question selection interface for a child."""
    with open(CHILD_QUESTIONS_FILE, "r") as f:
        child_questions = json.load(f)

    if request.method == "POST":
        # Save selected predefined and custom questions
        selected_questions = request.form.getlist("questions")  # Predefined questions
        custom_questions = request.form.getlist("custom_questions")  # Custom questions
        child_questions[child_name] = selected_questions + custom_questions

        # Save to JSON file
        with open(CHILD_QUESTIONS_FILE, "w") as f:
            json.dump(child_questions, f)

        # Ensure CSV headers are updated
        initialize_csv()

        return redirect(url_for("index"))

    # Separate predefined and custom questions for rendering
    selected_questions = child_questions.get(child_name, [])
    predefined_questions = {category: [] for category in PREDEFINED_QUESTIONS}
    custom_questions = []

    for question in selected_questions:
        found = False
        for category, questions in PREDEFINED_QUESTIONS.items():
            if question in questions:
                predefined_questions[category].append(question)
                found = True
                break
        if not found:
            custom_questions.append(question)

    return render_template(
        "select_questions.html",
        child_name=child_name,
        predefined_questions=PREDEFINED_QUESTIONS,
        selected_questions=predefined_questions,
        custom_questions=custom_questions,
    )

if __name__ == "__main__":
    initialize_csv()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)