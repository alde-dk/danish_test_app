export function QuestionCard({ question, selectedOption, onOptionClick }) {
  if (!question) return null;

  return (
    <div className="question-card">
      <div style={{ color: 'var(--text-light)', fontSize: '0.85rem', marginBottom: '0.5rem', fontWeight: 600 }}>
        Exam: {question.file_name} — Spørgsmål {question.question_number}
      </div>
      <h2 className="question-text">
        {question.question}
      </h2>
      <div className="options-list">
        {(question.options || []).map((opt) => {
          const isSelected = selectedOption === opt.option_letter;
          const isCorrectAnswer = opt.option_letter === question.answer_letter;
          
          let btnClass = "option-btn";
          if (selectedOption) {
            if (isSelected) {
              btnClass += isCorrectAnswer ? " correct" : " wrong";
            } else if (isCorrectAnswer) {
              btnClass += " correct-dimmed";
            }
          }

          return (
            <button 
              key={opt.option_letter}
              className={btnClass}
              onClick={() => onOptionClick(opt.option_letter)}
              disabled={!!selectedOption}
            >
              <span className="option-letter">{opt.option_letter}:</span> 
              <span className="option-text">{opt.option_text}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
