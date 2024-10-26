from app import main as generate_pdfs
from pathlib import Path

class QuizApp:
    def __init__(self):
        self.mcqs = [
            {
                "question": "What is the primary goal of a scheduling system in an operating system?",
                "options": ["To minimize CPU utilization", "To make full use of CPU cycles during I/O wait times",
                            "To increase I/O wait times", "To reduce the time needed for context switching"],
                "answer": "To make full use of CPU cycles during I/O wait times"
            },
            {
                "question": "What does a typical CPU-I/O burst cycle involve?",
                "options": ["Alternating between CPU execution and memory storage", 
                            "Alternating between CPU calculations and I/O wait times",
                            "Continuous CPU calculations only", "Continuous I/O wait times only"],
                "answer": "Alternating between CPU calculations and I/O wait times"
            },
            {
                "question": "Where are all processes stored upon entering the system?",
                "options": ["Ready Queue", "Job Queue", "Waiting Queue", "Device Queue"],
                "answer": "Job Queue"
            },
            {
                "question": "What is the main function of the long-term scheduler?",
                "options": ["To manage the job queue by loading processes into memory for execution",
                            "To handle device requests in the waiting queue", "To control I/O processes only", 
                            "To schedule jobs directly to the CPU"],
                "answer": "To manage the job queue by loading processes into memory for execution"
            }
        ]
        self.score = 0

    def start_quiz(self):
        print("\nWelcome to the Process Scheduling Quiz!")
        print("Answer the following questions by typing the option number (1-4).")

        # Iterate over each question
        for i, mcq in enumerate(self.mcqs):
            print(f"\nQ{i+1}: {mcq['question']}")
            for j, option in enumerate(mcq['options'], 1):
                print(f"  {j}. {option}")
            
            # Collect user's answer
            while True:
                try:
                    user_choice = int(input("Your answer (1-4): ").strip())
                    if 1 <= user_choice <= 4:
                        selected_option = mcq['options'][user_choice - 1]
                        # Check if the answer is correct
                        if selected_option == mcq['answer']:
                            self.score += 1
                        break
                    else:
                        print("Invalid choice, please select a number between 1 and 4.")
                except ValueError:
                    print("Invalid input, please enter a number.")

        return self.get_level()

    def get_level(self):
        total_questions = len(self.mcqs)
        percentage = (self.score / total_questions) * 100
        print(f"\nYour Score: {self.score} out of {total_questions} ({percentage:.2f}%)")

        # Determine explanation level based on score
        if percentage < 40:
            level = "beginner"
        elif 40 <= percentage < 70:
            level = "intermediate"
        else:
            level = "advanced"

        print(f"\nBased on your score, you'll receive a {level}-level explanation.")
        return level

def orchestrate_learning():
    # First, run the quiz
    quiz = QuizApp()
    appropriate_level = quiz.start_quiz()
    
    # Generate all PDFs using the original app
    pdf_path = Path(r"C:\Users\ajogd\OneDrive\Desktop\New folder (3)\U2-OS - Process Scheduling Concepts.pdf")
    if not pdf_path.exists():
        print("PDF file not found. Please check the path.")
        return
        
    print("\nGenerating your personalized explanation...")
    generate_pdfs(str(pdf_path))
    
    # Direct user to their appropriate level PDF
    level_pdf = f"{appropriate_level}_guide.pdf"
    print(f"\nBased on your quiz performance, please read: {level_pdf}")
    print("This explanation has been tailored to your current understanding of the topic.")

if __name__ == "__main__":
    orchestrate_learning()