class QuizScorer:

    def extract_correct_answer(self, text):

        for line in text.split("\n"):
            if "Answer:" in line:
                return line.split(":")[-1].strip().upper()

        return None

    def parse_quiz(self, quiz_text):

        questions = []
        current = []

        for line in quiz_text.split("\n"):

            if line.strip().startswith("Question"):
                if current:
                    questions.append("\n".join(current))
                    current = []

            current.append(line)

        if current:
            questions.append("\n".join(current))

        parsed = []

        for i, q in enumerate(questions, 1):
            parsed.append({
                "id": i,
                "question": q
            })

        return parsed

    def evaluate(self, quiz_text, user_answers):

        quiz = self.parse_quiz(quiz_text)

        score = 0
        results = []

        for q in quiz:

            correct = self.extract_correct_answer(q["question"])
            user = user_answers.get(q["id"], "").upper()

            is_correct = user == correct

            if is_correct:
                score += 1

            results.append({
                "id": q["id"],
                "correct": correct,
                "user": user,
                "is_correct": is_correct
            })

        return {
            "score": score,
            "total": len(quiz),
            "percentage": (score / len(quiz)) * 100 if quiz else 0,
            "details": results
        }
    
def hide_answers(quiz_text):
    """
    Remove Answer lines before showing quiz to user
    """
    lines = quiz_text.split("\n")

    filtered = [
        line for line in lines
        if not line.strip().startswith("Answer:")
    ]

    return "\n".join(filtered)