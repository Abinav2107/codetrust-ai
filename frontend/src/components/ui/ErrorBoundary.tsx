import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Icon } from './Icon';
import { Button } from './Button';

type Props = { children: ReactNode };
type State = { hasError: boolean; message?: string };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: unknown): State {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : 'An unexpected error occurred.',
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('DebugAgent UI error:', error, info.componentStack);
  }

  reset = () => this.setState({ hasError: false, message: undefined });

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <main className="error-screen">
        <div className="error-card card">
          <div className="error-icon"><Icon name="alert" size={22} /></div>
          <p className="eyebrow">UI ERROR</p>
          <h1>DebugAgent hit an unexpected error.</h1>
          <p className="error-copy">The app is still running, but this screen could not be rendered.</p>
          <details>
            <summary>Show technical details</summary>
            <code>{this.state.message}</code>
          </details>
          <div className="detail-actions">
            <Button onClick={this.reset} icon="refresh">Try again</Button>
            <Button variant="secondary" onClick={() => window.location.reload()}>Reload page</Button>
          </div>
        </div>
      </main>
    );
  }
}
