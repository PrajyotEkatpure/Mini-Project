import csv
import json
import os
import threading
import time
from multiprocessing import Process

import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from gemini import GiveGeminiOutput, MODEL_NAME

# Heavy / optional dependencies (OpenCV, MediaPipe, pygame, Firebase) are imported only where the
# games need them, so the chatbot, scenario and story features still start without them.

app = Flask(__name__)
CORS(app)

from story.routes import create_blueprint as create_story_blueprint
app.register_blueprint(create_story_blueprint())

# Load environment variables
load_dotenv()

# File to store chat history
history_file = "chat_history.json"

if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        chat_history = json.load(f)
else:
    chat_history = []

@app.route('/')
def hello_world():
    return 'Server is running!'

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

SUPPORTED_LANGUAGES = {
    "English", "Hindi", "Marathi", "Tamil", "Telugu", "Kannada", "Malayalam",
    "Bengali", "Gujarati", "Punjabi", "Odia", "Urdu", "Assamese",
}


def get_model():
    genai.configure(api_key=os.getenv("GENAI_API_KEY"))
    return genai.GenerativeModel(model_name=MODEL_NAME, safety_settings=SAFETY_SETTINGS)


def save_history():
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, indent=4, ensure_ascii=False)


@app.route("/get_scenario", methods=["POST"])
def get_scenario():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Please describe a scenario."}), 400
    if len(message) > 1500:
        return jsonify({"error": "Please keep the scenario under 1500 characters."}), 400
    try:
        from grounded import get_service
        return jsonify({"response": get_service().scenario(message)})
    except Exception as e:
        print(f"/get_scenario failed: {e}")
        return jsonify({"error": "The scenario service could not produce an answer. Please try again."}), 502


@app.route("/get_response", methods=["POST"])
def get_response():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    user_feedback = data.get("feedback", "")
    language = data.get("language") or "English"
    if language not in SUPPORTED_LANGUAGES:
        language = "English"
    image = data.get("image")  # optional {"mime": "image/png", "data": "<base64>"}
    if not message and not image:
        return jsonify({"error": "Message is required."}), 400
    image_part = None
    if image:
        import base64
        mime = str(image.get("mime", ""))
        if mime not in ("image/png", "image/jpeg", "image/webp"):
            return jsonify({"error": "Please upload a PNG, JPG or WebP image."}), 400
        try:
            raw = base64.b64decode(image.get("data", ""), validate=True)
        except Exception:
            return jsonify({"error": "The image could not be read."}), 400
        if not raw or len(raw) > 6 * 1024 * 1024:
            return jsonify({"error": "The image is empty or larger than 6 MB."}), 400
        image_part = {"mime_type": mime, "data": raw}
        message = message or "Explain what this image shows in relation to the Indian Constitution."

    plain_history = [{"role": "user" if t.get("role") == "user" else "bot", "content": str(t.get("content", ""))} for t in data.get("history", [])[-10:]]
    try:
        from grounded import get_service
        out = get_service().chat(message if not image else (data.get("message") or "").strip(), plain_history, language, image_part)
        result = out["response"]
    except Exception as e:
        print(f"/get_response failed: {e}")
        return jsonify({"error": "The chatbot could not answer right now. Please try again."}), 502

    chat_history.append({"user_message": message, "response": result, "language": language, "feedback": user_feedback})
    save_history()
    return jsonify({"response": result, "sources": out.get("sources", []), "mode": out.get("mode"), "verified": out.get("verified", False)})


# main driver function
@app.route('/generate-story', methods=['POST'])
def generate_story():
    text = (request.get_json(silent=True) or {}).get('text', '')
    try:
        convo = get_model().start_chat(history=[])
        convo.send_message(f"Give me a very short and simple story to understand this article. Use indian context and indian names: {text}")
        return jsonify({"story": convo.last.text})
    except Exception as e:
        print(f"/generate-story failed: {e}")
        return jsonify({"error": "Could not generate a story right now."}), 502


def run_game_1():
    from mario.main import Core
    oCore = Core()
    oCore.main_loop()
    return "Game 1 finished"




_db = None


def get_db():
    """Firestore client, created on first use so the rest of the server does not need Firebase credentials."""
    global _db
    if _db is None:
        from firebase_admin import credentials, firestore, initialize_app
        initialize_app(credentials.Certificate("./credentials.json"))
        _db = firestore.client()
    return _db


def get_username():
    try:
        with open("username.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print("username.txt not found")
        return None

def run_game_2():
    import cv2
    import cvzone
    from cvzone.HandTrackingModule import HandDetector
    from firebase_admin import firestore
    db = get_db()
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    detector = HandDetector(detectionCon=0.8)

    class MCQ():
        def __init__(self, data):
            self.question = data[0]
            self.choice1 = data[1]
            self.choice2 = data[2]
            self.choice3 = data[3]
            self.choice4 = data[4]
            self.answer = int(data[5])
            self.userAns = None

        def update(self, cursor, bboxs):
            for x, bbox in enumerate(bboxs):
                x1, y1, x2, y2 = bbox
                if x1 < cursor[0] < x2 and y1 < cursor[1] < y2:
                    self.userAns = x + 1
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), cv2.FILLED)

    pathCSV = "Mcqs.csv"
    with open(pathCSV, newline='\n') as f:
        reader = csv.reader(f)
        dataAll = list(reader)[1:]

    mcqList = [MCQ(q) for q in dataAll]

    qNo = 0
    qTotal = len(dataAll)

    while True:
        success, img = cap.read()
        if not success or img is None:
            print("Error: Failed to capture image. Skipping frame...")
            continue  # Skip this iteration if no valid image is captured

        img = cv2.flip(img, 1)
        hands, img = detector.findHands(img, flipType=False)

        if qNo < qTotal:
            mcq = mcqList[qNo]
            img, bbox = cvzone.putTextRect(img, mcq.question, [100, 100], 2, 2, offset=50, border=5)
            img, bbox1 = cvzone.putTextRect(img, mcq.choice1, [100, 250], 2, 2, offset=50, border=5)
            img, bbox2 = cvzone.putTextRect(img, mcq.choice2, [400, 250], 2, 2, offset=50, border=5)
            img, bbox3 = cvzone.putTextRect(img, mcq.choice3, [100, 400], 2, 2, offset=50, border=5)
            img, bbox4 = cvzone.putTextRect(img, mcq.choice4, [400, 400], 2, 2, offset=50, border=5)

            if hands:
                lmList = hands[0]['lmList']
                if len(lmList) >= 13:
                    cursor = lmList[8]
                    length, info, img = detector.findDistance(lmList[8][:2], lmList[12][:2], img)
                else:
                    cursor = None
                    length, info = 0, ""
                if length < 60:
                    mcq.update(cursor, [bbox1, bbox2, bbox3, bbox4])
                    if mcq.userAns is not None:
                        time.sleep(0.3)
                        qNo += 1
        else:
            correct_answers = sum(mcq.answer == mcq.userAns for mcq in mcqList)
            score_in_marks = correct_answers * 10  # 10 marks per correct answer

            img, _ = cvzone.putTextRect(img, "Quiz is completed", [250, 300], 2, 2, offset=50, border=5)
            img, _ = cvzone.putTextRect(img, f'Your Marks: {score_in_marks}', [700, 300], 2, 2, offset=16, border=5)

            # Update Firestore with the score
            username = get_username()
            if username:
                user_docs = db.collection("users").where("username", "==", username).stream()

                doc_found = False
                for doc in user_docs:
                    doc_id = doc.id
                    doc_data = doc.to_dict()
                    previous_score = doc_data.get("score", 0)
                    updated_score = previous_score + score_in_marks

                    db.collection("users").document(doc_id).update({
                        "score": updated_score,
                        "timestamp": firestore.SERVER_TIMESTAMP,
                    })
                    print(f"Updated Firestore: Username={username}, Previous Score={previous_score}, Added Score={score_in_marks}, New Score={updated_score}")
                    doc_found = True
                    break

                if not doc_found:
                    print(f"No existing document found for username: {username}")
            else:
                print("Failed to update Firestore: Username not found")

            cv2.imshow("Img", img)
            cv2.waitKey(1)  # Ensure the window updates before closing

            time.sleep(5)  # Wait 5 seconds before closing everything
            cap.release()
            cv2.destroyAllWindows()
            os._exit(0)  # Terminate the process

        barValue = 150 + (950 // qTotal) * qNo
        cv2.rectangle(img, (150, 600), (barValue, 650), (0, 255, 0), cv2.FILLED)
        cv2.rectangle(img, (150, 600), (1100, 650), (255, 0, 255), 5)
        img, _ = cvzone.putTextRect(img, f'{round((qNo / qTotal) * 100)}%', [1130, 635], 2, 2, offset=16, border=5)

        cv2.imshow("Img", img)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    os._exit(0)  # Ensure process termination



@app.route('/start-game-1', methods=['POST'])
def start_game_1():
    data = request.get_json()
    username = data.get('username')  # Retrieve the username from the request body

    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    # store the username in the file
    with open("username.txt", "w") as f:
        f.write(username)

    print(f"Starting Game 1 for user: {username}")
    game_thread = threading.Thread(target=run_game_1)
    game_thread.start()
    return jsonify({"message": "Game 1 started!", "username": username})

@app.route('/start-game-2', methods=['POST'])
def start_game_2():
    data = request.get_json()
    username = data.get('username')  # Retrieve the username from the request body

    if not username:
        return jsonify({"error": "Username is required"}), 400

    with open("username.txt", "w") as f:
        f.write(username)

    print(f"Starting Quiz Game for user: {username}")
    
    # Run game in a separate process (not a thread)
    quiz_process = Process(target=run_game_2)
    quiz_process.start()

    return jsonify({"message": "Quiz game started!", "username": username})
@app.route('/game-status', methods=['GET'])
def game_status():
    status = request.args.get('status', 'unknown')
    return jsonify({"status": status})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
