
import speech_recognition as sr
import os
import pandas as pd
import numpy as np
import re
# import Levenshtein
# import spacy
from deeppavlov import build_model, configs
import requests
import json
# import pyttsx3
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from gtts import gTTS 
import os 


import warnings
warnings.filterwarnings("ignore")

import random

import argparse
parser = argparse.ArgumentParser()
# parser.add_argument("--rider_name", help="Add Rider Name")
args = parser.parse_args()

#Squad
model = build_model(configs.squad.squad, download=True) #Run download=True for the first time.

class Voice():


    def listen(self):

        r = sr.Recognizer()
        with sr.Microphone() as source:
            text = ''

            while (text == ''):

                audio = r.listen(source)

                try:
                    print(1)
                    text = r.recognize_google(audio)
                    print(2)
                    print("Recognized audio:", text)
                except sr.UnknownValueError:
                    self.speak("Sorry, didn't get you, can you please repeat?")
                except sr.RequestError as e:
                    self.speak("Something went wrong, please try again.")


        return str(text)


    def speak(self, text):

        language = 'en-us'

        myobj = gTTS(text=text, lang=language, slow=False) 
        myobj.save("voice_note.mp3") 
        os.system("mpg321 voice_note.mp3") 

    def find_disease(self, df, symtoms):
        df["match"] = 0
        top_matched_disease = ''
        should_book_appointment = 0
        
        stopwords = {'and','also','who','is','a','at','is','he'}

        result_symtoms  = [word for word in re.split("\W+",symtoms) if word.lower() not in stopwords]

        
        for i in result_symtoms:
            print('i:', i)
            df["match"] += df["Symptom"].apply(lambda x: (re.match(str(x), str(i)) != None)*1)

        top_matched_disease = df.groupby("Disease")[["match", "Count of Disease Occurrence"]].agg({'match': sum, 'Count of Disease Occurrence': 'mean'}).sort_values(["match", "Count of Disease Occurrence"], ascending = False).reset_index().loc[0, 'Disease'].upper()

        if(df.groupby("Disease")[["match", "Count of Disease Occurrence"]].agg({'match': sum, 'Count of Disease Occurrence': 'mean'}).sort_values(["match", "Count of Disease Occurrence"], ascending = False).reset_index().loc[0, 'Count of Disease Occurrence'] < 268):
            should_book_appointment = 1
            
        return top_matched_disease, should_book_appointment
    #     return df.groupby("Disease")[["match", "Count of Disease Occurrence"]].agg({'match': sum, 'Count of Disease Occurrence': 'mean'}).sort_values(["match", "Count of Disease Occurrence"], ascending = False).reset_index().head()



if __name__ == "__main__":


    df = pd.read_excel('raw_data.xlsx')

    df = df.fillna(method='ffill')
    df['Symptom'] = df.Symptom.apply(lambda x: str(x).split('_')[1])
    df['Disease'] = df.Disease.apply(lambda x: str(x).split('_')[1])
    df['Disease'] = df.Disease.apply(lambda x: str(x).split('^')[0])


    welcome_msg = "Hey Saurav, Welcome to Pulse! What are some of the symptoms you are feeling?"

    voice = Voice()

    voice.speak(welcome_msg)

    ans = voice.listen()

    symptom = model([ans], ['What?'])[0][0]

    print("Recognized audio: ", symptom)

    top_matched_disease, should_book_appointment = voice.find_disease(df, symptom)

    voice.speak("Based on your symptoms my search suggests that you might have " + str(top_matched_disease) + ".")
    voice.speak("I've already emailed you a link to book an apointment at the nearest doctor for further consultation and some tips to help you get releif from the symptoms.")
    voice.speak("Thanks for using Pulse. Wish you a quick recovery!")
