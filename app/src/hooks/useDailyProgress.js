import { useState } from 'react';

export function useDailyProgress() {
  const [stats, setStats] = useState({
    correct: 0,
    total: 0
  });

  const recordAnswer = (isCorrect) => {
    setStats(prev => ({
      ...prev,
      total: prev.total + 1,
      correct: prev.correct + (isCorrect ? 1 : 0)
    }));
  };

  return { stats, recordAnswer };
}
