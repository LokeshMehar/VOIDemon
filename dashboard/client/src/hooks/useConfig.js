import { useState, useCallback } from "react";

const API_BASE = (import.meta.env.VITE_API_BASE || "") + "/api";

/**
 * useConfig — manages config.ini fetch, local edits, and save-back.
 *
 * Fix (CodeRabbit, Minor): config starts as null; callers must guard
 * against null before calling Object.entries(config).
 */
export function useConfig() {
  const [config, setConfig]       = useState(null);
  const [loading, setLoading]     = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [saving, setSaving]       = useState(false);

  // Fetch on mount
  const fetchConfig = useCallback(async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const res = await fetch(`${API_BASE}/config`);
      const data = await res.json();

      if (!res.ok || data.error) {
        throw new Error(data.error || `Server returned ${res.status}`);
      }

      setConfig(data);
    } catch (err) {
      setFetchError(err.message);
