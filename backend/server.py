import os
import time
import asyncio
import AVFoundation 
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import google.generativeai as genai
from deepgram import DeepgramClient, SpeakOptions
import websockets
from datetime import datetime
import json
import fitz
import pyaudio
import threading

# Configure Google Gemini model
genai.configure(api_key="key")
model = genai.GenerativeModel("gemini-1.5-flash")

is_asking_questions = False
is_narrating = False

# Initialize Deepgram
DG_API_KEY = "key"
deepgram = DeepgramClient(api_key=DG_API_KEY)

stored_data = []
stored_questions = []
global_transcripts = []
full_global_transcripts  = []

audio_queue = asyncio.Queue()

# PyAudio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024


# Flask app setup
app = Flask(__name__)
CORS(app)


# Example problem database
problems = {
    1: {
        "id": 1,
        "problem": """You are given a list of integers `nums`.
                      Your task is to write a function `solution(nums)` that returns the sum of all even positive numbers in the list.
                      If there are no even positive numbers, return `0`.
                      The integers can be positive, negative, or zero.
                      Only even positive numbers should be included in the sum.""",
        "testCases": [
            {"input": "[1, -2, 3, 4]\n", "output": "4\n"},
            {"input": "[-1, -2, -3]\n", "output": "0\n"},
            {"input": "[10, 20, 30]\n", "output": "60\n"},
            {"input": "[0, -10, 0, 10, -10]\n", "output": "10\n"},
            {"input": "[]\n", "output": "0\n"},
            {"input": "[1000000000, -1000000000, 500000000]\n", "output": "1500000000\n"},
            {"input": "[2, 4, 6]\n", "output": "12\n"},
            {"input": "[1, 3, 5, 7]\n", "output": "0\n"},
        ]
    },
}

filename = "output.mp3"

@app.route('/run-code', methods=['OPTIONS', 'POST'])
def run_code():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    if request.method == 'POST':
        data = request.get_json()
        code = data.get('code')
        problem_id = data.get('problemId')

        problem = problems.get(problem_id)
        if not problem:
            return jsonify({"error": "Problem not found"}), 400

        passed = 0
        total = len(problem['testCases'])
        test_results = []
        failed_cases = []

        for test_case in problem['testCases']:
            input_data = test_case['input']
            expected_output = test_case['output']

            try:
                exec_locals = {}
                exec(code, {}, exec_locals)

                if 'solution' not in exec_locals:
                    return jsonify({"error": "No function 'solution' defined in the code."}), 400

                solution = exec_locals['solution']
                input_values = json.loads(input_data)
                result = solution(input_values)

                if str(result) + '\n' == expected_output:
                    passed += 1
                    test_results.append({
                        "input": input_data,
                        "expected": expected_output,
                        "output": str(result) + '\n',
                        "passed": True,
                        "hint": "Good job! Your solution worked perfectly for this case."
                    })
                else:
                    # Store failed cases for later hint generation
                    failed_cases.append({
                        "code": code,
                        "input_data": input_data,
                        "expected_output": expected_output,
                        "actual_output": str(result) + '\n',
                        "problem_description": problem['problem']
                    })
                    test_results.append({
                        "input": input_data,
                        "expected": expected_output,
                        "output": str(result) + '\n',
                        "passed": False,
                        "hint": "You will get an overall hint at the end."
                    })

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # Generate overall hint if there are failed cases
        overall_hint = ""
        if failed_cases:
            overall_hint = asyncio.run(generate_overall_hint(failed_cases))

        audio_feedback = generate_audio_feedback(passed, total)
        asyncio.run(play_audio_feedback(audio_feedback))

        if failed_cases:
            asyncio.run(play_audio_feedback(overall_hint))

        return jsonify({
            "passed": passed,
            "total": total,
            "results": test_results,
            "overall_hint": overall_hint
        }), 200


async def generate_overall_hint(failed_cases):
    """
    Generates a single overall hint for all failed test cases by aggregating the problem descriptions and errors.
    """
    prompts = []
    for case in failed_cases:
        prompt = (
            f"Their code is:\n\n{case['code']}\n\n" +
            f"The problem description is:\n\n{case['problem_description']}\n\n" +
            f"For the input '{case['input_data']}', the expected output is '{case['expected_output']}', but the actual output was '{case['actual_output']}'."
        )
        prompts.append(prompt)
    
    # Join all cases into one prompt for Gemini
    full_prompt = "You are a coding interviewer. The student is trying to solve multiple test cases. Provide a short overall hint to help the student correct their mistakes and make sure you do not directly give them the answer but guide them right:\n\n" + "\n\n".join(prompts)
    try:
        # Use the Google Gemini model to generate the overall hint
        response = await asyncio.to_thread(model.generate_content, full_prompt)
        return response.text  # Adjust based on response structure
    except Exception as e:
        print(f"Error generating overall hint: {e}")
        return "Unable to generate an overall hint due to an error."




def generate_audio_feedback(passed, total):
    """
    Generates a summary feedback to be converted into speech using Deepgram.
    """
    if passed == total:
        feedback_text = f"Great job! You passed all {total} test cases."
    else:
        feedback_text = f"You passed {passed} out of {total} test cases."

    return feedback_text


async def play_audio_feedback(feedback_text):
    """
    Uses Deepgram to convert text feedback to speech and play it.
    """
    try:
        SPEAK_OPTIONS = {"text": feedback_text}
        options = SpeakOptions(model="aura-asteria-en")

        # Generate and save the audio file
        response = await deepgram.speak.asyncrest.v("1").save(filename, SPEAK_OPTIONS, options)

        # Play the audio file
        play_mp3(filename)

    except Exception as e:
        print(f"Error generating or playing audio: {e}")


def play_mp3(file_path):
    """
    Plays the MP3 file using AVFoundation.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} was not found.")
    
    url = AVFoundation.NSURL.fileURLWithPath_(file_path)
    player, error = AVFoundation.AVAudioPlayer.alloc().initWithContentsOfURL_error_(url, None)
    
    if error:
        raise Exception(f"Error initializing AVAudioPlayer: {error}")
    
    player.play()

    while player.isPlaying():
        time.sleep(0.1)


def _build_cors_preflight_response():
    """
    Build the CORS preflight response (OPTIONS request) with the appropriate headers.
    """
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "Content-Type, Authorization")
    response.headers.add('Access-Control-Allow-Methods', "POST, GET, OPTIONS, PUT, DELETE")
    return response

async def capture_audio(loop):
    """
    Captures audio from the microphone and puts it into the audio_queue asynchronously.
    """
    p = pyaudio.PyAudio()

    stream = p.open(
        format=pyaudio.paInt16,  # Define your format
        channels=1,  # Use mono (1) channel
        rate=16000,  # Sample rate for Deepgram
        input=True,
        frames_per_buffer=1024,  # Buffer size
    )

    print("🎤 Capturing audio...")

    try:
        while stream.is_active():
            mic_data = stream.read(1024)
            await audio_queue.put(mic_data)  # Push audio data into the queue
            await asyncio.sleep(0.01)  # Avoid blocking the event loop
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

# Function to send audio to Deepgram WebSocket
async def sender(ws):
    print("🟢 Streaming mic audio to Deepgram.")
    try:
        while True:
            mic_data = await audio_queue.get()  # Get mic data from the queue
            await ws.send(mic_data)  # Send audio data to Deepgram WebSocket
    except websockets.exceptions.ConnectionClosedOK:
        print("🔴 WebSocket connection closed after sending all data.")

# Function to receive transcription data from Deepgram
async def receiver(ws):
    first_message = True

    try:
        async for message in ws:
            data = json.loads(message)

            if first_message:
                print("🟢 Receiving transcription messages...")
                first_message = False

            if data.get("is_final"):
                transcript = data["channel"]["alternatives"][0]["transcript"]
                global_transcripts.append(transcript)  # Store the transcript globally
                print(f"🟢 Final transcript received: {transcript}")

            # Stop if the user says "done"
            if "done" in transcript.lower():
                print("🟢 User said 'done', closing stream.")
                stream.stop_stream()
                stream.close()
                p.terminate()
                return  # Stop receiving and exit the loop
    except websockets.exceptions.ConnectionClosedOK:
        print("🔴 WebSocket connection closed by the server.")

# Main function to run Deepgram WebSocket connection
async def run(key, **kwargs):
    deepgram_url = f'{kwargs["host"]}/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000'

    async with websockets.connect(
        deepgram_url, extra_headers={"Authorization": f"Token {key}"}
    ) as ws:
        print(f'ℹ️  Request ID: {ws.response_headers.get("dg-request-id")}')

        # Start capturing audio in the main event loop
        capture_task = asyncio.create_task(capture_audio(asyncio.get_running_loop()))

        # Concurrently send audio to Deepgram and receive transcriptions
        await asyncio.gather(
            sender(ws),  # Send mic audio to Deepgram
            receiver(ws),  # Receive transcription from Deepgram
            capture_task  # Capture audio
        )

        # Optionally save the transcripts to a file
        with open("transcriptions.txt", "w") as f:
            f.write(' '.join(global_transcripts))  # Save all transcriptions to a file

        return ' '.join(global_transcripts)  # Return the final transcript as a single string




@app.route('/listen', methods=['OPTIONS', 'POST'])
def listen():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    if request.method == 'POST':
        global audio_queue
        global global_transcripts
        global_transcripts = [] 
        audio_queue = asyncio.Queue()  # Initialize the queue here to avoid cross-event-loop issues

        try:
            # Use asyncio.run to call the async function and manage the WebSocket connection
            transcript = asyncio.run(run(DG_API_KEY, host="wss://api.deepgram.com"))
            print("yeet", transcript)

            # Return the captured transcript after WebSocket finishes
            if transcript:
                print(transcript)
                return jsonify({"success": True, "transcript": transcript}), 200
            else:
                return jsonify({"success": False, "message": "No transcript available"}), 400

        except Exception as e:
            return jsonify({"error": str(e)}), 500
        

@app.route('/evaluate', methods=['OPTIONS','POST'])
def evaluate_code():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    if request.method == 'POST':
        data = request.get_json()
        code = data.get('code')


        # Example: process the request using Gemini or any other service
        try:
            # Use Gemini to evaluate and get scores
            response =  asyncio.run(generate_gemini_feedback(
                f"This code is the {code} and , these are the questions that were asked: {stored_questions} and their response lists repectively {full_global_transcripts}. Please provide ratings for communication and technical questions. and output a pure list of numbers for the following paramtetrs: "
                "'codeCorrectness', 'communication', 'resumeQuestions', 'technicalQuestions in a x, x, x, x format. "
                f"For codeCorrectness, if the code passes the {problems} then give it a 5, otherwise give it based on the test cases passed between 1 and 4. "
                f"For communication, if the candidate was able to communicate effectivel with long proper answers in this {full_global_transcripts} which has a 3 lists which have all the responses, and fairly rate between 1 and 5 being slightly nice"
                f"For resumeQuestions, if the candidate was able to answer the {stored_questions} effectively,{full_global_transcripts},  and fairly rate between 1 and 5"
                "DONT OUTPUT ANY TEXT or explanations JUST NUMBERS between 0, 1, 2, 3, 4, 5, NA is 0" 
            ))
            
            scores = response.split(',')  
            score_fields = ['codeCorrectness', 'communication', 'resumeQuestions', 'technicalQuestions']
            score_dict = dict(zip(score_fields, scores))
            print(score_dict)

            # Parse the response and return the scores
            return jsonify({
        'success': True,
        'scores': score_dict
    })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
async def generate_gemini_feedback(prompt):
    # Asynchronously call the Gemini model to get feedback
    response = await asyncio.to_thread(model.generate_content, prompt)
    return response.text  # Adjust this based on Gemini's response format


@app.route('/process-voice', methods=['POST'])
def process_voice():
    data = request.get_json()
    code = data.get('code', '')
    listen()
    print(global_transcripts)
    question = ''.join(global_transcripts)
    if not question:
        return jsonify({'error': 'No question provided'}), 400

    try:
        # Use Google Gemini to generate an answer based on the question
        response = asyncio.run(generate_gemini_response(question + "this is my code:" + code))
        print(response)
        asyncio.run(play_audio_feedback(response))
        return jsonify({'success': True, 'answer': response}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

async def generate_gemini_response(question):
    # Use Gemini to generate a response to the voice input (question)
    prompt = f"Answer the following question in a helpful and concise manner as you are an interviewer, with only 2-3 sentences max and try not not give solution: {question}"
    response = await asyncio.to_thread(model.generate_content, prompt)
    return response.text

@app.route('/upload-resume', methods=['OPTIONS', 'POST'])
def upload_resume():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    if request.method == 'POST':
        file = request.files.get('resume')
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No resume uploaded'}), 400

        # Extract text from the resume PDF
        resume_text = extract_resume_text(file)

        # Generate questions based on the resume
        questions = asyncio.run(generate_resume_questions(resume_text))
        
        global stored_questions
        stored_questions = questions.split('\n')  # Store questions globally as a list
        return jsonify({'success': True, 'questions': questions}), 200


def extract_resume_text(file):
    """
    Extract text from the uploaded resume PDF using PyMuPDF (fitz).
    :param file: The uploaded file object (from Flask's request.files).
    :return: Extracted text from the PDF.
    """
    # Open the PDF from the uploaded file
    resume_text = ""
    
    # PyMuPDF needs a file-like object, so we'll use file.read() with open_memory method
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
    
    # Iterate over each page of the PDF
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        resume_text += page.get_text("text")  # Extract text from the page
    
    # Close the PDF document
    pdf_document.close()
    
    return resume_text

async def generate_resume_questions(resume_text):
    prompt = (
        f"The candidate's resume contains the following information:\n\n{resume_text}\n\n"
        "Generate only 1 interview question setbased on this resume in this format: 1. question1 2. question2 3. question3. do not attach any additional information or response"
    )
    try:
        response = await asyncio.to_thread(model.generate_content, prompt) 
        return response.text  # Return first 3 questions (adjust based on response format)
    except Exception as e:
        print(f"Error generating questions: {e}")
        return ["Error generating questions"]

# Use Deepgram to ask the current question
@app.route('/ask-question', methods=['OPTIONS','POST'])
def ask_questions():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    if request.method == 'POST':
        global is_asking_questions;
        if is_asking_questions:
            print(full_global_transcripts)
            return jsonify({"error": "Questions are already being asked."}), 400
        
        is_asking_questions = True;
        global stored_questions
        if not stored_questions:
            return jsonify({"error": "No questions found. Please upload a resume first."}), 400
        
            # Iterate over all questions
        for question in stored_questions[:3]:
            print(question)
            # Ask the question
            asyncio.run(play_audio_feedback(question))
            # Listen for the answer after each question
            transcript = asyncio.run(listen_for_answer())

            if transcript:
                 print(f"Received answer: {transcript}")
            else:
                    print("No answer received.")
        
        return jsonify({"success": True, "message": "Questions asked and answers received."})
    
    
async def listen_for_answer():
    global audio_queue
    global global_transcripts
    global full_global_transcripts
    full_global_transcripts.append(global_transcripts)
    global_transcripts = []  # Reset transcripts before listening
    audio_queue = asyncio.Queue()  # Initialize a new audio queue for each session

    try:
        # Call the WebSocket connection to Deepgram and get the transcript
        transcript = await run(DG_API_KEY, host="wss://api.deepgram.com")
        return transcript  # Return the captured transcript after listening

    except Exception as e:
        print(f"Error during listening: {e}")
        return None

@app.route('/narrate-problem', methods=['POST'])
def narrate_problem():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    if request.method == 'POST':
        if is_narrating:
            return jsonify({"error": "Narration is already in progress."}), 400
            
        is_narrating = True
        data = request.get_json()
        problem_description = data.get('problemDescription')

        # Use Deepgram or a TTS library to con
        # vert problem description to audio
        try:
            asyncio.run(play_audio_feedback(problem_description))
            return jsonify({"success": True}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run( use_reloader=False, threaded=False)

