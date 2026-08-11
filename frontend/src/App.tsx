import { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import type { Conversation, ChatMessage, ConfidenceScore, RequirementLock, EvidenceEntry, PipelineEvent } from './services/api'

const MOCK_CONVERSATIONS: Conversation[] = []

const PIPELINE_NODES = [
  'Prompt Firewall',
  'Intent Firewall',
  'Task Planner',
  'Requirement Lock',
  'Knowledge Boundary',
  'Qwen Generator',
  'Critic Agent',
  'Finalized',
]

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [conversations, setConversations] = useState<Conversation[]>(MOCK_CONVERSATIONS)
  const [activeConversation, setActiveConversation] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [activeNode, setActiveNode] = useState<string | null>(null)
  const [completedNodes, setCompletedNodes] = useState<string[]>([])
  const [currentResponseMode, setCurrentResponseMode] = useState<string>('verified')
  const [confidence, setConfidence] = useState<ConfidenceScore | null>(null)
  const [requirementLock, setRequirementLock] = useState<RequirementLock | null>(null)
  const [evidence, setEvidence] = useState<EvidenceEntry[]>([])

  const handleNewChat = useCallback(() => {
    const newConv: Conversation = {
      id: Date.now().toString(),
      title: 'New Chat',
      is_archived: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    setConversations(prev => [newConv, ...prev])
    setActiveConversation(newConv.id)
    setMessages([])
    setConfidence(null)
    setRequirementLock(null)
    setEvidence([])
    setCompletedNodes([])
    setActiveNode(null)
  }, [])

  const handleSelectConversation = useCallback((id: string) => {
    setActiveConversation(id)
    setMessages([])
    setConfidence(null)
    setRequirementLock(null)
    setEvidence([])
    setCompletedNodes([])
    setActiveNode(null)
  }, [])

  const handleDeleteConversation = useCallback((id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id))
    if (activeConversation === id) {
      setActiveConversation(null)
      setMessages([])
    }
  }, [activeConversation])

  const handleRenameConversation = useCallback((id: string, newTitle: string) => {
    setConversations(prev =>
      prev.map(c => c.id === id ? { ...c, title: newTitle } : c)
    )
  }, [])



  const handleSendMessage = useCallback(async (message: string) => {
    if (!message.trim() || isProcessing) return

    if (!activeConversation) {
      const newConv: Conversation = {
        id: Date.now().toString(),
        title: message.slice(0, 60),
        is_archived: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      setConversations(prev => [newConv, ...prev])
      setActiveConversation(newConv.id)
    }

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, conversation_id: activeConversation }),
      })

      if (!res.ok) {
        console.error('API Error:', await res.text())
        setIsProcessing(false)
        return
      }
      
      const data = await res.json()
      const userMsg: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: message,
        created_at: new Date().toISOString(),
      }
      const aiMsg: ChatMessage = {
        id: data.message_id,
        role: 'assistant',
        content: data.content,
        response_mode: data.response_mode,
        created_at: new Date().toISOString(),
        confidence: data.confidence,
        evidence: data.evidence,
      }
      setMessages(prev => [...prev, userMsg, aiMsg])
      if (data.response_mode !== 'simple') {
          if (data.confidence) setConfidence(data.confidence)
          if (data.evidence) setEvidence(data.evidence)
          if (data.requirement_lock) setRequirementLock(data.requirement_lock)
      }
      
      setIsProcessing(false)
    } catch (error) {
      console.error('Fetch error:', error)
      setIsProcessing(false)
    }
  }, [activeConversation, isProcessing])

  return (
    <div className="app-layout">
      <Sidebar
        isOpen={sidebarOpen}
        conversations={conversations}
        activeId={activeConversation}
        onNewChat={handleNewChat}
        onSelect={handleSelectConversation}
        onDelete={handleDeleteConversation}
        onRename={handleRenameConversation}
      />
      <ChatArea
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        messages={messages}
        isProcessing={isProcessing}
        activeNode={activeNode}
        completedNodes={completedNodes}
        pipelineNodes={currentResponseMode === 'simple' ? [] : PIPELINE_NODES}
        confidence={confidence}
        requirementLock={requirementLock}
        evidence={evidence}
        onSendMessage={handleSendMessage}
        activeConversation={activeConversation}
      />
    </div>
  )
}



export default App
