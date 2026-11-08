import { Component } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Button } from './ui.jsx'

export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidUpdate(prevProps) {
    if (this.state.error && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null })
    }
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div className="empty">
        <AlertTriangle size={28} aria-hidden="true" />
        <h3>Bir şeyler ters gitti</h3>
        <p>Bu sayfa yüklenirken bir hata oluştu. Tekrar dener misin?</p>
        <Button onClick={() => this.setState({ error: null })}>Tekrar dene</Button>
      </div>
    )
  }
}
