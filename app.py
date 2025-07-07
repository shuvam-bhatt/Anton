import os
import subprocess
import sys      
import time
import traceback
from pathlib import Path
from vosk import Model, KaldiRecognizer
import pyaudio
import json
from dotenv import load_dotenv


FILES_DIR = "Anton_Files"
os.makedirs(FILES_DIR, exist_ok=True)

# PySide6 imports
from PySide6.QtCore import (QSize, Qt, QPropertyAnimation, QEasingCurve, 
                          QParallelAnimationGroup, QSequentialAnimationGroup, 
                          QTimer, Signal, Property, QObject, QThread, Slot)
from PySide6.QtGui import (QFont, QColor, QPalette, QPixmap, QIcon, 
                         QFontDatabase, QAction, QLinearGradient, QPainter, 
                         QBrush, QPen, QPainterPath)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QLineEdit, QScrollArea, QFrame, QStackedWidget,
                             QListWidget, QListWidgetItem, QSplitter, 
                             QFileDialog, QMenu, QDialog, QComboBox, 
                             QProgressBar, QGraphicsOpacityEffect, QSizePolicy,
                             QToolButton)

# Import Anton's existing functionality
load_dotenv()

# Environment Variables
AiKey = os.getenv("GEMINI_API_KEY")
SearchId = os.getenv("SEARCH_ENGINE_ID")
SearchKey = os.getenv("CUSTOM_SEARCH_KEY")

# Google AI & Search
import google.generativeai as genai
from googleapiclient.discovery import build

# TTS & STT
import pyttsx3
import speech_recognition as sr

# Configure Gemini
genai.configure(api_key=AiKey)
model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
chat = model.start_chat(history=[])

# Text-to-Speech
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()
recognizer = sr.Recognizer()

def recognize_speech():
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand that."
    except sr.RequestError:
        return "Speech recognition service unavailable."

# Search Handling
def Anton_Search(query, num_results=7):
    service = build("customsearch", "v1", developerKey=SearchKey)
    results = service.cse().list(q=query, cx=SearchId, num=num_results).execute()
    search_results = []
    if "items" in results:
        for item in results["items"]:
            search_results.append({
                "title": item["title"],
                "link": item["link"],
                "snippet": item.get("snippet", "")
            })
    return search_results

def Should_Anton_search(user_query):
    model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
    decision_prompt = f"""
    You are an intelligent assistant determining whether the user's question requires real-time or updated web information.

    User's question: "{user_query}"

    Instructions:
    - If the question is about current events, news, weather, prices, sports, recent tech updates, or anything that may have changed recently, answer **yes**.
    - If the question can be answered using general knowledge, historical facts, or does not depend on recent developments, answer **no**.

    Respond ONLY with one word: "yes" or "no".
    """
    response = model.generate_content(decision_prompt).text.strip().lower()
    return "yes" in response

def Is_Assistant_Info_Query(user_query: str) -> bool:
    keywords = [
        "who are you", "what is your name", "what can you do", "tell me about yourself",
        "who made you", "are you human", "your capabilities", "your purpose", "what are you",
        "are you ai", "are you real", "who is anton", "your identity"
    ]
    user_query = user_query.lower()
    return any(keyword in user_query for keyword in keywords)

def Anton_Identity_Response() -> str:
    return (
        "I'm Anton, your smart and helpful AI assistant. "
        "I'm designed to support you with insights, answers, and tools to make your day easier. "
        "Think of me as your go-to digital companion."
    )
def Antons_Response(user_query: str) -> str:
    """Handles all types of user input: assistant info, file commands, search-based queries, or static responses."""
    
    # Handle assistant-related identity/info queries
    if Is_Assistant_Info_Query(user_query):
        return Anton_Identity_Response()

    # Handle file-related commands
    if is_file_related_query(user_query):
        file_response = process_file_command(user_query)
        if file_response:
            return f"File Operation Complete:\n\n{file_response}"
        else:
            return "Hmm, I couldn't process that file command. Try rephrasing?"

    # Initialize model
    model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')

    # Handle search-needed queries
    if Should_Anton_search(user_query):
        search_results = Anton_Search(user_query)
        search_info = "\n".join([
            f"- Title: {res['title']}\n  URL: {res['link']}\n  Snippet: {res['snippet']}"
            for res in search_results
        ])

        search_prompt = f"""
You are Anton, a smart and helpful assistant.

The user asked: "{user_query}"

Here are relevant search results:
{search_info}

Instructions:
- Carefully extract key points from the search snippets.
- Do NOT copy them verbatim or mention they are from a search.
- Answer as naturally and clearly as you can, as if chatting with a friend.
- Be brief, helpful, and insightful.

Response:
"""
        return model.generate_content(search_prompt).text.strip()

    # Handle static queries (no search needed)
    else:
        static_prompt = f"""
You are Anton, a smart and helpful assistant.

The user asked: "{user_query}"

Instructions:
- Provide a brief, sharp, and human-like answer.
- Make the tone friendly, smart, and clear.
- Keep the message focused on the essence of the question.

Response:
"""
        return model.generate_content(static_prompt).text.strip()
FILES_DIR = "Anton_Files"
os.makedirs(FILES_DIR, exist_ok=True)

def get_file_path(filename: str) -> str:
    """Returns the full path of the file inside Anton_Files directory."""
    return os.path.join(FILES_DIR, filename)

def create_file(filename: str, content: str) -> str:
    """Creates a new file with the provided content in Anton_Files directory."""
    filepath = get_file_path(filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File '{filename}' created at '{filepath}'."
    except Exception as e:
        return f"Error creating file: {e}"

def read_file(filename: str) -> str:
    """Reads and returns the content of a file."""
    filepath = get_file_path(filename)

    if not os.path.exists(filepath):
        return f"File `{filename}` not found."

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        summary_prompt = (
            f"Summarize this file content in plain, helpful language for the user:\n\n{content}\n\n"
            f"Include only the main ideas or purpose of the content."
        )
        summary = model.generate_content(summary_prompt).text.strip()

        return (
            f"Contents of `{filename}`:\n\n"
            f"Summary:\n{summary}"
        )

    except Exception as e:
        return f"Error reading `{filename}`: {e}"

def update_file(filename: str, new_content: str) -> str:
    """Overwrites the file with new content."""
    """Overwrites the file with new content and shows a summary of changes."""
    filepath = get_file_path(filename)

    if not os.path.exists(filepath):
        return f"File `{filename}` does not exist."

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            old_content = f.read()

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # Generate a summary of the changes
        change_prompt = (
            f"Compare the previous and new version of this file. Describe the changes clearly:\n\n"
            f"Previous:\n{old_content}\n\nNew:\n{new_content}\n\n"
            f"Summarize the changes in bullet points."
        )
        change_summary = model.generate_content(change_prompt).text.strip()
        summary_prompt = (
            f"Summarize the overall meaning or goal of the following new file content:\n\n{new_content}"
        )
        content_summary = model.generate_content(summary_prompt).text.strip()

        return (
            f"`{filename}` was updated.\n\n"
            f"What changed:\n{change_summary}\n\n"
            f"New content summary:\n{content_summary}"
        )
    except Exception as e:
        return f"Error updating `{filename}`: {e}"
    

def append_to_file(filename: str, additional_content: str) -> str:
    filepath = get_file_path(filename)

    if not os.path.exists(filepath):
        return f"File `{filename}` not found."

    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write("\n" + additional_content)

        # Optional: summarize what was appended
        summary_prompt = (
            f"Summarize in 2-3 sentences the purpose or meaning of the following appended content"
        )
        summary = model.generate_content(summary_prompt).text.strip()

        return f"Appended to `{filename}`.\n\nSummary of what was added:\n{summary}"

    except Exception as e:
        return f"Failed to append to `{filename}`: {e}"
    
def delete_file(filename: str) -> str:
    """Deletes a file."""
    filepath = get_file_path(filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return f"File '{filename}' deleted successfully."
        except Exception as e:
            return f"Error deleting file: {e}"
    return f"File '{filename}' does not exist."

def list_files() -> str:
    """Lists all files in the Anton_Files directory."""
    try:
        files = os.listdir(FILES_DIR)
        if not files:
            return "No files found in the Anton_Files directory."
        
        file_info = []
        for filename in files:
            filepath = get_file_path(filename)
            size = os.path.getsize(filepath)
            modified = os.path.getmtime(filepath)
            file_info.append(f"{filename} - {size} bytes")
        
        return "Files in Anton_Files directory:\n" + "\n".join(file_info)
    except Exception as e:
        return f"Error listing files: {e}"

def open_file(filename: str) -> str:
    """Opens a file using the appropriate program based on the file extension."""
    filepath = get_file_path(filename)
    
    if not os.path.exists(filepath):
        return f"File '{filename}' does not exist."

    try:
        if filename.endswith(('.cpp', '.py', '.txt', '.html', '.js', '.css')):
            command = f"code \"{filepath}\"" 
        elif filename.endswith('.pdf'):
            command = f"start \"\" \"{filepath}\"" if os.name == 'nt' else f"xdg-open \"{filepath}\""
        elif filename.endswith(('.docx', '.doc')):
            command = f"start winword \"{filepath}\"" if os.name == 'nt' else f"libreoffice \"{filepath}\""
        else:
            if os.name == 'nt': 
                command = f"start \"\" \"{filepath}\""

        subprocess.run(command, shell=True)
        return f"Opening '{filename}'..."
    except Exception as e:
        return f"Error opening file: {e}"

def process_file_command(user_query: str) -> str:
    """
    Processes file operation commands.
    Added commands:
      - "list files"
      - "append to file <filename> with <prompt>"
    """
    lower_q = user_query.lower().strip()
    if lower_q == "list files":
        return list_files()
    
    if lower_q.startswith("create file"):
        try:
            parts = user_query.split("with", 1)
            filename = parts[0].replace("create file", "", 1).strip()
            if len(parts) > 1:
                content_prompt = parts[1].strip()
                generation_prompt = f"Write content for a file named '{filename}'. {content_prompt}"
                file_content = model.generate_content(generation_prompt).text
            else:
                file_content = ""
                
            return create_file(filename, file_content)
        except Exception as e:
            return f"Error in create file command: {e}"
    elif lower_q.startswith("read file"):
        try:
            filename = user_query.replace("read file", "", 1).strip()
            return read_file(filename)
        except Exception as e:
            return f"Error in read file command: {e}"
    elif lower_q.startswith("update file"):
        try:
            parts = user_query.split("with", 1)
            filename = parts[0].replace("update file", "", 1).strip()
            
            if len(parts) > 1:
                new_content_prompt = parts[1].strip()
                generation_prompt = f"Write updated content for a file named '{filename}'. {new_content_prompt}"
                new_content = model.generate_content(generation_prompt).text
            else:
                new_content = ""
                
            return update_file(filename, new_content)
        except Exception as e:
            return f"Error in update file command: {e}"

    elif lower_q.startswith("append to file"):
        try:
            parts = user_query.split("with", 1)
            filename = parts[0].replace("append to file", "", 1).strip()
            
            if len(parts) > 1:
                append_content_prompt = parts[1].strip()
                # Generate content to append using LLM
                generation_prompt = f"Write additional content to append to a file named '{filename}'. {append_content_prompt}"
                append_content = model.generate_content(generation_prompt).text
            else:
                append_content = ""
                
            return append_to_file(filename, append_content)
        except Exception as e:
            return f"Error in append to file command: {e}"

    elif lower_q.startswith("delete file"):
        try:
            filename = user_query.replace("delete file", "", 1).strip()
            return delete_file(filename)
        except Exception as e:
            return f"Error in delete file command: {e}"

    elif lower_q.startswith("open file"):
        try:
            filename = user_query.replace("open file", "", 1).strip()
            return open_file(filename)
        except Exception as e:
            return f"Error in open file command: {e}"
    return None

def is_file_related_query(user_query: str) -> bool:
    keywords = [
        "create file", "read file", "update file", "append to file", 
        "delete file", "open file", "list files", "write to file"
    ]
    lower_q = user_query.lower()
    return any(kw in lower_q for kw in keywords)

class SpeechRecognitionThread(QThread):
    result = Signal(str)
    listening_status = Signal(bool)
    
    def run(self):
        self.listening_status.emit(True)
        recognized_text = recognize_speech()
        self.result.emit(recognized_text)
        self.listening_status.emit(False)

# Speech Recognition Thread
class SpeechRecognitionThread(QThread):
    result = Signal(str)
    listening_status = Signal(bool)
    
    def __init__(self, vosk_stt):
        super().__init__()
        self.vosk_stt = vosk_stt
        
    def run(self):
        self.listening_status.emit(True)
        recognized_text = recognize_speech(self.vosk_stt)
        self.result.emit(recognized_text)
        self.listening_status.emit(False)

class SpeechRecognitionThread(QThread):
    result = Signal(str)
    listening_status = Signal(bool)
    
    def run(self):
        self.listening_status.emit(True)
        recognized_text = recognize_speech()
        self.result.emit(recognized_text)
        self.listening_status.emit(False)

# Response Processing Thread
class ResponseThread(QThread):
    result = Signal(str)
    progress = Signal(int)
    
    def __init__(self, query):
        super().__init__()
        self.query = query
        
    def run(self):
            self.progress.emit(20)
            file_command_result = process_file_command(self.query)
            
            if file_command_result:
                self.result.emit(file_command_result)
                self.progress.emit(100)
                return
            else:
                if self.query.lower() in ["who are you", "who are you ?", "what are you", "what are you ?", "introduce yourself"]:
                    response = "I am Anton, your AI assistant. How can I help you today?"
                else:
                    # Simulate progress for better UX
                    self.progress.emit(50)
                    response = Antons_Response(self.query)
                    self.progress.emit(80)
                self.result.emit(response)
            self.progress.emit(100)

# Custom Widgets
class PulseAnimation(QObject):
    def __init__(self, target, property_name, start, end, duration):
        super().__init__()
        self.animation = QPropertyAnimation(target, property_name)
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.setDuration(duration)
        self.animation.setLoopCount(-1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
    def start(self):
        self.animation.start()
        
    def stop(self):
        self.animation.stop()

class WaveCircle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(40, 40)
        self._radius = 20
        self._color = QColor(0, 123, 255)
        self._waves = []
        self._active = False
        
    def paintEvent(self, event):
        if not self._active:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw center circle
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.width()/2 - self._radius/2, 
                          self.height()/2 - self._radius/2, 
                          self._radius, self._radius)
        
        # Draw waves
        for radius, opacity in self._waves:
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(self._color.red(), self._color.green(), 
                               self._color.blue(), int(255 * opacity)), 2))
            painter.drawEllipse(self.width()/2 - radius/2, 
                              self.height()/2 - radius/2, 
                              radius, radius)
    
    def start_waves(self):
        self._active = True
        self._waves = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_waves)
        self._timer.start(100)
        
    def stop_waves(self):
        self._active = False
        if hasattr(self, '_timer'):
            self._timer.stop()
        self.update()
        
    def _update_waves(self):
        # Add new wave
        if len(self._waves) == 0 or self._waves[-1][0] > self._radius * 1.5:
            self._waves.append([self._radius, 1.0])
            
        # Update existing waves
        new_waves = []
        for radius, opacity in self._waves:
            new_radius = radius + 1
            new_opacity = opacity - 0.03
            if new_opacity > 0:
                new_waves.append([new_radius, new_opacity])
        self._waves = new_waves
        self.update()

class ThemeColors:
    
    PRIMARY = "#0F0F17"           # Dark background (Perplexity dark theme base)
    SECONDARY = "#1A1A2E"         # Slightly lighter background
    ACCENT = "#6F58C4"            # Purple accent (Perplexity primary)
    ACCENT_BRIGHT = "#8A70DE"     # Lighter purple accent
    TEXT_PRIMARY = "#FFFFFF"      # Bright text
    TEXT_SECONDARY = "#A0A0B8"    # Soft lavender-gray text
    USER_BUBBLE = "#1A1A2E"       # Dark bubble for user messages
    ASSISTANT_BUBBLE = "#2D2B55"  # Deep indigo for assistant messages
    GRADIENT_START = "#0F0F17"    # Gradient start
    GRADIENT_END = "#1A1A2E"      # Gradient end
    SUCCESS = "#BB85FC"           # Soft purple for success (replacing green)
    ERROR = "#FF5370"             # Bright coral for errors
    WARNING = "#FFCB6B"           # Amber yellow for warnings


class ChatBubble(QFrame):
    def __init__(self, text, is_user=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.text = text
        
        self.setObjectName("chatBubble")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
        self.setMinimumWidth(200)
        self.setMaximumWidth(600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Create layout FIRST
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Create message text FIRST
        self.message_label = QLabel(text)  # CREATE LABEL FIRST
        self.message_label.setObjectName("messageText")
        self.message_label.setWordWrap(True)  # THEN SET PROPERTIES
        self.message_label.setMaximumWidth(550)
        self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.message_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.message_label)
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Create message text
        self.message_label = QLabel(text)
        self.message_label.setObjectName("messageText")
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.message_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.message_label)
        
        # Create timestamp
        current_time = time.strftime("%H:%M")
        self.time_label = QLabel(current_time)
        self.time_label.setObjectName("timeLabel")
        self.time_label.setFont(QFont("Segoe UI", 8))
        self.time_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.time_label)
        
        # Set style based on sender
        self.update_style()
            
    def update_style(self):
        if self.is_user:
            self.setStyleSheet(f"""
                #chatBubble {{
                    background-color: {ThemeColors.USER_BUBBLE};
                    border-radius: 18px;
                    border-top-right-radius: 4px;
                    border: none;
                }}
                #messageText {{
                    color: {ThemeColors.TEXT_PRIMARY};
                    background: transparent;
                }}
                #timeLabel {{
                    color: rgba(248, 248, 242, 0.7);
                    background: transparent;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                #chatBubble {{
                    background-color: {ThemeColors.ASSISTANT_BUBBLE};
                    border-radius: 18px;
                    border-top-left-radius: 4px;
                    border: none;
                }}
                #messageText {{
                    color: {ThemeColors.TEXT_PRIMARY};
                    background: transparent;
                }}
                #timeLabel {{
                    color: rgba(248, 248, 242, 0.7);
                    background: transparent;
                }}
            """)
            
    def enterEvent(self, event):
        # Subtle hover effect
        if self.is_user:
            self.setStyleSheet(f"""
                #chatBubble {{
                    background-color: #2D2B55;
                    border-radius: 18px;
                    border-top-right-radius: 4px;
                    border: none;
                }}
                #messageText {{
                    color: {ThemeColors.TEXT_PRIMARY};
                    background: transparent;
                }}
                #timeLabel {{
                    color: rgba(248, 248, 242, 0.7);
                    background: transparent;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                #chatBubble {{
                    background-color: #413C7A;
                    border-radius: 18px;
                    border-top-left-radius: 4px;
                    border: none;
                }}
                #messageText {{
                    color: {ThemeColors.TEXT_PRIMARY};
                    background: transparent;
                }}
                #timeLabel {{
                    color: rgba(248, 248, 242, 0.7);
                    background: transparent;
                }}
            """)
        
    def leaveEvent(self, event):
        # Reset to original style
        self.update_style()

class RoundedButton(QPushButton):
    def __init__(self, text="", icon=None, color=ThemeColors.ACCENT, parent=None):
        super().__init__(text, parent)
        self.setMinimumSize(40, 40)
        if icon:
            self.setIcon(icon)
        
        self.color = color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {ThemeColors.TEXT_PRIMARY};
                border-radius: 20px;
                font-weight: bold;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(color, 0.1)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 0.1)};
            }}
        """)
        
        # Add animation effect
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def _lighten_color(self, color, factor=0.1):
        """Lighten the given color by the factor"""
        c = QColor(color)
        h, s, l, a = c.getHsl()
        return QColor.fromHsl(h, s, min(255, int(l * (1 + factor))), a).name()
    
    def _darken_color(self, color, factor=0.1):
        """Darken the given color by the factor"""
        c = QColor(color)
        h, s, l, a = c.getHsl()
        return QColor.fromHsl(h, s, max(0, int(l * (1 - factor))), a).name()
        
    def enterEvent(self, event):
        rect = self.geometry()
        self._animation.setStartValue(rect)
        self._animation.setEndValue(rect.adjusted(-2, -2, 2, 2))
        self._animation.start()
        
    def leaveEvent(self, event):
        rect = self.geometry()
        self._animation.setStartValue(rect)
        self._animation.setEndValue(rect.adjusted(2, 2, -2, -2))
        self._animation.start()

class AnimatedLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set style
        self.setStyleSheet(f"""
            QLineEdit {{
                padding: 14px;
                border-radius: 24px;
                border: 2px solid {ThemeColors.ACCENT};
                background-color: {ThemeColors.SECONDARY};
                font-size: 14px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 2px solid {ThemeColors.ACCENT_BRIGHT};
            }}
        """)
        
        # Animation for focus
        self.focus_animation = QPropertyAnimation(self, b"styleSheet")
        self.focus_animation.setDuration(300)
        
    def focusInEvent(self, event):
        start_style = f"""
            QLineEdit {{
                padding: 14px;
                border-radius: 24px;
                border: 2px solid {ThemeColors.ACCENT};
                background-color: {ThemeColors.SECONDARY};
                font-size: 14px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """
        end_style = f"""
            QLineEdit {{
                padding: 14px;
                border-radius: 24px;
                border: 2px solid {ThemeColors.ACCENT_BRIGHT};
                background-color: {ThemeColors.SECONDARY};
                font-size: 14px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """
        self.focus_animation.setStartValue(start_style)
        self.focus_animation.setEndValue(end_style)
        self.focus_animation.start()
        super().focusInEvent(event)
        
    def focusOutEvent(self, event):
        start_style = f"""
            QLineEdit {{
                padding: 14px;
                border-radius: 24px;
                border: 2px solid {ThemeColors.ACCENT_BRIGHT};
                background-color: {ThemeColors.SECONDARY};
                font-size: 14px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """
        end_style = f"""
            QLineEdit {{
                padding: 14px;
                border-radius: 24px;
                border: 2px solid {ThemeColors.ACCENT};
                background-color: {ThemeColors.SECONDARY};
                font-size: 14px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """
        self.focus_animation.setStartValue(start_style)
        self.focus_animation.setEndValue(end_style)
        self.focus_animation.start()
        super().focusOutEvent(event)

class FileListWidget(QWidget):
    fileSelected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        self.title_label = QLabel("Files")
        self.title_label.setObjectName("fileTitle")
        self.title_label.setStyleSheet(f"#fileTitle {{ font-weight: bold; font-size: 16px; color: {ThemeColors.TEXT_PRIMARY}; background: transparent; }}")
        layout.addWidget(self.title_label)
        
        # File list
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("fileList")
        self.list_widget.setStyleSheet(f"""
            #fileList {{
                border: 1px solid {ThemeColors.ACCENT};
                border-radius: 10px;
                background-color: {ThemeColors.SECONDARY};
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            #fileList::item {{
                padding: 10px;
                border-bottom: 1px solid #44475a;
                background: transparent;
            }}
            #fileList::item:hover {{
                background-color: #44475a;
            }}
            #fileList::item:selected {{
                background-color: {ThemeColors.ACCENT};
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self.list_widget)
        
        # Button layout
        btn_layout = QHBoxLayout()
        
        # Refresh button
        self.refresh_btn = RoundedButton("Refresh", color=ThemeColors.SUCCESS)
        self.refresh_btn.clicked.connect(self.refresh_files)
        btn_layout.addWidget(self.refresh_btn)
        
        # New file button
        self.new_file_btn = RoundedButton("New", color=ThemeColors.ACCENT_BRIGHT)
        self.new_file_btn.clicked.connect(self.create_new_file)
        btn_layout.addWidget(self.new_file_btn)
        
        layout.addLayout(btn_layout)
        
        # Initial file loading
        self.refresh_files()
        
        # Connect signals
        self.list_widget.itemDoubleClicked.connect(self.open_selected_file)
        
    def refresh_files(self):
        self.list_widget.clear()
        files = os.listdir(FILES_DIR)
        for filename in files:
            file_path = os.path.join(FILES_DIR, filename)
            size = os.path.getsize(file_path)
            size_str = f"{size} bytes"
            item = QListWidgetItem(f"{filename} ({size_str})")
            item.setData(Qt.UserRole, filename)
            self.list_widget.addItem(item)
            
    def create_new_file(self):
        filename, ok = QFileDialog.getSaveFileName(self, "Create New File", 
                                                 FILES_DIR, 
                                                 "All Files (*)")
        if ok and filename:
            base_name = os.path.basename(filename)
            create_file(base_name, "")
            self.refresh_files()
            
    def open_selected_file(self, item):
        filename = item.data(Qt.UserRole)
        self.fileSelected.emit(filename)

# Main Application Window
class AntonApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anton AI Assistant")
        self.setMinimumSize(1000, 700)
        self.setObjectName("mainWindow")
        
        # Setup icon
        # self.setWindowIcon(QIcon("icon.png"))
        
        # Setup central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left sidebar
        sidebar_widget = QWidget()
        sidebar_widget.setObjectName("sidebarWidget")
        sidebar_widget.setMaximumWidth(250)
        sidebar_widget.setStyleSheet(f"#sidebarWidget {{ background-color: {ThemeColors.PRIMARY}; }}")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(20)
        
        # Logo and title
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        logo_label = QLabel("Anton")
        logo_label.setObjectName("logoLabel")
        logo_label.setStyleSheet(f"#logoLabel {{ font-size: 26px; font-weight: bold; color: {ThemeColors.ACCENT_BRIGHT}; background: transparent; }}")
        header_layout.addWidget(logo_label)
        
        ai_label = QLabel("AI Assistant")
        ai_label.setObjectName("aiLabel")
        ai_label.setStyleSheet(f"#aiLabel {{ font-size: 16px; color: {ThemeColors.ACCENT}; background: transparent; }}")
        header_layout.addWidget(ai_label)
        header_layout.addStretch()
        sidebar_layout.addWidget(header_widget)
        
        # Add decorative line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"background-color: {ThemeColors.ACCENT}; max-height: 1px;")
        sidebar_layout.addWidget(line)
        
        # File browser
        self.file_list_widget = FileListWidget()
        sidebar_layout.addWidget(self.file_list_widget)
        
        # Add sidebar to main layout
        main_layout.addWidget(sidebar_widget)
        
        # Vertical divider
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet(f"color: {ThemeColors.ACCENT};")
        main_layout.addWidget(divider)
        
        # Main content area
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet(f"#contentWidget {{ background-color: {ThemeColors.PRIMARY}; }}")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)  # Increased spacing between elements
        
        # Chat title
        chat_title = QLabel("Conversation")
        chat_title.setObjectName("chatTitle")
        chat_title.setStyleSheet(f"#chatTitle {{ font-size: 20px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY}; margin-bottom: 10px; background: transparent; }}")
        content_layout.addWidget(chat_title)
        
        # Chat display area - set to expand and take available space
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setFrameShape(QFrame.NoFrame)
        self.chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Make it expand
        self.chat_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {ThemeColors.PRIMARY};
                border: none;
            }}
        """)
        
        self.chat_widget = QWidget()
        self.chat_widget.setObjectName("chatWidget")
        self.chat_widget.setStyleSheet(f"#chatWidget {{ background-color: {ThemeColors.PRIMARY}; }}")
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(20)
        self.chat_layout.setContentsMargins(10, 10, 10, 20)  # Added more bottom margin
        
        self.chat_area.setWidget(self.chat_widget)
        content_layout.addWidget(self.chat_area, 1)  # Set stretch factor to 1 to take available space
        
        # Add a spacer line to separate chat and input
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {ThemeColors.SECONDARY};")
        content_layout.addWidget(separator)
        
        # Input area - fixed at bottom with fixed height
        input_widget = QWidget()
        input_widget.setObjectName("inputWidget")
        input_widget.setStyleSheet(f"#inputWidget {{ background-color: {ThemeColors.PRIMARY}; }}")
        input_widget.setFixedHeight(80)  # Fixed height for input area
        input_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Fixed height policy
        
        # Create a vertical layout for input area containing progress bar and input controls
        input_vbox = QVBoxLayout(input_widget)
        input_vbox.setContentsMargins(0, 10, 0, 0)
        input_vbox.setSpacing(8)
        
        # Progress bar for response generation
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {ThemeColors.SECONDARY};
                border-radius: 1px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.ACCENT_BRIGHT};
                border-radius: 1px;
            }}
        """)
        input_vbox.addWidget(self.progress_bar)
        
        # Input controls layout
        input_controls = QHBoxLayout()
        input_controls.setContentsMargins(0, 0, 0, 0)
        input_controls.setSpacing(10)
        
        # Input field
        self.input_field = AnimatedLineEdit()
        self.input_field.setPlaceholderText("Ask Anton something...")
        self.input_field.returnPressed.connect(self.send_message)
        input_controls.addWidget(self.input_field)
        
        # Send button
        self.send_button = RoundedButton("Send", color=ThemeColors.ACCENT_BRIGHT)
        self.send_button.clicked.connect(self.send_message)
        input_controls.addWidget(self.send_button)
        
        # Voice button stack
        self.voice_stack = QStackedWidget()
        self.voice_stack.setFixedSize(50, 50)
        
        # Voice input button
        self.voice_button = RoundedButton("", color=ThemeColors.SUCCESS)
        self.voice_button.setIcon(QIcon.fromTheme("audio-input-microphone"))
        self.voice_button.setFixedSize(50, 50)
        self.voice_button.clicked.connect(self.start_voice_input)
        
        # Voice input indicator
        self.voice_indicator = WaveCircle()
        self.voice_indicator.setFixedSize(50, 50)
        self.voice_indicator.setVisible(False)
        self.voice_indicator._color = QColor(ThemeColors.SUCCESS)
        
        self.voice_stack.addWidget(self.voice_button)     
        self.voice_stack.addWidget(self.voice_indicator) 
        input_controls.addWidget(self.voice_stack)
        
        # Add input controls to the input vertical layout
        input_vbox.addLayout(input_controls)
        
        # Connect file selector
        self.file_list_widget.fileSelected.connect(self.handle_file_selection)
        
        # Add input widget to content layout
        content_layout.addWidget(input_widget)
        main_layout.addWidget(content_widget, 1)
        
        # Setup speech recognition thread
        self.speech_thread = None
        
        # Setup opacity animation for new messages
        self.opacity_animation = None
        
        # Setup progress animation
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(300)
        self.progress_animation.setEasingCurve(QEasingCurve.OutQuad)
        
        # Add a welcome message
        self.add_message("Hello! I'm Anton, your AI assistant. How can I help you today?", is_user=False)
        
        # Apply global styles
        self.apply_global_styles()
        
    def apply_global_styles(self):
        """Apply global application styles with improved consistency"""
        self.setStyleSheet(f"""
            #mainWindow {{
                background-color: {ThemeColors.PRIMARY};
            }}
            QWidget {{
                font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
                background-color: transparent;
            }}
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY};
                background-color: transparent;
            }}
            QScrollArea {{
                background-color: {ThemeColors.PRIMARY};
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {ThemeColors.PRIMARY};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {ThemeColors.ACCENT};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)
        
    def add_message(self, message, is_user=True):
        """Add a message to the chat area"""
        message_widget = ChatBubble(message, is_user)
        
        # Add alignment container
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        if is_user:
            container_layout.addStretch()
            container_layout.addWidget(message_widget)
        else:
            container_layout.addWidget(message_widget)
            container_layout.addStretch()
            
        # Add fade-in animation
        opacity_effect = QGraphicsOpacityEffect(message_widget)
        message_widget.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0)
        
        self.chat_layout.addWidget(container)
        
        self.opacity_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.opacity_animation.setDuration(300)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.opacity_animation.start()
        scroll_bar = self.chat_area.verticalScrollBar()
        scroll_anim = QPropertyAnimation(scroll_bar, b"value")
        scroll_anim.setDuration(500)
        scroll_anim.setStartValue(scroll_bar.value())
        scroll_anim.setEndValue(scroll_bar.maximum())
        scroll_anim.setEasingCurve(QEasingCurve.OutQuint)
        scroll_anim.start()
        
        # Scroll to the bottom
        QTimer.singleShot(100, lambda: self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()))
            
    def send_message(self):
        """Send a message to Anton"""
        message = self.input_field.text().strip()
        if not message:
            return
            
        # Add message to chat
        self.add_message(message, is_user=True)
        self.input_field.clear()
        
        # Show progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Process the message in a thread
        self.response_thread = ResponseThread(message)
        self.response_thread.result.connect(self.handle_response)
        self.response_thread.progress.connect(self.update_progress)
        self.response_thread.start()
        
    def update_progress(self, value):
        """Update progress bar with animation"""
        self.progress_animation.stop()
        self.progress_animation.setStartValue(self.progress_bar.value())
        self.progress_animation.setEndValue(value)
        self.progress_animation.start()
        
    def handle_response(self, response):
        """Handle the response from Anton"""
        # Add response to chat
        self.add_message(response, is_user=False)
        
        # Hide progress bar after a moment
        QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
        
        # Speak the response
        QTimer.singleShot(100, lambda: speak(response))
        
    def start_voice_input(self):
        """Start voice input"""
        # Hide the voice button and show indicator
        self.voice_indicator.start_waves()
        
        # Start speech recognition in a thread
        self.speech_thread = SpeechRecognitionThread()
        self.speech_thread.result.connect(self.handle_speech_result)
        self.speech_thread.listening_status.connect(self.update_listening_status)
        self.speech_thread.start()
        
    def handle_speech_result(self, text):
        """Handle speech recognition result"""
        if text and not text.startswith("Sorry"):
            self.input_field.setText(text)
            QTimer.singleShot(500, self.send_message)
        else:
            self.add_message(text, is_user=False)
            
    def update_listening_status(self, is_listening):
        """Update the UI listening status"""
        self.voice_stack.setCurrentIndex(1 if is_listening else 0)
        if not is_listening:
            self.voice_indicator.stop_waves()
            self.voice_indicator.stop_waves()
            self.voice_indicator.setVisible(False)
            self.voice_button.setVisible(True)
    
    def handle_file_selection(self, filename):
        result = open_file(filename)
        self.add_message(f"File opened: {filename}", is_user=True)
        self.add_message(result, is_user=False)

# Add a splash screen for additional animation
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 350)
        self.setObjectName("splashScreen")
        
        # Center the splash screen
        center_point = QApplication.primaryScreen().availableGeometry().center()
        self.move(center_point - self.rect().center())
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Anton AI")
        title.setObjectName("splashTitle")
        title.setStyleSheet(f"#splashTitle {{ font-size: 56px; font-weight: bold; color: {ThemeColors.ACCENT_BRIGHT}; letter-spacing: 1px; background: transparent; }}")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Your Intelligent Assistant")
        subtitle.setObjectName("splashSubtitle")
        subtitle.setStyleSheet(f"#splashSubtitle {{ font-size: 24px; color: {ThemeColors.ACCENT}; margin-bottom: 20px; background: transparent; }}")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {ThemeColors.SECONDARY};
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                          stop:0 {ThemeColors.ACCENT}, 
                                          stop:1 {ThemeColors.ACCENT_BRIGHT});
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.progress)
        
        # Loading text
        self.loading_text = QLabel("Loading...")
        self.loading_text.setObjectName("loadingText")
        self.loading_text.setStyleSheet(f"#loadingText {{ font-size: 16px; color: {ThemeColors.TEXT_SECONDARY}; margin-top: 10px; background: transparent; }}")
        self.loading_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.loading_text)
        
        # Animation
        self.loading_animation = QPropertyAnimation(self.progress, b"value")
        self.loading_animation.setDuration(2500)
        self.loading_animation.setStartValue(0)
        self.loading_animation.setEndValue(100)
        self.loading_animation.setEasingCurve(QEasingCurve.OutInQuint)
        self.loading_animation.finished.connect(self.close)
        
        # Loading text animation
        self.loading_texts = ["Loading resources...", "Initializing AI models...", "Almost ready...", "Preparing your experience..."]
        self.text_timer = QTimer(self)
        self.text_timer.timeout.connect(self.update_loading_text)
        self.text_timer.start(700)
        
        # Start the animation
        self.loading_animation.start()
        
    def update_loading_text(self):
        """Update the loading text"""
        current_text = self.loading_text.text()
        index = self.loading_texts.index(current_text) if current_text in self.loading_texts else -1
        next_index = (index + 1) % len(self.loading_texts)
        self.loading_text.setText(self.loading_texts[next_index])
        
    def paintEvent(self, event):
        """Paint the background with rounded corners and blur effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
        
        # Create a subtle glow effect behind the text with our purple theme
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(ThemeColors.PRIMARY))
        gradient.setColorAt(1, QColor(ThemeColors.SECONDARY))
        painter.fillPath(path, QBrush(gradient))
        
        # Add subtle border with accent color
        painter.setPen(QPen(QColor(ThemeColors.ACCENT), 2))
        painter.drawRoundedRect(1, 1, self.width()-2, self.height()-2, 20, 20)

def main():
    try:
        app = QApplication(sys.argv)
        
        # Set application font
        font = QFont("Segoe UI", 10)
        app.setFont(font)
        
        print("Starting Anton app...")
        
        try:
            # Test model initialization
            test_model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
            print("Model initialized successfully")
        except Exception as model_error:
            print(f"Error initializing Gemini model: {model_error}")
            # Fallback to simpler model configuration if needed
        
        # Show splash screen
        try:
            splash = SplashScreen()
            splash.show()
            print("Splash screen created")
            
            # Create main window
            main_window = AntonApp()
            print("Main window created")
            
            # When splash screen closes, show main window
            splash.loading_animation.finished.connect(lambda: main_window.show())
            
            sys.exit(app.exec())
        except Exception as ui_error:
            print(f"Error creating UI components: {ui_error}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"Critical error in main function: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()