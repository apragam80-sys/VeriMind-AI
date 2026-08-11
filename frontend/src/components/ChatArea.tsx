import React, { useState, useRef, useEffect } from 'react'
import { 
  Send, Menu, Share2, MoreVertical, FileText, CheckCircle2, ShieldAlert,
  Terminal, Server, Code, FileSearch, ShieldCheck, Link, Shield, Settings, Activity
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { ChatMessage, ConfidenceScore, RequirementLock, EvidenceEntry } from '../services/api'

interface ChatAreaProps {
  sidebarOpen: boolean
  onToggleSidebar: () => void
  messages: ChatMessage[]
  isProcessing: boolean
  activeNode: string | null
  completedNodes: string[]
  pipelineNodes: string[]
  confidence: ConfidenceScore | null
  requirementLock: RequirementLock | null
  evidence: EvidenceEntry[]
  onSendMessage: (msg: string) => void
  activeConversation: string | null
}

export default function ChatArea({
  sidebarOpen,
  onToggleSidebar,
  messages,
  isProcessing,
  activeNode,
  completedNodes,
  pipelineNodes,
  confidence,
  requirementLock,
  evidence,
  onSendMessage,
  activeConversation
}: ChatAreaProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isProcessing])

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!input.trim() || isProcessing) return
    onSendMessage(input)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="main-content">
      <div className="main-header">
        <div className="header-left">
          <button className="menu-toggle" onClick={onToggleSidebar}>
            <Menu size={20} />
          </button>
          <div className="header-title">
            {activeConversation ? 'Active Verification Session' : 'New Session'}
          </div>
        </div>
        <div className="header-right">
          <button className="menu-toggle"><Settings size={18} /></button>
          <button className="menu-toggle"><Share2 size={18} /></button>
          <button className="menu-toggle"><MoreVertical size={18} /></button>
        </div>
      </div>

      <div className="chat-area">
        <div className="chat-container">
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-logo">
                <Shield size={36} strokeWidth={2.5} />
              </div>
              <h1 className="welcome-title">VeriMind Assistant</h1>
              <p className="welcome-subtitle">
                An intent-aligned AI that strictly respects your requirements and verifies every claim it makes against an evidence ledger.
              </p>
              
              <div className="suggestion-grid">
                <div className="suggestion-card" onClick={() => onSendMessage("Create a malware analysis tool using Python")}>
                  <Terminal className="card-icon" size={20} />
                  <div className="card-title">Malware Analysis Tool</div>
                  <div className="card-desc">See the Intent Firewall block out blockchain and mobile apps.</div>
                </div>
                <div className="suggestion-card" onClick={() => onSendMessage("Summarize the methodology of this research paper")}>
                  <FileSearch className="card-icon" size={20} />
                  <div className="card-title">Research Paper Analysis</div>
                  <div className="card-desc">Watch the Evidence Ledger trace every claim back to the source.</div>
                </div>
                <div className="suggestion-card" onClick={() => onSendMessage("Build a secure REST API for a user database")}>
                  <Server className="card-icon" size={20} />
                  <div className="card-title">Secure REST API</div>
                  <div className="card-desc">Observe the Requirement Lock generate strict assumptions.</div>
                </div>
                <div className="suggestion-card" onClick={() => onSendMessage("Write a quick sorting algorithm")}>
                  <Code className="card-icon" size={20} />
                  <div className="card-title">Sorting Algorithm</div>
                  <div className="card-desc">See the Model Router bypass heavy models for a fast response.</div>
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div key={msg.id || idx} className="message">
                  <div className={`message-avatar ${msg.role}`}>
                    {msg.role === 'user' ? 'U' : <ShieldCheck size={18} />}
                  </div>
                  <div className="message-content">
                    <div className="message-role">
                      {msg.role === 'user' ? 'You' : 'VeriMind Engine'}
                    </div>
                    <div className="message-text">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                    
                    {/* Render message-specific confidence if available */}
                    {msg.confidence && (
                      <div className="confidence-panel mt-4">
                        <div className="confidence-header">
                          <div className="confidence-label">Verification Score</div>
                          <div className={`confidence-badge ${msg.confidence.approved ? 'approved' : 'rejected'}`}>
                            {msg.confidence.approved ? 'CRITIC APPROVED' : 'CRITIC REJECTED'}
                          </div>
                        </div>
                        <div className="confidence-bars">
                          <div className="confidence-bar">
                            <span className="bar-label">Evidence Support</span>
                            <div className="bar-track"><div className="bar-fill green" style={{ width: `${msg.confidence.evidence_support}%` }}></div></div>
                            <span className="bar-value">{msg.confidence.evidence_support}%</span>
                          </div>
                          <div className="confidence-bar">
                            <span className="bar-label">Requirement Match</span>
                            <div className="bar-track"><div className="bar-fill blue" style={{ width: `${msg.confidence.requirement_match}%` }}></div></div>
                            <span className="bar-value">{msg.confidence.requirement_match}%</span>
                          </div>
                          <div className="confidence-bar">
                            <span className="bar-label">Hallucination Risk</span>
                            <div className="bar-track"><div className="bar-fill red" style={{ width: `${msg.confidence.hallucination_risk}%` }}></div></div>
                            <span className="bar-value">{msg.confidence.hallucination_risk}%</span>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Render message-specific evidence if available */}
                    {msg.evidence && msg.evidence.length > 0 && (
                      <div className="evidence-panel mt-4">
                        <div className="confidence-label mb-3">Evidence Ledger</div>
                        {msg.evidence.map((ev, i) => (
                          <div key={i} className="evidence-item">
                            <Link size={14} className="text-accent flex-shrink-0 mt-1" />
                            <div className="evidence-claim">{ev.claim}</div>
                            {ev.section && <div className="evidence-source">Sec: {ev.section}</div>}
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="message-actions">
                      <button className="msg-action-btn"><Share2 size={14} /> Share</button>
                      <button className="msg-action-btn"><FileText size={14} /> Copy</button>
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Active processing state visualizations */}
              {isProcessing && (
                <div className="message">
                  <div className="message-avatar assistant">
                    <Activity size={18} className="animate-spin" />
                  </div>
                  <div className="message-content">
                    <div className="message-role">Processing Pipeline...</div>
                    
                    {pipelineNodes.length > 0 && (
                      <div className="pipeline-progress mt-2">
                        <div className="pipeline-title">Agent Orchestrator State</div>
                        <div className="pipeline-nodes">
                          {pipelineNodes.map(node => (
                            <div 
                              key={node} 
                              className={`pipeline-node ${completedNodes.includes(node) ? 'completed' : ''} ${activeNode === node ? 'active' : ''}`}
                            >
                              {completedNodes.includes(node) ? <CheckCircle2 size={12} /> : <div className="node-dot"></div>}
                              {node}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {requirementLock && pipelineNodes.length > 0 && (
                      <div className="req-lock-card">
                        <div className="req-lock-title"><ShieldAlert size={14} /> Requirement Lock Established</div>
                        <div className="flex flex-wrap gap-x-8 gap-y-4 mt-3">
                          <div className="req-lock-section">
                            <div className="req-lock-section-title">Strictly Bound Scope</div>
                            <div className="req-lock-tags">
                              {requirementLock.allowed_topics.map(t => <span key={t} className="req-tag allowed">{t}</span>)}
                            </div>
                          </div>
                          <div className="req-lock-section">
                            <div className="req-lock-section-title">Forbidden Expansions</div>
                            <div className="req-lock-tags">
                              {requirementLock.forbidden_topics.map(t => <span key={t} className="req-tag blocked">{t}</span>)}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="typing-indicator mt-4">
                      <div className="dot"></div><div className="dot"></div><div className="dot"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      <div className="input-area">
        <div className="input-container">
          <form className="input-wrapper" onSubmit={handleSubmit}>
            <div className="input-actions-left">
              <button type="button" className="input-action-btn" title="Upload Document">
                <FileText size={18} />
              </button>
            </div>
            <textarea 
              className="chat-input"
              placeholder="Ask anything... our Intent Firewall will protect the scope."
              rows={1}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isProcessing}
            />
            <button 
              type="submit" 
              className="send-btn"
              disabled={!input.trim() || isProcessing}
            >
              <Send size={16} />
            </button>
          </form>
          <div className="input-footer">
            VeriMind AI uses a multi-agent orchestrated pipeline to prevent hallucinations and scope creep.
          </div>
        </div>
      </div>
    </div>
  )
}
