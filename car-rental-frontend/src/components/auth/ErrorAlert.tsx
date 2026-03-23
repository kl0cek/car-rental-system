interface ErrorAlertProps {
  message: string | null;
}

export function ErrorAlert({ message }: ErrorAlertProps) {
  if (!message) return null;

  return (
    <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm" role="alert">
      {message}
    </div>
  );
}
