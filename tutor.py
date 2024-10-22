import google.generativeai as genai
import os
import time
import re
import asyncio
from deepgram import DeepgramClient, SpeakOptions
import requests
from playsound import playsound
import AVFoundation
import PyPDF2

genai.configure(api_key=os.environ["API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash")

filename = "output.mp3"

def pdf_to_txt(pdf_file_path, txt_file_path):
    with open(pdf_file_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()

    with open(txt_file_path, 'w') as txt_file:
        txt_file.write(text)

def play_mp3(file_path):
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} was not found.")
    
    # Create an AVAudioPlayer instance
    url = AVFoundation.NSURL.fileURLWithPath_(file_path)
    # AVAudioPlayer returns a tuple (audioPlayer, error)
    player, error = AVFoundation.AVAudioPlayer.alloc().initWithContentsOfURL_error_(url, None)
    
    # Check if there was an error during initialization
    if error:
        raise Exception(f"Error initializing AVAudioPlayer: {error}")
    
    # Play the audio file
    player.play()

    # Keep the program running while the audio is playing
    while player.isPlaying():
        time.sleep(0.1)

async def main():
    try:
        # STEP 1: Create a Deepgram client.
        # By default, the DEEPGRAM_API_KEY environment variable will be used for the API Key
        deepgram = DeepgramClient()

        # pdf_path = 'PDF_PATH'

        # output_txt = 'TXT_PATH'

        # pdf_to_txt(pdf_path, output_txt)

        f = open("LEETCODE_CODE_FILE_PATH", "r")
        data = f.read()
        response = model.generate_content("You are a leetcode tutor giving feedback/recommendation of my code. Give me concise feedback and assist on the progress of my code so far. Make your response conversational and encouraging. We are trying to solve the problem of reversing a linked list: " + data)

        # f = open("Resume.txt", "r")
        # data = f.read()
        # print(data)
        # response = model.generate_content("You are a software engineer role interviewer. Read the resume and ask questions on it to test the interviewer's proficiency in the technologies that they list and their fit as a software engineer. Your response should be less than 1500 characters. Resume: " + data)
        SPEAK_OPTIONS = {"text": response.text}

        # STEP 2: Configure the options (such as model choice, audio configuration, etc.)
        options = SpeakOptions(
            model="aura-asteria-en",
        )

        # STEP 3: Call the save method on the speak property
        response = await deepgram.speak.asyncrest.v("1").save(filename, SPEAK_OPTIONS, options)
        print(response.to_json(indent=4))
        play_mp3(filename)

    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    asyncio.run(main())