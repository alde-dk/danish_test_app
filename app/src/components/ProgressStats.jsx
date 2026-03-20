export function ProgressStats({ stats }) {
  if (!stats) return null;
  return (
    <div className="stats-container">
      <div>Score: {stats.correct || 0} / {stats.total || 0}</div>
    </div>
  );
}
