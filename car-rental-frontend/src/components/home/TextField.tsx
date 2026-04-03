import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface TextFieldProps {
  id: string;
  label: string;
  type: string;
  placeholder: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  autoComplete?: string;
}

export function TextField({ id, label, ...props }: TextFieldProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} required {...props} />
    </div>
  );
}
