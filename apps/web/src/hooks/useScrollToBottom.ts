"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Hook that tracks scroll position of a container and provides a
 * `scrollToBottom` function plus a `showScrollButton` flag.
 */
export function useScrollToBottom(deps: unknown[] = []) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [isAtBottom, setIsAtBottom] = useState(true);

  const checkScroll = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const threshold = 80;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
    setIsAtBottom(atBottom);
    setShowScrollButton(!atBottom);
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    const el = containerRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior });
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    el.addEventListener("scroll", checkScroll, { passive: true });
    return () => el.removeEventListener("scroll", checkScroll);
  }, [checkScroll]);

  // Auto-scroll when deps change if already at bottom
  useEffect(() => {
    if (isAtBottom) {
      scrollToBottom("smooth");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { containerRef, showScrollButton, scrollToBottom, isAtBottom };
}
