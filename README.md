This project is an interactive quiz program designed to read questions and answers from a sequential text file, present them to the user, and provide feedback on the user's answers. The program features a random question selection mechanism, a time limit option, and result logging. It supports both Windows and Linux environments.

</br >
</br >

Features
- Question Reading: Reads a set of questions and answers from a sequential text file
- Random Question Selection: Randomly selects questions for the quiz to ensure varied sessions
- Answer Feedback: Provides immediate feedback on whether the user's answer is correct or incorrect
- Time Limit: Allows the user to specify a time limit for the quiz session. If the limit is exceeded, the quiz will terminate and display the results
- Logging: Maintains a log file recording the results of each quiz session, with access control to ensure user privacy

</br >
</br >

Environment Compatibility
- Windows: Interactive menu-based interface.
- Linux: Command-line interface with hidden log file.

</br >
</br >

Instructions
</br >
Linux
</br >
To run the quiz, type in:
python3 "asg3linux.py" "quiz.txt" --total-questions ... --time-limit ...

if you want to change the quiz file, upload it to the directory and replace "quiz.txt" with the new file.

To view the log files, type in:
python3 "asg3linux.py" "quiz.txt" --display-logs

</br >
Windows
</br >  
When you run the program, you will see a menu with four different options. 

Type in 1 to set up the options for the quiz. You need to type in how many questions there will be on the quiz, the time limit, and then input the quiz file. No quotations are needed for the file.

Type in 2 to start the quiz. When answering the question, type in the number for your answer, you will automatically get a response whether this is the correct answer or not. The quiz will end once all the questions have been answered. You will be sent back to the menu*** after each attempt, where you have the choice to retake (2) or to change the quiz options (1).

Type 3 to see previous quiz logs.

Type 4 to end the program.

***The timer for the windows version does not work, it ends the program instead of going back to the menu.
