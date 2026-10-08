import { useState } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000/chat'

const EXAMPLE_QUESTIONS = [
  'Which hubs in the Midwest are most exposed to winter disruption?',
  'Compare Miami and Houston in terms of hurricane and flood exposure.',
  'What percentage of days in Denver last year had snowfall?',
  "Why is the Dallas hub's weather disruption risk high?",
]

// The whole chat page: message list, example questions and the input box.
function App() {
  // Each message is one of:
  //   { role: 'user', text }
  //   { role: 'agent', answer, key_numbers, caveat }
  //   { role: 'error', text }
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)

  // Sends one question to the backend and adds the reply (or an error) to the chat.
  async function sendMessage(text) {
    setMessages((previous) => [...previous, { role: 'user', text }])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      })
      if (!response.ok) {
        throw new Error(`Something went wrong (error ${response.status}). Please try again.`)
      }
      const data = await response.json()
      setSessionId(data.session_id)
      setMessages((previous) => [...previous, { role: 'agent', ...data }])
    } catch (error) {
      // fetch itself fails with a TypeError when the server cannot be reached.
      const text = error instanceof TypeError
        ? 'Could not reach the server. Is the backend running?'
        : error.message
      setMessages((previous) => [...previous, { role: 'error', text }])
    }

    setLoading(false)
  }

  // Runs when the form is submitted (Send button or Enter key).
  function handleSubmit(event) {
    event.preventDefault() // stop the browser from reloading the page
    const text = input.trim()
    if (text) {
      sendMessage(text)
    }
  }

  // Clears the chat and forgets the session, so the next question starts fresh.
  function startNewChat() {
    setMessages([])
    setSessionId(null)
  }

  return (
    <div className="page">
      <header className="header">
        <h1>Weather Risk Agent</h1>
        <button onClick={startNewChat} disabled={loading}>New chat</button>
      </header>

      <main className="messages">
        {messages.length === 0 && (
          <div className="examples">
            <p>Try one of these questions:</p>
            {EXAMPLE_QUESTIONS.map((question) => (
              <button key={question} onClick={() => sendMessage(question)} disabled={loading}>
                {question}
              </button>
            ))}
          </div>
        )}

        {messages.map((message, index) => (
          <Message key={index} message={message} />
        ))}

        {loading && <p className="thinking">Thinking...</p>}
      </main>

      <form className="input-row" onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about weather risk at the hubs..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>Send</button>
      </form>
    </div>
  )
}

// Shows one message: a user question, an agent reply, or an error.
function Message({ message }) {
  if (message.role === 'user') {
    return <div className="message user">{message.text}</div>
  }

  if (message.role === 'error') {
    return <div className="message error">{message.text}</div>
  }

  return (
    <div className="message agent">
      <p>{message.answer}</p>

      {message.key_numbers.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Hub</th>
              <th>Label</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {message.key_numbers.map((number, index) => (
              <tr key={index}>
                <td>{number.hub_id}</td>
                <td>{number.label}</td>
                <td>{number.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {message.caveat && <p className="caveat">{message.caveat}</p>}
    </div>
  )
}

export default App
