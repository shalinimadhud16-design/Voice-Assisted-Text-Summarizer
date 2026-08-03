

!pip install nltk spacy transformers pydub flask-ngrok requests pyngrok gensim
!python -m nltk.downloader all
!python -m spacy download en_core_web_sm
import gensim
print(gensim._version_)
!pkill ngrok
from pyngrok import ngrok
ngrok.set_auth_token("2nbg79YLy8mzS5qQgch1QM1HpWj_2HyEZTUtZeHdy12B9iAcf")
public_url = ngrok.connect(5000)
print(public_url)
import os
import requests
from flask import Flask, request, jsonify, render_template
from pydub import AudioSegment
from transformers import pipeline
import io

# Initializing Flask app
app = Flask(_name_)

# AssemblyAI API key
ASSEMBLYAI_API_KEY = '0827ab0a7e454344b8202e691104aaf9'

# Hugging Face sentiment analysis pipeline
# sentiment_classifier = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
sentiment_classifier = pipeline('text-classification', model='bhadresh-savani/distilbert-base-uncased-emotion', return_all_scores=True)

summarization_pipeline = pipeline("summarization")

#converting audio to FLAC
def convert_to_flac(audio_file_path):
    audio = AudioSegment.from_file(audio_file_path)
    flac_io = io.BytesIO()
    audio.export(flac_io, format='flac')
    flac_io.seek(0)
    return flac_io

# AssemblyAI transcription
def transcribe_audio(audio_file_path):
    # Convert the audio file to FLAC
    flac_audio = convert_to_flac(audio_file_path)

    # Uploading audio file to AssemblyAI
    headers = {
        'authorization': ASSEMBLYAI_API_KEY,
        'content-type': 'application/json',
    }
    upload_response = requests.post(
        'https://api.assemblyai.com/v2/upload',
        headers=headers,
        data=flac_audio.read()
    )

    audio_url = upload_response.json()['upload_url']

    # Requesting transcription
    transcript_request = requests.post(
        'https://api.assemblyai.com/v2/transcript',
        json={'audio_url': audio_url},
        headers=headers
    )

    transcript_id = transcript_request.json()['id']

    #  transcription completion
    while True:
        transcript_response = requests.get(
            f'https://api.assemblyai.com/v2/transcript/{transcript_id}',
            headers=headers
        )
        if transcript_response.json()['status'] == 'completed':
            return transcript_response.json()['text']
        elif transcript_response.json()['status'] == 'failed':
            raise Exception("Transcription failed.")

# Sentiment analysis  using Hugging Face's BERT model
def analyze_sentiment(text):
    result = sentiment_classifier(text)
    print(result)
    sentiments = {
        "joy": 0,
        "anger": 0,
        "sadness": 0,
        "fear": 0,
        "neutral": 0,
        "surprise": 0,
        "disgust": 0,
        "love":0,
    }
    for r in result[0]:  # Assuming 'result' is a list containing a single dictionary of scores
        label = r['label']
        score = r['score']
        if label in sentiments:
            sentiments[label] = score
    # for r in result:
    #     label = r['label']
    #     score = r['score']
    #     if label == "NEGATIVE":
    #        sentiments["sadness"] = score  # Assign full score to negative
    #     elif label == "POSITIVE":
    #         sentiments["joy"] = score  # Assign full score to positive
    #     elif label == "sadness":
    #         sentiments["sadness"] = score
    #     else:
    #         sentiments["neutral"] = score

          #sentiments["sadness"] = score * 0.5
          #sentiments["anger"] = score * 0.3
          #sentiments["fear"] = score * 0.2
    #else:
        #sentiments[label] = score
        #sentiments[label] = score

    # Calculating overall sentiment as positive, negative, or neutral
    positive_score = sentiments.get("joy", 0)
    # negative_score = sentiments.get("sadness", 0)
    negative_score = sentiments.get("sadness", 0) + sentiments.get("anger", 0) + sentiments.get("fear",    0) + sentiments.get("disgust", 0)
    #positive_score = sentiments.get("joy", 0) + sentiments.get("surprise", 0)
    #negative_score = sentiments.get("anger", 0) + sentiments.get("sadness", 0) + sentiments.get("fear", 0) + sentiments.get("disgust", 0)

    if positive_score>=0.495 or positive_score<=0.509:
        overall_sentiment="neutral"
    if positive_score > negative_score:
        overall_sentiment = "positive"
    elif negative_score > positive_score:
        overall_sentiment = "negative"
    else:
        overall_sentiment = "neutral"

    return sentiments, overall_sentiment


def summarize_text(text):
    try:
        summary = summarization_pipeline(text,max_length=100, min_length=30, do_sample=False)
        return summary[0] ['summary_text']
    except ValueError as e:
        return str(e)
# Route for frontend form
@app.route('/')
def index():
    return render_template('index.html')

#  to handle audio file upload and processing
@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Saving uploaded file
    file_path = os.path.join('uploads', file.filename)
    file.save(file_path)

    try:
        # Step 1: Transcribe  audio
        transcript = transcribe_audio(file_path)

        # Step 2: Performing sentiment analysis on the transcribed text
        sentiments, overall_sentiment = analyze_sentiment(transcript)
        sentiments = f"{sentiments}"
        print( sentiments, overall_sentiment)
        # Step 3: Performing summarization
        summary = summarize_text(transcript)
        # Step 4:Return the result as JSON
        return jsonify({
            "transcript": transcript,
            "sentiments": sentiments,
            "overall_sentiment": overall_sentiment,
            "summary": summary
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the Flask app
if _name_ == "_main_":
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run()
