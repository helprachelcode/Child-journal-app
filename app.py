from flask import Flask, render_template, request, redirect, url_for
import csv
from datetime import datetime
import os
import pandas as pd
import matplotlib.pyplot as plt
import json

app = Flask(__name__, static_folder="static")

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


def initialize_csv():
    """Ensure the CSV file exists and add missing headers dynamically."""
    # Default headers
    headers = ["Date/Time", "Child Name"]

    # Load child-specific questions from the JSON file
    if os.path.exists(CHILD_QUESTIONS_FILE):
        with open(CHILD_QUESTIONS_FILE, "r") as f:
            child_questions = json.load(f)
            # Add all unique questions from all children
            for child, questions in child_questions.items():
                headers.extend(questions)
            headers = list(set(headers))  # Remove duplicates and maintain unique headers

    if os.path.exists(CSV_FILE):
        # Read existing headers
        with open(CSV_FILE, mode="r", newline="") as file:
            reader = csv.reader(file)
            rows = list(reader)  # Save existing rows
            existing_headers = rows[0] if rows else []

        # Add missing headers
        for header in headers:
            if header not in existing_headers:
                existing_headers.append(header)

        # Rewrite the CSV with updated headers
        with open(CSV_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(existing_headers)  # Write updated headers
            writer.writerows(rows[1:])  # Write back existing rows, skipping the old header
    else:
        # Create a new file with the correct headers
        with open(CSV_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

def save_to_csv(child_name, responses):
    """Save the responses to a CSV file without overwriting existing data."""
    initialize_csv()  # Ensure headers are up-to-date

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Load child-specific questions from JSON
    with open(CHILD_QUESTIONS_FILE, "r") as f:
        child_questions = json.load(f)
    questions = child_questions.get(child_name, [])

    # Load existing data
    updated = False
    rows = []
    with open(CSV_FILE, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        for row in reader:
            # Update the current child's entry if it matches the timestamp
            if row["Child Name"] == child_name and row["Date/Time"] == now:
                for i, question in enumerate(questions):
                    row[question] = responses[i] if i < len(responses) else row.get(question)
                updated = True
            rows.append(row)

    # If not updated, add a new row
    if not updated:
        new_row = {header: "" for header in headers}
        new_row["Date/Time"] = now
        new_row["Child Name"] = child_name
        for i, question in enumerate(questions):
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

@app.route('/submit', methods=["GET", "POST"])
def submit():
    """Handle the form submission."""
    success_message = None  # Initialize the success message to None

    if request.method == "POST":
        action_type = request.form.get("action_type", "submit_data")
        child_name = request.form.get("child_name", "").strip()

        if action_type == "submit_data":
            # Handle data submission
            with open(CHILD_QUESTIONS_FILE, "r") as f:
                child_questions = json.load(f)
            questions = child_questions.get(child_name, [])

            # Process responses
            responses = []
            for i, question in enumerate(questions):
                response = request.form.get(f"q{i}", "").strip()
                if question.lower().startswith("did"):
                    response = int(response) if response in ["1", "0"] else None
                elif question.lower().startswith("on a scale of 1–5"):
                    response = int(response) if response.isdigit() and 1 <= int(response) <= 5 else None
                responses.append(response)

            # Save the responses
            save_to_csv(child_name, responses)

            # Set the success message
            success_message = "Your data has been successfully submitted."

        # For "change_child", no data submission, no success message
        # Just update selected_child and reload questions
        selected_child = child_name
        with open(CHILD_QUESTIONS_FILE, "r") as f:
            child_questions = json.load(f)
        questions = child_questions.get(selected_child, [])
    else:
        # Handle GET request
        children = get_existing_children()
        selected_child = children[0] if children else None
        with open(CHILD_QUESTIONS_FILE, "r") as f:
            child_questions = json.load(f)
        questions = child_questions.get(selected_child, [])

    # Reload the form (GET or POST)
    children = get_existing_children()
    return render_template(
        "data_entry.html",
        success_message=success_message,
        children=children,
        selected_child=selected_child,
        questions=questions,
        enumerate=enumerate
    )
    
@app.route('/dashboard')
def dashboard_overview():
    """Dashboard overview page with a list of children."""
    children = get_existing_children()
    if not children:
        return "No children available. Please add a child first."
    return render_template("dashboard_overview.html", children=children)

@app.route('/dashboard/<child_name>')
def child_dashboard(child_name):
    """Child-specific dashboard showing charts based on selected questions."""
    # Clear the static folder before generating new charts
    clear_static_folder()

    print(f"Dashboard for child: {child_name}")
    if not os.path.exists(CSV_FILE):
        return "No data available to visualize."

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

    # Filter by child name
    df["Child Name"] = df["Child Name"].str.strip()
    filtered_df = df[df["Child Name"] == child_name]
    print(f"Filtered Data for {child_name}:\n", filtered_df)  # Debug: Show filtered data

    if filtered_df.empty:
        return render_template("child_dashboard.html", child_name=child_name, charts=[])

    # Dynamically find questions for the child
    with open(CHILD_QUESTIONS_FILE, "r") as f:
        child_questions = json.load(f)

    questions = child_questions.get(child_name, [])
    print("Selected Questions:", questions)  # Debug: Show questions for the child

    # Filter out empty or invalid questions
    questions = [q for q in questions if q.strip() and q in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[q])]

    # Generate line charts for numeric columns
    charts = []
    import re

    def sanitize_filename(filename):
        """Sanitize a filename by removing special characters."""
        filename = re.sub(r'[^\w\s]', '', filename)  # Remove all non-alphanumeric and non-space characters
        filename = re.sub(r'\s+', '_', filename)    # Replace spaces with underscores
        return filename

    for question in questions:
        # Generate the sanitized chart file path
        sanitized_question = sanitize_filename(question)
        chart_path = f"static/{child_name}_{sanitized_question}_chart.png"
        try:
            grouped_data = filtered_df.groupby("Date")[question].mean()
            grouped_data.plot(kind="line", title=question, figsize=(10, 6), marker="o")

            plt.xlabel("Date")
            plt.ylabel("Average")
            plt.xticks(rotation=45)

            # Limit x-axis labels to reduce overcrowding
            num_labels = 10  # Adjust this number as needed
            if len(grouped_data) > num_labels:
                step = max(1, len(grouped_data) // num_labels)
                plt.gca().set_xticks(grouped_data.index[::step])

            plt.tight_layout()
            plt.savefig(chart_path)
            plt.close()
            charts.append({"title": question, "path": chart_path})
            print(f"Generated chart for {question}: {chart_path}")
        except Exception as e:
            print(f"Error generating chart for {question}: {e}")

    # Generate correlation heat map
    numeric_columns = filtered_df.select_dtypes(include=['number'])
    if not numeric_columns.empty:
        correlation_matrix = numeric_columns.corr()
        heatmap_path = f"static/{child_name}_heatmap.png"
        try:
            import seaborn as sns
            plt.figure(figsize=(10, 8))
            print("Generating heat map...")
            sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f")
            print("Heat map generated. Saving chart...")
            plt.title(f"Correlation Heatmap for {child_name}")
            plt.savefig(heatmap_path)
            print(f"Heat map saved at: {chart_path}")
            plt.close()
        except Exception as e:
            heatmap_path = None
            print(f"Error generating heatmap: {e}")
    else:
        heatmap_path = None

    return render_template("child_dashboard.html", child_name=child_name, charts=charts, heatmap_path=heatmap_path)

def clear_static_folder():
    """Delete all files in the static folder."""
    STATIC_FOLDER = "static"
    for filename in os.listdir(STATIC_FOLDER):
        file_path = os.path.join(STATIC_FOLDER, filename)
        try:
            if os.path.isfile(file_path):  # Check if it's a file
                os.unlink(file_path)  # Delete the file
                print(f"Deleted: {file_path}")
            elif os.path.isdir(file_path):  # Check if it's a directory (if necessary)
                os.rmdir(file_path)  # Remove the directory
                print(f"Deleted directory: {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")

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
        updated_custom_questions = request.form.getlist("custom_questions")  # Edited custom questions
        new_custom_question = request.form.get("new_custom_question")  # New custom question
        new_custom_question_checkbox = request.form.get("new_custom_question_checkbox")

        # Add the new custom question only if the checkbox is selected and the input is not empty
        if new_custom_question and new_custom_question_checkbox:
            updated_custom_questions.append(new_custom_question.strip())

        child_questions[child_name] = selected_questions + updated_custom_questions

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
        custom_questions=custom_questions,  # Send current custom questions
    )


if __name__ == "__main__":
    initialize_csv()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)