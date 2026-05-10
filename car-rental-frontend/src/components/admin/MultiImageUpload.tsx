'use client';

import { useEffect, useRef, useState } from 'react';
import { ImagePlus, Star, StarOff, Trash2, X } from 'lucide-react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { useTranslation } from '@/i18n/useTranslation';

const MAX_FILE_BYTES = 5 * 1024 * 1024;
const ACCEPTED_MIME = ['image/jpeg', 'image/png', 'image/webp'];

export interface PendingImage {
  /** Stable identifier for React keys + reorder; not sent to API. */
  uid: string;
  file: File;
  previewUrl: string;
}

interface MultiImageUploadProps {
  /** Files queued for upload (used in create mode, before the vehicle exists). */
  pending: PendingImage[];
  onChange: (next: PendingImage[]) => void;
  /** Index of the primary image inside ``pending``. -1 when no choice yet. */
  primaryIndex: number;
  onPrimaryChange: (index: number) => void;
  /** Override the helper hint text; useful when extending behaviour. */
  hint?: string;
}

function makeUid(): string {
  return Math.random().toString(36).slice(2);
}

/**
 * Pure client-side queue of file uploads with previews, validation,
 * delete and "set as primary" buttons. The parent owns persistence —
 * this component never talks to the network itself.
 */
export function MultiImageUpload({
  pending,
  onChange,
  primaryIndex,
  onPrimaryChange,
  hint,
}: MultiImageUploadProps) {
  const { t } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);

  // Object URLs leak memory if you don't revoke them when the component
  // unmounts or the file is removed. Track them per-image and revoke once.
  useEffect(() => {
    return () => {
      for (const img of pending) URL.revokeObjectURL(img.previewUrl);
    };
    // pending array identity changes with every onChange — only run once on unmount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setError(null);

    const accepted: PendingImage[] = [];
    for (const file of Array.from(files)) {
      if (!ACCEPTED_MIME.includes(file.type)) {
        setError(t('multiImage.invalidType'));
        continue;
      }
      if (file.size > MAX_FILE_BYTES) {
        setError(t('multiImage.tooLarge'));
        continue;
      }
      accepted.push({
        uid: makeUid(),
        file,
        previewUrl: URL.createObjectURL(file),
      });
    }
    if (accepted.length === 0) return;

    const next = [...pending, ...accepted];
    onChange(next);
    // Auto-promote the first uploaded file to primary when none is selected
    if (primaryIndex === -1) onPrimaryChange(pending.length);
  };

  const removeAt = (index: number) => {
    const removed = pending[index];
    URL.revokeObjectURL(removed.previewUrl);
    const next = pending.filter((_, i) => i !== index);
    onChange(next);

    // Re-anchor primaryIndex so it keeps pointing at the right file.
    if (index === primaryIndex) {
      onPrimaryChange(next.length === 0 ? -1 : 0);
    } else if (index < primaryIndex) {
      onPrimaryChange(primaryIndex - 1);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">{t('multiImage.title')}</p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => inputRef.current?.click()}
        >
          <ImagePlus className="w-4 h-4 mr-2" />
          {t('multiImage.add')}
        </Button>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_MIME.join(',')}
          className="hidden"
          onChange={(e) => {
            handleFiles(e.target.files);
            e.target.value = '';
          }}
        />
      </div>

      <p className="text-xs text-muted-foreground">{hint ?? t('multiImage.hint')}</p>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {pending.length === 0 ? (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="w-full border-2 border-dashed border-border rounded-xl py-10 flex flex-col items-center justify-center gap-2 hover:bg-secondary/50 transition-colors"
        >
          <ImagePlus className="w-8 h-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">{t('multiImage.empty')}</p>
        </button>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {pending.map((img, i) => (
            <div
              key={img.uid}
              className="relative group rounded-lg overflow-hidden border border-border aspect-video bg-muted"
            >
              <Image src={img.previewUrl} alt="" fill className="object-cover" />
              {i === primaryIndex && (
                <span className="absolute top-1.5 left-1.5 inline-flex items-center gap-1 bg-primary text-primary-foreground text-[10px] uppercase tracking-wider rounded px-1.5 py-0.5">
                  <Star className="w-2.5 h-2.5" />
                  {t('multiImage.primary')}
                </span>
              )}
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                <Button
                  type="button"
                  size="icon"
                  variant="secondary"
                  onClick={() => onPrimaryChange(i)}
                  aria-label={t('multiImage.setPrimary')}
                >
                  {i === primaryIndex ? (
                    <StarOff className="w-3.5 h-3.5" />
                  ) : (
                    <Star className="w-3.5 h-3.5" />
                  )}
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="destructive"
                  onClick={() => removeAt(i)}
                  aria-label={t('common.delete')}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              </div>
              <button
                type="button"
                onClick={() => removeAt(i)}
                className="sm:hidden absolute top-1 right-1 bg-background/80 rounded-full p-1"
                aria-label={t('common.delete')}
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
