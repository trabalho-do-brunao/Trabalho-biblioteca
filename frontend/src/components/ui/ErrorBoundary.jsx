import { Component } from 'react'

import Button from './Button'
import Feedback from './Feedback'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, info) {
    if (import.meta.env.DEV) {
      console.error('Erro inesperado de interface:', error, info)
    }
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="ui-error-boundary">
          <Feedback type="error">
            Ocorreu um erro inesperado ao exibir esta tela. Nenhum detalhe interno foi mostrado por segurança.
          </Feedback>
          <Button type="button" onClick={this.handleReload}>
            Recarregar aplicação
          </Button>
        </main>
      )
    }

    return this.props.children
  }
}
