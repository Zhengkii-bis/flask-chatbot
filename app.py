from flask import Flask, render_template, request
import textstat
from gingerit.gingerit import GingerIt
from symspellpy import SymSpell, Verbosity
import re
import os

app = Flask(__name__)

# Load SymSpell for spelling correction
sym_spell = SymSpell()
dictionary_path = "frequency_dictionary_en_82_765.txt"

if os.path.exists(dictionary_path):
    sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
else:
    print("Error: Dictionary file not found. Download it manually.")

# Ginger API for grammar correction
ginger = GingerIt()

def check_grammar(text):
    return ginger.parse(text)['result']

def check_spelling(text):
    words = text.split()
    corrected_words = []
    
    for word in words:
        suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
        if suggestions:
            corrected_words.append(suggestions[0].term)
        else:
            corrected_words.append(word)
    
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
        corrected_spelling = check_spelling(essay)
        corrected_essay = check_grammar(corrected_spelling)
        readability = textstat.flesch_reading_ease(essay)
        organization_feedback = analyze_organization(essay)

        feedback = f"Word Count: {word_count}<br>"
        feedback += f"Readability Score: {readability:.2f}<br>"
        feedback += "Organization Feedback: " + ', '.join(organization_feedback)

    return render_template('index.html', feedback=feedback, corrected_essay=corrected_essay)

if __name__ == '__main__':
    app.run(debug=True)
