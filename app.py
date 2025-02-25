from flask import Flask, render_template, request, jsonify
import textstat
import re
import requests
from symspellpy import SymSpell, Verbosity
import pkg_resources

app = Flask(__name__)

# Load SymSpell
sym_spell = SymSpell(max_dictionary_edit_distance=2)
sym_spell.load_dictionary("frequency_dictionary_en_82_765.txt", term_index=0, count_index=1)

def check_spelling(text):
    words = text.split()
    misspelled = []
    
    for word in words:
        suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
        if not suggestions:
            misspelled.append(word)  # If no suggestions, consider it misspelled
    
    return misspelled    

def correct_grammar(text):
    url = "https://api.languagetool.org/v2/check"
    params = {
        "text": text,
        "language": "en-US"
    }

    response = requests.post(url, data=params)

    if response.status_code == 200:
        result = response.json()
        corrected_text = text

        # Apply corrections from LanguageTool
        for match in reversed(result.get("matches", [])):
            offset = match["offset"]
            length = match["length"]
            replacement = match["replacements"][0]["value"] if match["replacements"] else ""
            corrected_text = corrected_text[:offset] + replacement + corrected_text[offset+length:]

        return corrected_text
    else:
        return text  # Return original text if API call fails= []
            
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

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.get_json()
        essay = data.get("essay", "")

        word_count = len(essay.split())
        spelling_mistakes = check_spelling(essay)
        readability = textstat.flesch_reading_ease(essay)
        grammar_feedback = check_grammar(essay)
        organization_feedback = analyze_organization(essay)
        corrected_essay = correct_grammar(essay)

        return jsonify({
            "word_count": word_count,
            "spelling_mistakes": spelling_mistakes,
            "readability": readability,
            "grammar_feedback": grammar_feedback,
            "organization_feedback": organization_feedback,
            "corrected_essay": corrected_essay
        })

    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
