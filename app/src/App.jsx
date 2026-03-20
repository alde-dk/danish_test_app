import { useState, useEffect, useCallback } from 'react'
import { ProgressStats } from './components/ProgressStats'
import { QuestionCard } from './components/QuestionCard'
import { useDailyProgress } from './hooks/useDailyProgress'
import quizData from '../data/output.json'
import generatedQuizData from '../data/output_generated_questions.json'
import './index.css'

function App() {
  const { stats, recordAnswer } = useDailyProgress();
  
  // Combine questions inside component
  const allQuestions = [
    ...(quizData?.questions || []),
    ...(generatedQuizData?.questions || [])
  ];

  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);

  const pickRandomQuestion = useCallback(() => {
    if (allQuestions.length === 0) return;
    const randomIndex = Math.floor(Math.random() * allQuestions.length);
    setCurrentQuestion(allQuestions[randomIndex]);
    setSelectedOption(null);
  }, [allQuestions]);

  // initial load
  useEffect(() => {
    if (allQuestions.length > 0 && !currentQuestion) {
      pickRandomQuestion();
    }
  }, [allQuestions, currentQuestion, pickRandomQuestion]);

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
        {allQuestions.length === 0 ? (
          <div style={{ textAlign: 'center', marginTop: '2rem', color: 'red' }}>
            <h2>No questions loaded.</h2>
            <p>Source 1: {quizData?.questions?.length || 0} questions</p>
            <p>Source 2: {generatedQuizData?.questions?.length || 0} questions</p>
          </div>
        ) : (
          <QuestionCard 
            question={currentQuestion}
            selectedOption={selectedOption}
            onOptionClick={handleOptionClick}
          />
        )}

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
