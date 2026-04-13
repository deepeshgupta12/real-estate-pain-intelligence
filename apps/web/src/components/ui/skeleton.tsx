export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{
        background: "linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%)",
        backgroundSize: "200% 100%",
        animation: "shimmer 1.5s infinite",
        borderRadius: "6px",
      }}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="card" style={{ padding: "20px" }}>
      <Skeleton style={{ height: "20px", width: "60%", marginBottom: "12px" }} />
      <Skeleton style={{ height: "14px", width: "90%", marginBottom: "8px" }} />
      <Skeleton style={{ height: "14px", width: "70%", marginBottom: "8px" }} />
      <Skeleton style={{ height: "14px", width: "80%" }} />
    </div>
  );
}
