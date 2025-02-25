from flask import Flask, render_template, request
import textstat
import re
from gingerit.gingerit import GingerIt
from symspellpy import SymSpell, Verbosity
import pkg_resources

app = Flask(__name__)

# Initialize GingerIt for grammar checking
ginger = GingerIt()

# Initialize SymSpell for spelling correction
sym_spell = SymSpell()
dictionary_path = pkg_resources.resource_filename("symspellpy", "frequency_dictionary_en_82_765.txt")
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

def check_grammar(text):
    """Uses GingerIt to correct grammar and return the corrected text."""
    corrected_text = ginger.parse(text)['result']
    return corrected_text

def check_spelling(text):
    """Uses SymSpell to correct spelling mistakes in a given text."""
    words = text.split()
    corrected_words = []
    
    for word in words:
        suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
        corrected_word = suggestions[0].term if suggestions else word
        corrected_words.append(corrected_word)
    
    return ' '.join(corrected_words)

def analyze_organization(text):
    """Analyzes the organization of an essay based on sentence and paragraph structure."""
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
        
        # Apply spelling correction first
        corrected_spelling = check_spelling(essay)
        
        # Apply grammar correction after spelling correction
        corrected_essay = check_grammar(corrected_spelling)
        
        readability = textstat.flesch_reading_ease(essay)
        organization_feedback = analyze_organization(essay)

        feedback = f"Word Count: {word_count}<br>"
        feedback += f"Readability Score: {readability:.2f}<br>"
        feedback += "Organization Feedback: " + ', '.join(organization_feedback)
    
    return render_template('index.html', feedback=feedback, corrected_essay=corrected_essay)

if __name__ == '__main__':
    app.run(debug=True)
