import { ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AuthSubmitButtonProps {
  label: string;
  isLoading: boolean;
  disabled?: boolean;
}

export function AuthSubmitButton({ label, isLoading, disabled }: AuthSubmitButtonProps) {
  return (
    <Button
      type="submit"
      disabled={disabled ?? isLoading}
      aria-busy={isLoading}
      className="w-full h-11"
    >
      {isLoading ? (
        <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
      ) : (
        <>
          {label}
          <ArrowRight className="w-4 h-4" />
        </>
      )}
    </Button>
  );
}
