"use client";

import { Component } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/Button";

type ErrorBoundaryProps = {
  children: React.ReactNode;
  fallback?: React.ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
  error: Error | null;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("[ErrorBoundary]", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex min-h-[200px] flex-col items-center justify-center gap-4 rounded-2xl border border-red-900 bg-red-950/30 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-500/10">
            <AlertTriangle size={24} className="text-red-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-red-300">Algo salió mal</p>
            <p className="mt-1 max-w-md text-xs text-red-400/70">
              {this.state.error?.message ?? "Error inesperado en la interfaz."}
            </p>
          </div>
          <Button variant="danger" size="sm" onClick={this.handleRetry}>
            <RefreshCw size={14} />
            Reintentar
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Wraps an async function in a safe try/catch and provides error state.
 * Usage: const { execute, isLoading, error } = useAsyncHandler(fn);
 */
export function useAsyncHandler<T extends (...args: never[]) => Promise<unknown>>(
  fn: T,
  onError?: (err: Error) => void,
) {
  const state = { isLoading: false, error: null as Error | null };

  async function execute(...args: Parameters<T>): Promise<Awaited<ReturnType<T>> | null> {
    state.isLoading = true;
    state.error = null;
    try {
      const result = await fn(...args);
      return result as Awaited<ReturnType<T>>;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      state.error = error;
      onError?.(error);
      return null;
    } finally {
      state.isLoading = false;
    }
  }

  return { execute, get isLoading() { return state.isLoading; }, get error() { return state.error; } };
}
