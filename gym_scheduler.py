import re
import speech_recognition as sr
from gtts import gTTS
import winsound
from pydub import AudioSegment
import schedule
import time
import threading


#Listening for commands function from the user
def listen_for_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as mic:
        print("Listening to your commands...")
        recognizer.adjust_for_ambient_noise(mic)
        try:
            recording = recognizer.listen(mic, timeout=5) 
            order = recognizer.recognize_google(recording)
            print("You said:", order)
            return order.lower()
        except sr.UnknownValueError:
            print("Can't understand audio.")
            return None
        except sr.RequestError:
            print("Error occured accessing Google Speech Recognition API.")
            return None
        except sr.WaitTimeoutError:
            print("Waiting timeout error occured")
            return None

# Text-to-speech responding to user function 
def respond(response_text):
    print(response_text)
    txtToSpeech = gTTS(text=response_text, lang='en')
    txtToSpeech.save("response.mp3")
    audio = AudioSegment.from_mp3("response.mp3")
    audio.export("response.wav", format="wav")
    winsound.PlaySound("response.wav", winsound.SND_FILENAME)

# Parse time input formats said by user function
def parse_time(time_input):
    """
    Handles time formats spoken by the user e.g '8 a m', '8 o'clock', '14:30' into 24-hour format (HH:MM).
    """
    time_input = time_input.lower()
    time_input = re.sub(r"[^\w\s:]", "", time_input)  # for removing excess chars

    # this section for matching HH:MM format
    match = re.match(r"^(?P<hour>[01]?\d|2[0-3]):(?P<minute>[0-5]\d)$", time_input)
    if match:
        return f"{int(match.group('hour')):02}:{int(match.group('minute')):02}"

    # This section for matching time in spoken format, like '8 a m', '8'
    match = re.match(r"(?P<hour>\d+)(\s*(?P<period>am|pm|a m|p m)?)", time_input)
    if match:
        hour = int(match.group("hour"))
        period = match.group("period")
        if period in ("pm", "p m") and hour < 12:
            hour += 12
        elif period in ("am", "a m") and hour == 12:
            hour = 0
        return f"{hour:02}:00"

    # This section for matching 'o'clock' format
    match = re.match(r"(?P<hour>\d+)\s*o'clock", time_input)
    if match:
        return f"{int(match.group('hour')):02}:00"

    return None  # When input is invalid

# This dictionary handles all gym sessions scheduled
gym_scheduler = {}

# Function to schedule a gym reminder
def gym_reminder(day, time_set):
    respond(f"Now is the time for your gym workout set on {day.capitalize()} at {time_set}!")

# Function to get valid input
def get_valid_input(prompt, valid_options=None):
    """Prompt the user until valid input is received."""
    while True:
        respond(prompt)
        user_input = listen_for_command()
        if user_input:
            if not valid_options or user_input in valid_options:
                return user_input
            else:
                respond(f"Sorry, I didn't understand that. Please choose from {', '.join(valid_options)}.")
        else:
            respond("I couldn't hear you. Please try again.")

# Function to set a gym workout schedule
def set_gym_scheduler():
    """Set a gym workout reminder for a specific day and time."""
    global gym_scheduler

    # Ask for the day
    week_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    day_command = get_valid_input("On which day would you like to schedule your gym session?", week_days)
    
    # Ask for the time and validate format
    while True:
        time_command = get_valid_input("At what time do you want to schedule you gym session?")
        
        # Convert and validate time
        parsed_time = parse_time(time_command)
        if parsed_time:
            try:
                # Schedule the gym reminder
                getattr(schedule.every(), day_command).at(parsed_time).do(gym_reminder, day=day_command, time_key=parsed_time)
                gym_scheduler[f"{day_command.capitalize()} at {parsed_time}"] = "Gym Session"
                respond(f"Your gym session has been scheduled for {day_command.capitalize()} at {parsed_time}.")
                break
            except ValueError:
                respond("Invalid time. Please try again.")
        else:
            respond("I couldn't understand the time format.")

# This function to show the list of all scheduled gym sessions
def list_gym_schedule():
    if gym_scheduler:
        respond("Your scheduled gym sessions are as followed:")
        for schedule_time in gym_scheduler.keys():
            respond(f"{schedule_time}")
    else:
        respond("You have no gym sessions scheduled.")

# Scheduler thread to keep reminders running
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Main function for voice commands
def main():
    respond("Hey!, This is your personal gym scheduler. How can I help you?")
    
    # Start the scheduler in a separate thread
    threading.Thread(target=run_scheduler, daemon=True).start()

    while True:
        
        command = listen_for_command()
        if command:
                if "ria" in command:
                    respond("Yes, how can I assist you?")
                elif re.search(r"\bschedule gym\b", command):
                    set_gym_scheduler()
                elif re.search(r"\blist gym sessions\b", command):
                    list_gym_schedule()
                elif "exit" or "thank you" in command:
                    respond("Sure! Stay strong and fit.")
                    break
                else:
                    respond("Apologize, I couldn't understand your command.")
        else:
            respond("I didn't understand that. please say that again.")

if __name__ == "__main__":
    main()
