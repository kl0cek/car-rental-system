'use client';

import { useState } from 'react';
import { Loader2, Pencil, Plus, Trash2, X, NotebookText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/formatters';
import { useCustomerNoteMutations } from '@/hooks/useCustomerDetail';
import type { CustomerNote } from '@/types/customer';
import { useTranslation } from '@/i18n/useTranslation';

interface CustomerNotesPanelProps {
  customerId: string;
  notes: CustomerNote[];
  /** Used to gate edit / delete to the original author. */
  currentUserId: string;
  onChanged: () => void;
}

export function CustomerNotesPanel({
  customerId,
  notes,
  currentUserId,
  onChanged,
}: CustomerNotesPanelProps) {
  const { t } = useTranslation();
  const { createNote, updateNote, deleteNote, isLoading } =
    useCustomerNoteMutations(customerId);
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState('');
  const [editing, setEditing] = useState<string | null>(null);
  const [editingDraft, setEditingDraft] = useState('');

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim()) return;
    try {
      await createNote(draft.trim());
      setDraft('');
      setAdding(false);
      onChanged();
    } catch (err) {
      console.error('Create note failed', err);
    }
  }

  async function handleSaveEdit(noteId: string) {
    const text = editingDraft.trim();
    if (!text) return;
    try {
      await updateNote(noteId, text);
      setEditing(null);
      setEditingDraft('');
      onChanged();
    } catch (err) {
      console.error('Update note failed', err);
    }
  }

  async function handleDelete(noteId: string) {
    try {
      await deleteNote(noteId);
      onChanged();
    } catch (err) {
      console.error('Delete note failed', err);
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3 flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base flex items-center gap-2">
          <NotebookText className="w-4 h-4" />
          {t('customerDetail.notes')}
        </CardTitle>
        {!adding && (
          <Button size="sm" variant="outline" onClick={() => setAdding(true)}>
            <Plus className="w-3.5 h-3.5 mr-1" />
            {t('customerDetail.addNote')}
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {adding && (
          <form
            onSubmit={handleCreate}
            className="rounded-lg border border-border p-3 space-y-2 bg-muted/30"
          >
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              required
              maxLength={2000}
              rows={3}
              placeholder={t('customerDetail.notePlaceholder')}
              className="w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm focus-visible:ring-3 focus-visible:ring-ring/50 outline-none resize-none"
            />
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => {
                  setAdding(false);
                  setDraft('');
                }}
              >
                <X className="w-3.5 h-3.5 mr-1" />
                {t('common.cancel')}
              </Button>
              <Button type="submit" size="sm" disabled={isLoading || !draft.trim()}>
                {isLoading && <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />}
                {t('common.save')}
              </Button>
            </div>
          </form>
        )}

        {notes.length === 0 ? (
          <p className="text-sm text-muted-foreground py-6 text-center">
            {t('customerDetail.noNotes')}
          </p>
        ) : (
          <ul className="space-y-2">
            {notes.map((note) => {
              const canManage = note.author.id === currentUserId;
              const isEditing = editing === note.id;
              return (
                <li key={note.id} className="rounded-lg border border-border p-3 space-y-1.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="text-xs text-muted-foreground">
                      {note.author.firstName} {note.author.lastName} · {formatDate(note.createdAt)}
                      {note.updatedAt !== note.createdAt && (
                        <span className="ml-1">({t('customerDetail.edited')})</span>
                      )}
                    </div>
                    {canManage && !isEditing && (
                      <div className="flex gap-1">
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => {
                            setEditing(note.id);
                            setEditingDraft(note.body);
                          }}
                          aria-label={t('common.edit')}
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => handleDelete(note.id)}
                          aria-label={t('common.delete')}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    )}
                  </div>
                  {isEditing ? (
                    <div className="space-y-2">
                      <textarea
                        value={editingDraft}
                        onChange={(e) => setEditingDraft(e.target.value)}
                        required
                        maxLength={2000}
                        rows={3}
                        className="w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm focus-visible:ring-3 focus-visible:ring-ring/50 outline-none resize-none"
                      />
                      <div className="flex justify-end gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setEditing(null);
                            setEditingDraft('');
                          }}
                        >
                          {t('common.cancel')}
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          onClick={() => handleSaveEdit(note.id)}
                          disabled={isLoading || !editingDraft.trim()}
                        >
                          {t('common.save')}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm whitespace-pre-wrap">{note.body}</p>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
