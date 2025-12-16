import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import type { ErrorInfo, ReactNode } from 'react';
import { Component } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  public override state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public override componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false });
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  public override render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className='min-h-screen bg-gray-50 flex items-center justify-center p-4'>
          <div className='max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center'>
            <div className='flex justify-center mb-4'>
              <div className='p-3 bg-red-100 rounded-full'>
                <AlertTriangle className='h-8 w-8 text-red-600' />
              </div>
            </div>

            <h1 className='text-xl font-semibold text-gray-900 mb-2'>
              Something went wrong
            </h1>

            <p className='text-gray-600 mb-6'>
              We encountered an unexpected error. This has been reported to our
              team.
            </p>

            {/* Development mode: Show error details */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className='bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6 text-left'>
                <h3 className='text-sm font-medium text-gray-900 mb-2'>
                  Error Details:
                </h3>
                <p className='text-xs text-red-600 font-mono break-all'>
                  {this.state.error.message}
                </p>
                {this.state.errorInfo && (
                  <details className='mt-2'>
                    <summary className='text-xs text-gray-600 cursor-pointer hover:text-gray-900'>
                      Stack Trace
                    </summary>
                    <pre className='text-xs text-gray-600 mt-2 whitespace-pre-wrap overflow-auto max-h-32'>
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            <div className='flex gap-3 justify-center'>
              <button
                onClick={this.handleRetry}
                className='flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors'
              >
                <RefreshCw size={16} />
                Try Again
              </button>

              <button
                onClick={this.handleGoHome}
                className='flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors'
              >
                <Home size={16} />
                Go Home
              </button>
            </div>

            <p className='text-xs text-gray-500 mt-4'>
              If this problem persists, please contact our support team.
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook version for functional components
export function withErrorBoundary<T extends object>(
  Component: React.ComponentType<T>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WrappedComponent = (props: T) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}
