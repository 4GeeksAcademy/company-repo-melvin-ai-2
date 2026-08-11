interface MetricCardProps {
  label: string;
  value: string;
  detail: string;
  tone?: "default" | "positive" | "warning";
}

export function MetricCard({
  label,
  value,
  detail,
  tone = "default",
}: MetricCardProps) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <div className="metric-heading">
        <span>{label}</span>
        <span className="metric-dot" aria-hidden="true" />
      </div>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  );
}
