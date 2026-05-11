'use client';

import { useState } from 'react';
import useSWR from 'swr';
import type {
  CustomerDetail,
  CustomerDetailApi,
  CustomerNote,
  CustomerNoteApi,
  Incident,
  IncidentApi,
  IncidentSeverity,
  IncidentType,
} from '@/types/customer';
import { mapCustomerDetail, mapCustomerNote, mapIncident } from '@/types/customer';

const detailFetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((r) => {
    if (!r.ok) throw new Error(`Failed to fetch customer (${r.status})`);
    return r.json() as Promise<CustomerDetailApi>;
  });

export function useCustomerDetail(customerId: string | null | undefined) {
  const key = customerId ? `/api/admin/customers/${customerId}` : null;
  const { data, isLoading, error, mutate } = useSWR(key, detailFetcher);

  return {
    detail: data ? mapCustomerDetail(data) : null,
    isLoading,
    error: error as Error | undefined,
    refresh: mutate,
  };
}

// ---------------------------------------------------------------------------
// Mutations — incidents and notes. Each one optimistically returns the
// updated row so the page can patch its local copy without re-fetching.
// ---------------------------------------------------------------------------

export interface IncidentInput {
  rentalId: string | null;
  type: IncidentType;
  severity: IncidentSeverity;
  title: string;
  description: string;
  cost: string | null;
}

export function useCustomerIncidentMutations(customerId: string) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run<T>(fn: () => Promise<T>): Promise<T> {
    setIsLoading(true);
    setError(null);
    try {
      return await fn();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Operation failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  async function createIncident(input: IncidentInput): Promise<Incident> {
    return run(async () => {
      const res = await fetch(`/api/admin/customers/${customerId}/incidents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          rental_id: input.rentalId,
          type: input.type,
          severity: input.severity,
          title: input.title,
          description: input.description,
          cost: input.cost,
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Create incident failed (${res.status}): ${text}`);
      }
      return mapIncident((await res.json()) as IncidentApi);
    });
  }

  async function deleteIncident(incidentId: string): Promise<void> {
    return run(async () => {
      const res = await fetch(`/api/admin/customers/${customerId}/incidents/${incidentId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Delete incident failed (${res.status}): ${text}`);
      }
    });
  }

  return { createIncident, deleteIncident, isLoading, error };
}

export function useCustomerNoteMutations(customerId: string) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run<T>(fn: () => Promise<T>): Promise<T> {
    setIsLoading(true);
    setError(null);
    try {
      return await fn();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Operation failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  async function createNote(body: string): Promise<CustomerNote> {
    return run(async () => {
      const res = await fetch(`/api/admin/customers/${customerId}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ body }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Create note failed (${res.status}): ${text}`);
      }
      return mapCustomerNote((await res.json()) as CustomerNoteApi);
    });
  }

  async function updateNote(noteId: string, body: string): Promise<CustomerNote> {
    return run(async () => {
      const res = await fetch(`/api/admin/customers/${customerId}/notes/${noteId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ body }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Update note failed (${res.status}): ${text}`);
      }
      return mapCustomerNote((await res.json()) as CustomerNoteApi);
    });
  }

  async function deleteNote(noteId: string): Promise<void> {
    return run(async () => {
      const res = await fetch(`/api/admin/customers/${customerId}/notes/${noteId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Delete note failed (${res.status}): ${text}`);
      }
    });
  }

  return { createNote, updateNote, deleteNote, isLoading, error };
}

export type { CustomerDetail };
