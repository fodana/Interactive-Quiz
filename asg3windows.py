import random
import sys
import threading
import time
import os
import json
import getpass

# Global variables
question_list = []
correct = 0
incorrect = 0
questions_answered = 0
log_file = "quiz_log.dat"
log_dir = "quiz_logs"
question_file = ""
stored_options = {}


class bcolors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Function to load questions from file
def load_questions(file_path):
    try:
        with open(file_path, 'r') as f:
            current_q = []
            lines = [line for line in f.readlines() if line.strip()]

            for line in lines:
                if line[:2].lower() == "@q":
                    current_q = [line.rstrip('\n')]
                    while True:
                        line = f.readline().rstrip('\n')
                        if not line or line[:2].lower() == "@a":
                            break
                        current_q.append(line)
                elif line[:2].lower() == "@e" and current_q:
                    current_q.append(line.rstrip('\n'))
                    question_list.append(current_q)
                    current_q = []
                elif current_q:
                    current_q.append(line.rstrip('\n'))

            random.shuffle(question_list)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        sys.exit(1)

    return question_list


# Function to display questions
def display(ql, total_q):
    questions_displayed = 0

    for q_data in ql:
        if questions_displayed == total_q:
            break

        question = q_data[1:q_data.index("@A")]
        correct_answer = q_data[q_data.index("@A") + 1]
        choices = q_data[q_data.index("@A") + 2:q_data.index("@E")]

        full = "\n".join(question)
        print("\n" + bcolors.BOLD + full + bcolors.END + "\n")
        for i in range(0, len(choices)):
            print(f"{i + 1}. {choices[i]}")

        questions_displayed += 1

        yield choices, correct_answer


# Function to handle quiz time
def timer(duration, total_q, input_event, start_time):
    global questions_answered

    while True:
        elapsed_time = time.time() - start_time

        if duration and float(elapsed_time) >= float(duration) or input_event.is_set():
            print(bcolors.BOLD + "\n\nTIMES UP!" + bcolors.END)
            input_event.set()
            end_time = time.time()
            end(total_q, start_time)
            return

        elif questions_answered >= total_q:
            input_event.set()
            return

        time.sleep(1)


# Function to handle user's answer input
def answer(choices, input_event, timeout):
    global questions_answered

    input_thread = threading.Thread(target=lambda: setattr(
        input_event, 'result', input("\nSelect your answer (integer): ")))
    input_thread.start()
    input_thread.join(timeout=float(timeout) if timeout else None)  # Ensure timeout is a float or None

    if input_thread.is_alive():
        input_event.set()
        os._exit(0)

    try:
        user_input = int(input_event.result)
        if 1 <= user_input <= len(choices):
            questions_answered += 1
            return user_input
        else:
            print("Invalid input")
            return answer(choices, input_event, timeout)
    except ValueError:
        print("Invalid input.")
        return answer(choices, input_event, timeout)


# Function to evaluate user's answer
def evaluate(user_input, correct_answer):
    global correct, incorrect

    if user_input == int(correct_answer):
        correct += 1
        print(bcolors.GREEN + "CORRECT" + bcolors.END)
    else:
        incorrect += 1
        print(bcolors.RED + "INCORRECT" + bcolors.END)

    return correct, incorrect


# Function to handle end of quiz
def end(total_q, start_time):
    global correct, incorrect

    print("\nEnd of quiz!")
    print(bcolors.UNDERLINE + f"\nAsked a total of {correct + incorrect} out of {total_q} question(s)")
    print(f"The number of correct answers: {correct}")

    percent = (correct / total_q) * 100
    print(f"Percentage: {percent}%")

    elapsed_time = time.time() - start_time
    print(f"Elapsed Time: {elapsed_time:.2f} seconds" + bcolors.END)

    log_result(total_q, correct, percent, elapsed_time)

    # Reset quiz variables for repeated runs
    correct = 0
    incorrect = 0

    return  # Return to main menu instead of exiting


# Function to log quiz results
def log_result(total_q, correct_answers, percentage, elapsed_time):
    user = get_user_id()
    result = {
        "Total Questions": total_q,
        "Correct Answers": correct_answers,
        "Percentage": percentage,
        "Elapsed Time": elapsed_time
    }

    log_path = os.path.join(log_dir, log_file)

    try:
        with open(log_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append({user: result})

    with open(log_path, 'w') as f:
        json.dump(data, f, indent=4)


# Function to get user's ID
def get_user_id():
    return get_username()


# Function to get current user's Windows ID
def get_username():
    return getpass.getuser()


# Function to handle user's answer input
def get_user_input(choices, input_event, timeout):
    user_input = answer(choices, input_event, timeout)
    if user_input is not None:
        return user_input
    else:
        os._exit(0)

# Function to load user's records from log file
def load_user_records():
    log_path = os.path.join(log_dir, log_file)

    if not os.path.exists(log_path):
        return "No log records found."

    try:
        with open(log_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "Error loading log records."

    return data


# Function to create log directory if it doesn't exist
def create_log_directory():
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


# Function to run the quiz
def quiz():
    global question_file, stored_options
    total_q = stored_options.get('total_questions', None)
    duration = stored_options.get('time_limit', None)

    if not total_q:
        print("Please set the total number of questions before running the quiz.")
        return
    elif not question_file:
        print("Please select a question file first.")
        return

    load_questions(question_file)

    start_time = time.time()
    input_event = threading.Event()

    if duration is not None:
        timer_thread = threading.Thread(target=timer, args=(duration, total_q, input_event, start_time))
        timer_thread.start()

    current_display = display(question_list, total_q)

    try:
        for choices, correct_answer in current_display:
            answer_thread = threading.Thread(target=get_user_input, args=(choices, input_event, duration))
            answer_thread.start()
            answer_thread.join()
            evaluate(int(input_event.result), correct_answer)

            if input_event.is_set():  # Check if the user has requested to exit
                break  # Exit the loop if the user wants to exit mid-test

            if questions_answered >= total_q:
                input_event.set()  # Set the event to indicate all questions are answered
                break  # Exit the loop if all questions have been answered

    except KeyboardInterrupt:
        print("\nQuiz interrupted. Returning to main menu.")

    if duration is not None:
        end_time = time.time()
        timer_thread.join()

    if not input_event.is_set():  # Check if the quiz ended due to all questions answered or time up
        end(total_q, start_time)


# Function to display main menu and handle user's choices
def main_menu():
    global stored_options
    while True:
        print("\n===== Main Menu =====")
        print("1. Set Options")
        print("2. Run Quiz")
        print("3. Display Scores")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            set_options()
        elif choice == '2':
            if not question_file:
                print("Please select a question file first.")
            else:
                if 'total_questions' in stored_options and 'time_limit' in stored_options:
                    quiz()
                else:
                    print("Please set options before running the quiz.")
        elif choice == '3':
            print(display_scores())
        elif choice == '4':
            print("Exiting program")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter a number from 1 to 4.")


# Function to handle selecting quiz file and setting options
def set_options():
    global stored_options, question_file, question_list, questions_answered
    stored_options = {}  # Reset stored options
    total_questions = input("Enter the total number of questions: ")
    if total_questions:
        stored_options['total_questions'] = int(total_questions)

    time_limit = input("Enter the time limit for the quiz in seconds: ")
    if time_limit:
        stored_options['time_limit'] = int(time_limit)

    if question_file:
        print("Using previously selected quiz file:", question_file)
    else:
        select_quiz_file()

    # Reset questions_answered variable
    questions_answered = 0

    # Reload question list based on the new total_questions
    if question_file and 'total_questions' in stored_options:
        question_list = load_questions(question_file)[:stored_options['total_questions']]

    print("Options have been set successfully.")


# Function to display user's scores
def display_scores():
    records = load_user_records()
    if isinstance(records, list):
        for record in records:
            for user, result in record.items():
                print(f"User: {user}")
                for key, value in result.items():
                    print(f"{key}: {value}")
                print()
    else:
        print(records)


# Function to select quiz file
def select_quiz_file():
    global question_file
    question_file = input("Enter the path of the quiz file: ")
    if not os.path.isfile(question_file):
        print("Invalid file path. Please enter a valid file path.")
        question_file = ""
    else:
        print("Quiz file selected successfully.")


# Main function
def main():
    create_log_directory()
    main_menu()


if __name__ == "__main__":
    main()