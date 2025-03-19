from flask import Flask, render_template, request, jsonify
import textstat
import re
import requests
from symspellpy import SymSpell, Verbosity
import pkg_resources

sym_spell = SymSpell()
dictionary_path = pkg_resources.resource_filename("symspellpy", "frequency_dictionary_en_82_765.txt")
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

app = Flask(__name__)

def check_spelling(text):
    words = text.split()
    misspelled = {}

    for word in words:
        suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
        
        if not suggestions or word.lower() not in [s.term.lower() for s in suggestions]:  
            # If no valid suggestions or word is not a correct suggestion
            best_suggestion = suggestions[0].term if suggestions else "No suggestion"
            misspelled[word] = best_suggestion  

    return misspelled  # Returns a dictionary of {wrong_word: suggested_correction}

def correct_grammar(text):
    url = "https://api.languagetool.org/v2/check"
    params = {
        "text": text,
        "language": "en-US"
    }
    response = requests.post(url, data=params)
    
    if response.status_code == 200:
        result = response.json()
        matches = result.get("matches", [])
        
        if not matches:
            return text, 0  # No corrections needed, 0 grammar issues

    corrected_text = text
    for match in reversed(matches):
    if match["replacements"]:
        suggestion = match["replacements"][0]["value"]
        start, end = match["offset"], match["offset"] + match["length"]
        corrected_text = corrected_text[:start] + suggestion + corrected_text[end:]

return corrected_text, len(matches)  # Moved outside loop
    else:
        return text, 0  # Return original text with 0 issues if API fails
                
    
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


def calculate_grade(readability, spelling_mistakes, grammar_feedback, organization_feedback):
    score = 100  # Start with full points

    # **Readability Impact**
    if readability < 30:
        score -= 30
    elif readability < 50:
        score -= 20
    elif readability < 70:
        score -= 10

    # **Spelling Mistakes Deduction**
    spelling_count = len(spelling_mistakes)  # Dictionary length gives the number of mistakes
    score -= min(spelling_count * 2, 15)  # Deduct 2 points per mistake, max 15

    # **Grammar Issues Deduction (Fixed)**
    if isinstance(grammar_feedback, str):  # Convert string to issue count
        grammar_count = grammar_feedback.count(" | ") + 1 if " | " in grammar_feedback else (0 if grammar_feedback == "No grammar issues found." else 1)
    else:
        grammar_count = len(grammar_feedback) if isinstance(grammar_feedback, list) else 0
    score -= min(grammar_count * 2, 15)  # Deduct 2 points per issue, max 15

    # **Organization Feedback Deduction**
    organization_issues = len(organization_feedback) if isinstance(organization_feedback, list) else 0
    score -= min(organization_issues * 5, 15)  # Deduct 5 points per issue, max 15

    # **Ensure score stays within 0-100 range**
    return round(max(0, min(score, 100)), 2)  # Round to 2 decimal places for precision
 
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.get_json()
        essay = data.get("essay", "")

        word_count = len(essay.split())
        spelling_mistakes = check_spelling(essay)
        spelling_feedback = " | ".join(f"{word} → {correction}" for word, correction in spelling_mistakes.items()) if spelling_mistakes else "No spelling mistakes found."
        readability = textstat.flesch_reading_ease(essay)
        organization_feedback = analyze_organization(essay)
        corrected_essay, grammar_issues = correct_grammar(essay)  # Now getting grammar issue count

        overall_grade = calculate_grade(readability, spelling_mistakes, grammar_issues, organization_feedback)  # Pass grammar_issues instead of undefined variable

        return jsonify({
            "word_count": word_count,
            "spelling_mistakes": spelling_feedback,
            "readability": readability,
            "organization_feedback": " | ".join(organization_feedback),
            "corrected_essay": corrected_essay,
            "overall_grade": overall_grade
        })

    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
