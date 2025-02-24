from flask import Flask, render_template, request
import textstat

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    feedback = ""
    if request.method == "POST":
        essay = request.form.get("essay")
        if essay:
            readability_score = textstat.flesch_reading_ease(essay)
            feedback = f"Readability Score: {readability_score:.2f}"
        else:
            feedback = "Please enter an essay."

    return render_template("index.html", feedback=feedback)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
