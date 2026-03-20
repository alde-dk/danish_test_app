import { useState, useEffect, useCallback } from 'react'
import { ProgressStats } from './components/ProgressStats'
import { QuestionCard } from './components/QuestionCard'
import { useDailyProgress } from './hooks/useDailyProgress'
import quizData from '../data/output.json'
import './index.css'

function App() {
  const { stats, recordAnswer } = useDailyProgress();
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);

  const pickRandomQuestion = useCallback(() => {
    const questions = quizData.questions;
    const randomIndex = Math.floor(Math.random() * questions.length);
    setCurrentQuestion(questions[randomIndex]);
    setSelectedOption(null);
  }, []);

  // initial load
  useEffect(() => {
    pickRandomQuestion();
  }, [pickRandomQuestion]);

  const handleOptionClick = (letter) => {
    if (selectedOption) return; // prevent double clicks
    
    setSelectedOption(letter);
    const isCorrect = letter === currentQuestion.answer_letter;
    recordAnswer(isCorrect);
  };

  const isCorrect = selectedOption === currentQuestion?.answer_letter;

  return (
    <div className="app-container">
      <header className="header">
        <h1>Indfødsretsprøven</h1>
        <ProgressStats stats={stats} />
      </header>
      
      <main>
        <QuestionCard 
          question={currentQuestion}
          selectedOption={selectedOption}
          onOptionClick={handleOptionClick}
        />

        {selectedOption && (
          <div className="next-container">
            <div className={`status-message ${isCorrect ? 'correct' : 'wrong'}`}>
              {isCorrect ? 'Rigtigt! (Correct!)' : 'Forkert! (Wrong)'}
            </div>
            <button className="next-btn" onClick={pickRandomQuestion}>
              Næste Spørgsmål
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
