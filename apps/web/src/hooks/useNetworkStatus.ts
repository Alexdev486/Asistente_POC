"use client";

import { useCallback, useEffect, useState } from "react";

type NetworkStatus = {
  online: boolean;
  wasOffline: boolean;
};

/**
 * Tracks navigator.onLine status and provides a flag for showing
 * a reconnection banner after coming back online.
 */
export function useNetworkStatus(): NetworkStatus {
  const [online, setOnline] = useState(
    typeof navigator !== "undefined" ? navigator.onLine : true,
  );
  const [wasOffline, setWasOffline] = useState(false);

  const handleOnline = useCallback(() => {
    setOnline(true);
    setWasOffline(true);
    // Reset the "was offline" flag after 3 seconds
    setTimeout(() => setWasOffline(false), 3000);
  }, []);

  const handleOffline = useCallback(() => {
    setOnline(false);
  }, []);

  useEffect(() => {
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [handleOnline, handleOffline]);

  return { online, wasOffline };
}
