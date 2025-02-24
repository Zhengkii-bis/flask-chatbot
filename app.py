from flask import Flask, request, render_template, jsonify
import language_tool_python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import textstat

app = Flask(__name__)

# Initialize tools
tool = language_tool_python.LanguageTool('en-US')
analyzer = SentimentIntensityAnalyzer()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    try:
        data = request.json
        essay = data.get('essay', '')

        if not essay.strip():
            return jsonify({"error": "No text provided"}), 400

        # Word Count
        word_count = len(essay.split())

        # Grammar & Spelling Suggestions
        matches = tool.check(essay)
        grammar_feedback = [
            {"ruleId": match.ruleId, "message": match.message, "suggestions": match.replacements}
            for match in matches[:5]  # Limit to 5 suggestions
        ]
        corrected_essay = tool.correct(essay)

        # Readability Analysis
        flesch_score = textstat.flesch_reading_ease(essay)
        grade_level = textstat.flesch_kincaid_grade(essay)

        # Sentiment Analysis
        sentiment_score = analyzer.polarity_scores(essay)
        positive = sentiment_score['pos']
        neutral = sentiment_score['neu']
        negative = sentiment_score['neg']

        # Argument Feedback
        if positive > negative:
            argument_feedback = "Your essay has a clear and positive tone."
        elif neutral > 0.6:
            argument_feedback = "Your essay may need stronger arguments."
        else:
            argument_feedback = "Your essay seems unclear. Try refining your arguments."

        # Final Feedback
        feedback = []
        if matches:
            feedback.append("Consider improving grammar using the suggested corrections.")
        else:
            feedback.append("Great job! No grammar mistakes found.")

        if flesch_score < 50:
            feedback.append("Try simplifying your sentences to improve readability.")
        else:
            feedback.append("Your readability is good.")

        feedback.append(argument_feedback)

        return jsonify({
            "word_count": word_count,
            "grammar_feedback": grammar_feedback,
            "readability_score": flesch_score,
            "grade_level": grade_level,
            "sentiment_analysis": {
                "positive": f"{positive*100:.2f}%",
                "neutral": f"{neutral*100:.2f}%",
                "negative": f"{negative*100:.2f}%"
            },
            "final_feedback": feedback,
            "corrected_essay": corrected_essay
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
