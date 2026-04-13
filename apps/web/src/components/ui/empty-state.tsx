interface EmptyStateProps {
  icon?: string;
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({ icon = "📭", title, description, action }: EmptyStateProps) {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "48px 24px",
      textAlign: "center",
    }}>
      <div style={{ fontSize: "48px", marginBottom: "16px" }}>{icon}</div>
      <h3 style={{ fontSize: "18px", fontWeight: 600, color: "var(--color-text)", marginBottom: "8px" }}>
        {title}
      </h3>
      <p style={{ fontSize: "14px", color: "var(--color-text-secondary)", maxWidth: "320px", marginBottom: "24px" }}>
        {description}
      </p>
      {action && (
        <button className="btn-primary" onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  );
}
