import type { LucideIcon } from 'lucide-react';
import Link from 'next/link';

interface StatusMessageProps {
  icon: LucideIcon;
  iconClassName: string;
  bgClassName: string;
  title: string;
  description: string;
  link: {
    href: string;
    label: string;
    icon?: LucideIcon;
  };
}

export function StatusMessage({
  icon: Icon,
  iconClassName,
  bgClassName,
  title,
  description,
  link,
}: StatusMessageProps) {
  const LinkIcon = link.icon;

  return (
    <div className="text-center space-y-4">
      <div
        className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto ${bgClassName}`}
      >
        <Icon className={`w-8 h-8 ${iconClassName}`} />
      </div>
      <h2 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h2>
      <p className="text-muted-foreground">{description}</p>
      <Link
        href={link.href}
        className="inline-flex items-center gap-2 text-sm text-primary font-medium hover:text-primary/80 transition-colors"
      >
        {LinkIcon && <LinkIcon className="w-4 h-4" />}
        {link.label}
      </Link>
    </div>
  );
}
