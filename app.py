from flask import Flask, render_template, request
import textstat
import re
import requests
from symspellpy import SymSpell, Verbosity
import pkg_resources

app = Flask(__name__)

# Initialize SymSpell for spelling correction
sym_spell = SymSpell()
dictionary_path = pkg_resources.resource_filename("symspellpy", "frequency_dictionary_en_82_765.txt")
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

def check_grammar(text):
    url = "https://api.languagetool.org/v2/check"
    params = {
        "text": text,
        "language": "en-US"
    }
    response = requests.post(url, data=params)
    if response.status_code == 200:
        result = response.json()
        suggestions = []
        for match in result.get("matches", []):
            if "replacements" in match and match["replacements"]:
                suggestions.append(match["replacements"][0]["value"])
        return suggestions if suggestions else ["No grammar issues found"]
    return ["Grammar check failed"]
    print("GrammarBot API response:", response.json())

def correct_spelling(text):
    words = text.split()
    corrected_words = []
    for word in words:
        suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
        corrected_words.append(suggestions[0].term if suggestions else word)
    return " ".join(corrected_words)

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

@app.route('/', methods=['GET', 'POST'])
def index():
    feedback = ""
    corrected_essay = ""
    
    if request.method == 'POST':
        essay = request.form['essay']
        word_count = len(essay.split())
        corrected_spelling = correct_spelling(essay)
        readability = textstat.flesch_reading_ease(essay)
        grammar_feedback = check_grammar(essay)
        organization_feedback = analyze_organization(essay)
        
        feedback = f"Word Count: {word_count}<br>"
        feedback += f"Readability Score: {readability:.2f}<br>"
        feedback += "Grammar Feedback: " + ', '.join(grammar_feedback) + "<br>"
        feedback += "Organization Feedback: " + ', '.join(organization_feedback)
        
        corrected_essay = corrected_spelling
        
    return render_template('index.html', feedback=feedback, corrected_essay=corrected_essay)
print("Received essay:", essay)
print("Grammar feedback:", grammar_feedback)
print("Corrected essay:", corrected_essay)
if __name__ == '__main__':
    app.run(debug=True)
