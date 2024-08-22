import random
import sys
import threading
import time
import os
import json
import getpass
import argparse

question_list = []
correct = 0
incorrect = 0
questions_answered = 0
log_file = ".quizlog"
log_dir = "quiz_logs"
question_file = ""
total_questions = None
time_limit = None


class bcolors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


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


def timer(duration, total_q, input_event, start_time):
    global questions_answered

    while True:
        current_time = time.time()  # Get the current time
        elapsed_time = current_time - start_time  # Calculate the elapsed time

        if duration and float(elapsed_time) >= float(duration) or input_event.is_set():
            print(bcolors.BOLD + "\n\nTIMES UP!" + bcolors.END)
            input_event.set()
            end_time = current_time
            end(total_q, start_time, end_time)
            return

        elif questions_answered >= total_q:
            input_event.set()
            return

        time.sleep(1)


def answer(choices, input_event, timeout):
    global questions_answered

    input_thread = threading.Thread(target=lambda: setattr(
        input_event, 'result', input("\nSelect your answer (integer) or type 'exit' to quit: ")))
    input_thread.start()
    input_thread.join(timeout=float(timeout) if timeout else None)  # Ensure timeout is a float or None

    if input_thread.is_alive():
        input_event.set()
        os._exit(0)

    user_input = input_event.result.strip().lower()
    if user_input == 'exit':
        input_event.set()
        os._exit(0)

    try:
        user_input = int(user_input)
        if 1 <= user_input <= len(choices):
            questions_answered += 1
            return user_input
        else:
            print("Invalid input")
            return answer(choices, input_event, timeout)
    except ValueError:
        print("Invalid input.")
        return answer(choices, input_event, timeout)


def evaluate(user_input, correct_answer):
    global correct, incorrect

    if user_input == int(correct_answer):
        correct += 1
        print(bcolors.GREEN + "CORRECT" + bcolors.END)
    else:
        incorrect += 1
        print(bcolors.RED + "INCORRECT" + bcolors.END)

    return correct, incorrect


def end(total_q, start_time, end_time):
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
    questions_answered = 0

    return  # Return to main menu instead of exiting


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


def get_user_id():
    # Get the username
    return get_username()


def get_username():
    # Get the current system's username
    return getpass.getuser()


def get_user_input(choices, input_event, timeout):
    user_input = answer(choices, input_event, timeout)
    if user_input is not None:
        return user_input
    else:
        os._exit(0)


def load_user_records():
    log_path = os.path.join(log_dir, log_file)

    if not os.path.exists(log_path):
        return "No log records found."

    with open(log_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return "Error: Log file is corrupted."

    if not data:
        return "No records found in the log file."

    return data


def create_log_directory():
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


def quiz(file_path, total_q=None, duration=None):
    load_questions(file_path)

    if total_q == '':
        total_q = None  # Set to None if total_q is an empty string
    elif total_q is not None:
        try:
            total_q = int(total_q)  # Convert to integer if not None
        except ValueError:
            print("Error: Total number of questions must be an integer.")
            return  # Return to the main menu instead of exiting the program

    if total_q is None:
        total_q = len(question_list)
    elif total_q > len(question_list):
        print(
            f"Error: Total questions requested ({total_q}) is greater than the available questions ({len(question_list)}).")
        return  # Return to the main menu instead of exiting the program

    start_time = time.time()

    input_event = threading.Event()
    quiz_completed = False
    user_ended = False  # Flag to track if user ended the quiz early

    if duration is not None:
        timer_thread = threading.Thread(target=timer, args=(duration, total_q, input_event, start_time))
        timer_thread.start()

    current_display = display(question_list, total_q)

    try:
        for choices, correct_answer in current_display:
            answer_thread = threading.Thread(target=get_user_input, args=(choices, input_event, duration))
            answer_thread.start()
            answer_thread.join()
            user_input = input_event.result.strip().lower()
            if user_input == 'exit':
                user_ended = True
                break
            elif user_input == 'end':
                break

            evaluate(int(input_event.result), correct_answer)

            if input_event.is_set():  # Check if the user has requested to exit
                break  # Exit the loop if the user wants to exit mid-test
        else:
            quiz_completed = True
    except KeyboardInterrupt:
        print("\nQuiz interrupted.")
    finally:
        if duration is not None:
            timer_thread.join()

        end_time = time.time() if duration is not None else None
        end(total_q, start_time, end_time)

        if user_ended or user_input == 'end':
            sys.exit(0)  # Exit the program immediately if the user types "end" or "exit"


def select_quiz_file():
    global question_file
    parser = argparse.ArgumentParser(description='Quiz Program')
    parser.add_argument('file_path', type=str, help='Path to the quiz file')
    parser.add_argument('--total-questions', type=int, help='Total number of questions', default=None)
    parser.add_argument('--time-limit', type=int, help='Time limit for the quiz in seconds', default=None)
    parser.add_argument('--display-logs', action='store_true', help='Display past results from the logfile')

    args = parser.parse_args()

    question_file = args.file_path
    total_q = args.total_questions
    duration = args.time_limit

    if args.display_logs:
        records = load_user_records()
        if isinstance(records, list):
            for record in records:
                for user, result in record.items():
                    print(f"User: {user}")
                    print(f"Total Questions: {result['Total Questions']}")
                    print(f"Correct Answers: {result['Correct Answers']}")
                    print(f"Percentage: {result['Percentage']}%")
                    print(f"Elapsed Time: {result['Elapsed Time']:.2f} seconds")
                    print()
        else:
            print(records)
        sys.exit(0)

    quiz(question_file, total_q, duration)


def main():
    create_log_directory()
    select_quiz_file()


if __name__ == "__main__":
    main()
