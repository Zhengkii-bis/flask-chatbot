from flask import Flask, render_template, request
import textstat
import requests
from spellchecker import SpellChecker
import re

app = Flask(__name__)  
spell = SpellChecker()

# Grammar check function
def check_grammar(text):
    url = "https://services.gingersoftware.com/Ginger/correct/jsonSecured/GingerTheText"
    params = {
        "lang": "US",
        "clientVersion": "2.0",
        "apiKey": "6ae0c3a0-afdc-4532-a810-82ded0054236",
        "text": text
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        result = response.json()
        corrections = []
        for suggestion in result.get("LightGingerTheTextResult", []):
            if "Suggestions" in suggestion and suggestion["Suggestions"]:
                corrections.append(suggestion["Suggestions"][0]["Text"])
        return corrections if corrections else ["No grammar issues found"]
    
    return ["Grammar check failed"]

# Organization analysis function
def analyze_organization(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    num_sentences = len(sentences)
    avg_sentence_length = sum(len(s.split()) for s in sentences) / num_sentences if num_sentences else 0
    paragraphs = text.split("\n")
    num_paragraphs = len([p for p in paragraphs if p.strip()])

    feedback = []
    if avg_sentence_length > 25:
        feedback.append("Sentences may be too long. Consider breaking them up.")
    elif avg_sentence_length < 8:
        feedback.append("Sentences may be too short. Consider expanding ideas.")

    if num_paragraphs < 2:
        feedback.append("Consider adding more paragraphs to improve readability.")

    return feedback if feedback else ["Organization looks good."]

# Route for handling form submission
@app.route('/', methods=['GET', 'POST'])
def index():
    feedback = ""
    if request.method == 'POST':
        essay = request.form['essay']
        word_count = len(essay.split())
        spelling_mistakes = list(spell.unknown(essay.split()))
        readability = textstat.flesch_reading_ease(essay)
        grammar_feedback = check_grammar(essay)
        organization_feedback = analyze_organization(essay)

        # Formatting the feedback output
        feedback = f"""
            <strong>Word Count:</strong> {word_count} <br>
            <strong>Spelling Mistakes:</strong> {', '.join(spelling_mistakes) if spelling_mistakes else 'None'} <br>
            <strong>Readability Score:</strong> {readability:.2f} <br>
            <strong>Grammar Feedback:</strong> {', '.join(grammar_feedback)} <br>
            <strong>Organization Feedback:</strong> {', '.join(organization_feedback)}
        """

    return render_template('index.html', feedback=feedback)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
