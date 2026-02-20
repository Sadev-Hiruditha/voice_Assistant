import pyttsx3
import speech_recognition as sr
import datetime
import wikipedia
import webbrowser
import os
import pywhatkit
import spacy
from tkinter import Tk, Label, Button, Text, Scrollbar, END, Frame
from threading import Thread
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VoiceAssistant:
    def __init__(self):
        """Initialize the voice assistant with text-to-speech and NLP."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)
            self.nlp = spacy.load("en_core_web_sm")
            self.recognizer = sr.Recognizer()
            self.setup_recognizer()
            logging.info("Voice assistant initialized successfully")
        except Exception as e:
            logging.error(f"Initialization error: {e}")
            raise

    def setup_recognizer(self):
        """Configure speech recognizer with optimal settings."""
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 4000
        self.recognizer.pause_threshold = 0.8

    def speak(self, text):
        """Convert text to speech with error handling."""
        try:
            logging.info(f"Speaking: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logging.error(f"Speech error: {e}")

    def listen(self):
        """Listen to user commands with improved error handling."""
        try:
            with sr.Microphone() as source:
                logging.info("Listening for command...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                command = self.recognizer.recognize_google(audio).lower()
                logging.info(f"Command received: {command}")
                return command
        except sr.WaitTimeoutError:
            logging.warning("Listening timeout")
            return ""
        except sr.UnknownValueError:
            logging.warning("Could not understand audio")
            self.speak("Sorry, I didn't catch that. Could you repeat?")
            return ""
        except sr.RequestError as e:
            logging.error(f"API error: {e}")
            self.speak("I'm having trouble connecting to the speech service.")
            return ""
        except Exception as e:
            logging.error(f"Unexpected error in listen: {e}")
            return ""

    def process_command(self, command):
        """Process and respond to voice commands with improved intent detection."""
        if not command:
            return "No command received."

        doc = self.nlp(command)
        intent = self.detect_intent(doc)
        
        handlers = {
            "wikipedia": self.handle_wikipedia,
            "play_music": self.handle_play_music,
            "open_notepad": self.handle_open_notepad,
            "open_word": self.handle_open_word,
            "time": self.handle_time,
            "date": self.handle_date,
            "open_browser": self.handle_open_browser,
            "search": self.handle_search,
            "exit": self.handle_exit
        }
        
        handler = handlers.get(intent, self.handle_unknown)
        return handler(command)

    def detect_intent(self, doc):
        """Enhanced intent detection with better keyword matching."""
        text = doc.text.lower()
        
        intent_keywords = {
            "wikipedia": ["wikipedia", "wiki"],
            "play_music": ["play", "music", "song", "youtube"],
            "open_notepad": ["notepad", "note pad"],
            "open_word": ["word", "microsoft word"],
            "time": ["time", "what time"],
            "date": ["date", "what date", "today's date"],
            "open_browser": ["browser", "chrome", "firefox"],
            "search": ["search", "google", "look up"],
            "exit": ["exit", "quit", "shutdown", "goodbye", "bye"]
        }
        
        for intent, keywords in intent_keywords.items():
            if any(keyword in text for keyword in keywords):
                return intent
        
        return "unknown"

    def handle_wikipedia(self, command):
        """Search Wikipedia and return results."""
        query = command.replace("wikipedia", "").replace("wiki", "").strip()
        if not query:
            response = "What would you like me to search on Wikipedia?"
        else:
            try:
                results = wikipedia.summary(query, sentences=2)
                response = f"According to Wikipedia: {results}"
            except wikipedia.DisambiguationError as e:
                response = f"That term is ambiguous. Did you mean: {', '.join(e.options[:3])}?"
            except wikipedia.PageError:
                response = f"Sorry, I couldn't find any information about {query} on Wikipedia."
            except Exception as e:
                logging.error(f"Wikipedia error: {e}")
                response = "Sorry, I encountered an error searching Wikipedia."
        
        self.speak(response)
        return response

    def handle_play_music(self, command):
        """Play music on YouTube."""
        song = command.replace("play", "").replace("music", "").replace("song", "").strip()
        if not song:
            response = "What would you like me to play?"
        else:
            response = f"Playing {song} on YouTube."
            try:
                pywhatkit.playonyt(song)
            except Exception as e:
                logging.error(f"YouTube error: {e}")
                response = "Sorry, I couldn't open YouTube."
        
        self.speak(response)
        return response

    def handle_open_notepad(self, command):
        """Open Notepad application."""
        response = "Opening Notepad."
        try:
            if os.name == 'nt':  # Windows
                os.system("notepad")
            elif os.name == 'posix':  # macOS/Linux
                os.system("open -a TextEdit" if os.uname().sysname == "Darwin" else "gedit &")
        except Exception as e:
            logging.error(f"Notepad error: {e}")
            response = "Sorry, I couldn't open the text editor."
        
        self.speak(response)
        return response

    def handle_open_word(self, command):
        """Open Microsoft Word application."""
        response = "Opening Microsoft Word."
        word_paths = [
            "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
            "C:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
            "/Applications/Microsoft Word.app"
        ]
        
        opened = False
        for path in word_paths:
            if os.path.exists(path):
                try:
                    os.startfile(path) if os.name == 'nt' else os.system(f'open "{path}"')
                    opened = True
                    break
                except Exception as e:
                    logging.error(f"Word open error: {e}")
        
        if not opened:
            response = "Microsoft Word is not installed or I couldn't locate it."
        
        self.speak(response)
        return response

    def handle_time(self, command):
        """Tell the current time."""
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        response = f"The current time is {current_time}"
        self.speak(response)
        return response

    def handle_date(self, command):
        """Tell the current date."""
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        response = f"Today is {current_date}"
        self.speak(response)
        return response

    def handle_open_browser(self, command):
        """Open web browser."""
        response = "Opening browser."
        try:
            webbrowser.open("https://google.com")
        except Exception as e:
            logging.error(f"Browser error: {e}")
            response = "Sorry, I couldn't open the browser."
        
        self.speak(response)
        return response

    def handle_search(self, command):
        """Search on Google."""
        query = command.replace("search", "").replace("google", "").replace("look up", "").strip()
        if not query:
            response = "What would you like me to search for?"
        else:
            response = f"Searching for {query} on Google."
            try:
                webbrowser.open(f"https://www.google.com/search?q={query}")
            except Exception as e:
                logging.error(f"Search error: {e}")
                response = "Sorry, I couldn't perform the search."
        
        self.speak(response)
        return response

    def handle_exit(self, command):
        """Exit the assistant."""
        response = "Goodbye! Have a great day!"
        self.speak(response)
        return response

    def handle_unknown(self, command):
        """Handle unknown commands."""
        response = "I'm not sure how to help with that. Try asking me to search Wikipedia, play music, tell the time, or open applications."
        self.speak(response)
        return response


class VoiceAssistantApp:
    def __init__(self, root):
        """Initialize the GUI application."""
        self.root = root
        self.assistant = VoiceAssistant()
        self.is_listening = False
        self.setup_gui()

    def setup_gui(self):
        """Setup the graphical user interface."""
        self.root.title("AI Voice Assistant")
        self.root.geometry("600x500")
        self.root.configure(bg="#2c3e50")
        self.root.resizable(False, False)

        # Title
        title = Label(
            self.root, 
            text="🎤 Voice Assistant", 
            font=("Arial", 24, "bold"), 
            bg="#2c3e50", 
            fg="#ecf0f1",
            pady=20
        )
        title.pack()

        # Status label
        self.status_label = Label(
            self.root, 
            text="Ready to assist you", 
            font=("Arial", 12), 
            bg="#2c3e50", 
            fg="#95a5a6"
        )
        self.status_label.pack()

        # Button frame
        button_frame = Frame(self.root, bg="#2c3e50")
        button_frame.pack(pady=20)

        # Listen button
        self.listen_button = Button(
            button_frame, 
            text="🎙️ Start Listening", 
            command=self.listen_to_user, 
            font=("Arial", 14, "bold"), 
            bg="#27ae60", 
            fg="white", 
            padx=20, 
            pady=10,
            relief="raised",
            cursor="hand2"
        )
        self.listen_button.grid(row=0, column=0, padx=10)

        # Quit button
        quit_button = Button(
            button_frame, 
            text="❌ Quit", 
            command=self.quit_app, 
            font=("Arial", 14, "bold"), 
            bg="#e74c3c", 
            fg="white", 
            padx=20, 
            pady=10,
            relief="raised",
            cursor="hand2"
        )
        quit_button.grid(row=0, column=1, padx=10)

        # Response display
        response_label = Label(
            self.root, 
            text="Response Log:", 
            font=("Arial", 12, "bold"), 
            bg="#2c3e50", 
            fg="#ecf0f1"
        )
        response_label.pack(pady=(10, 5))

        # Text widget with scrollbar
        text_frame = Frame(self.root, bg="#2c3e50")
        text_frame.pack(padx=20, pady=10, fill="both", expand=True)

        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        self.response_text = Text(
            text_frame, 
            height=10, 
            font=("Arial", 10), 
            bg="#34495e", 
            fg="#ecf0f1",
            yscrollcommand=scrollbar.set,
            wrap="word"
        )
        self.response_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.response_text.yview)

    def listen_to_user(self):
        """Handle listening in a separate thread to avoid UI freezing."""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.listen_button.config(state="disabled", bg="#95a5a6")
        self.status_label.config(text="Listening... 🎤", fg="#3498db")
        
        def listen_thread():
            self.assistant.speak("How can I assist you?")
            command = self.assistant.listen()
            
            if command:
                self.update_response_log(f"You: {command}")
                response = self.assistant.process_command(command)
                self.update_response_log(f"Assistant: {response}")
                
                if "goodbye" in response.lower() or "exit" in command:
                    self.root.after(2000, self.quit_app)
            
            self.is_listening = False
            self.listen_button.config(state="normal", bg="#27ae60")
            self.status_label.config(text="Ready to assist you", fg="#95a5a6")
        
        Thread(target=listen_thread, daemon=True).start()

    def update_response_log(self, text):
        """Update the response log display."""
        self.response_text.insert(END, f"{text}\n\n")
        self.response_text.see(END)

    def quit_app(self):
        """Quit the application."""
        self.assistant.speak("Goodbye!")
        self.root.destroy()


if __name__ == "__main__":
    root = Tk()
    app = VoiceAssistantApp(root)
    root.mainloop()