'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export function SyncButton() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSync = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/transactions/sync', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        alert(`Synced successfully! Inserted ${data.inserted} new transactions.`);
        router.refresh();
      } else {
        alert('Failed to sync.');
      }
    } catch (e) {
      console.error(e);
      alert('An error occurred during sync.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button 
      onClick={handleSync} 
      disabled={loading}
      className="bg-black text-white px-4 py-2 rounded-md disabled:opacity-50"
    >
      {loading ? 'Syncing...' : 'Sync Gmail'}
    </button>
  );
}