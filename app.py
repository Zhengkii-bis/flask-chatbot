from flask import Flask, render_template, request
import textstat
import language_tool_python
from spellchecker import SpellChecker

app = Flask(__name__)
tool = language_tool_python.LanguageTool('en-US')
spell = SpellChecker()

def analyze_essay(essay):
    feedback = []
    
    # Word Count
    word_count = len(essay.split())
    feedback.append(f"<strong>Word Count:</strong> {word_count}")
    
    # Readability Score
    readability_score = textstat.flesch_reading_ease(essay)
    feedback.append(f"<strong>Readability Score:</strong> {readability_score:.2f} (Higher is easier to read)")
    
    # Spelling Mistakes
    words = essay.split()
    misspelled = spell.unknown(words)
    if misspelled:
        feedback.append(f"<strong>Potential Spelling Mistakes:</strong> {', '.join(misspelled)}")
    else:
        feedback.append("<strong>No spelling mistakes detected.</strong>")
    
    # Grammar Check
    grammar_errors = tool.check(essay)
    if grammar_errors:
        feedback.append(f"<strong>Grammar Issues Found:</strong> {len(grammar_errors)}")
        for error in grammar_errors[:5]:  # Show first 5 errors only
            feedback.append(f"- {error.message} (<em>Suggestion:</em> {', '.join(error.replacements)})")
    else:
        feedback.append("<strong>No grammar issues detected.</strong>")
    
    # Organization Check (Basic: Checks if paragraphs are present)
    paragraphs = essay.strip().split("\n")
    if len(paragraphs) < 2:
        feedback.append("<strong>Consider breaking your essay into paragraphs for better organization.</strong>")
    else:
        feedback.append("<strong>Your essay has a good paragraph structure.</strong>")
    
    return "<br>".join(feedback)

@app.route("/", methods=["GET", "POST"])
def index():
    feedback = ""
    if request.method == "POST":
        essay = request.form.get("essay")
        if essay:
            feedback = analyze_essay(essay)
        else:
            feedback = "<strong>Please enter an essay.</strong>"
    
    return render_template("index.html", feedback=feedback)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
    
