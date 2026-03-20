export function ProgressStats({ stats }) {
  return (
    <div className="stats-container">
      <div>Score: {stats.correct} / {stats.total}</div>
    </div>
  );
}
