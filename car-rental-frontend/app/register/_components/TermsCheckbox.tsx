export function TermsCheckbox() {
  return (
    <div className="flex items-start gap-2">
      <input
        type="checkbox"
        id="terms"
        className="w-4 h-4 mt-0.5 rounded border-input text-primary focus:ring-ring"
        required
      />
      <label htmlFor="terms" className="text-sm text-muted-foreground">
        I agree to the{' '}
        <button type="button" className="text-primary hover:text-primary/80 transition-colors">
          Terms of Service
        </button>{' '}
        and{' '}
        <button type="button" className="text-primary hover:text-primary/80 transition-colors">
          Privacy Policy
        </button>
      </label>
    </div>
  );
}
