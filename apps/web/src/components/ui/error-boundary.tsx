"use client";

import React, { Component, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  label?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * React error boundary that catches unhandled rendering errors within a
 * subtree and shows a localized error card instead of crashing the whole
 * console.  Per-section use prevents a failure in one panel from taking
 * down unrelated panels.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error(
      `[ErrorBoundary${this.props.label ? ` — ${this.props.label}` : ""}]`,
      error,
      info.componentStack,
    );
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="rounded-xl border border-red-200 bg-red-50 p-5">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 text-red-500 text-lg">⚠</span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-red-700">
                {this.props.label ? `${this.props.label} — ` : ""}
                Something went wrong
              </p>
              <p className="mt-1 text-xs text-red-600 break-all">
                {this.state.error?.message ?? "An unexpected rendering error occurred."}
              </p>
              <button
                onClick={this.handleReset}
                className="mt-3 rounded-md bg-red-100 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-200 transition-colors"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
