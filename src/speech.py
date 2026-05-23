import speech_recognition
import pyttsx3
import pygame
from gtts import gTTS
import os

recognizer = speech_recognition.Recognizer()
engine = pyttsx3.init()

def speak_old(text):
    engine.say(text)
    engine.runAndWait()

def speak(text):
    tts = gTTS(text)
    tts.save('temp.mp3')
    pygame.mixer.init()

    pygame.mixer.music.load('temp.mp3')
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.music.unload()
    os.remove("temp.mp3")

def listen():
    with speech_recognition.Microphone() as source:
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except speech_recognition.UnknownValueError:
            return "Sorry, I didn't catch that."
        except speech_recognition.RequestError:
            return "Sorry, speech recognition service is unavailable."
