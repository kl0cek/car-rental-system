import { ArrowRight } from 'lucide-react';

export function SubmitButton({ isLoading, disabled }: { isLoading: boolean; disabled: boolean }) {
  return (
    <button
      type="submit"
      disabled={disabled}
      aria-busy={isLoading}
      className="w-full h-11 bg-primary text-primary-foreground rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
    >
      {isLoading ? (
        <div
          className="w-5 h-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin"
          aria-label="Loading"
        />
      ) : (
        <>
          Create account
          <ArrowRight className="w-4 h-4" aria-hidden="true" />
        </>
      )}
    </button>
  );
}
