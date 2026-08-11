import React from 'react'
import { Plus, MessageSquare, Trash2, Edit2, Hexagon } from 'lucide-react'
import type { Conversation } from '../services/api'

interface SidebarProps {
  isOpen: boolean
  conversations: Conversation[]
  activeId: string | null
  onNewChat: () => void
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onRename: (id: string, newTitle: string) => void
}

export default function Sidebar({
  isOpen,
  conversations,
  activeId,
  onNewChat,
  onSelect,
  onDelete,
  onRename
}: SidebarProps) {
  // Group conversations by time
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  
  const groups = {
    'Today': [] as Conversation[],
    'Yesterday': [] as Conversation[],
    'Previous 7 Days': [] as Conversation[],
    'Older': [] as Conversation[]
  }

  conversations.forEach(c => {
    const d = new Date(c.updated_at || c.created_at)
    if (d.toDateString() === today.toDateString()) {
      groups['Today'].push(c)
    } else if (d.toDateString() === yesterday.toDateString()) {
      groups['Yesterday'].push(c)
    } else if (today.getTime() - d.getTime() < 7 * 24 * 60 * 60 * 1000) {
      groups['Previous 7 Days'].push(c)
    } else {
      groups['Older'].push(c)
    }
  })

  return (
    <div className={`sidebar ${!isOpen ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="logo-icon"><Hexagon size={22} fill="white" strokeWidth={1} /></div>
          <h1>VeriMind AI</h1>
        </div>
      </div>
      
      <button className="new-chat-btn" onClick={onNewChat}>
        <Plus size={18} />
        New Verification Session
      </button>

      <div className="chat-history">
        {Object.entries(groups).map(([label, items]) => {
          if (items.length === 0) return null
          
          return (
            <div key={label} className="chat-history-group">
              <div className="chat-history-label">{label}</div>
              {items.map(c => (
                <div 
                  key={c.id} 
                  className={`chat-history-item ${activeId === c.id ? 'active' : ''}`}
                  onClick={() => onSelect(c.id)}
                >
                  <MessageSquare size={16} className="item-icon" />
                  <div className="item-title">{c.title}</div>
                  <div className="item-actions">
                    <button 
                      className="item-action-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        const t = prompt('Rename conversation:', c.title)
                        if (t) onRename(c.id, t)
                      }}
                    >
                      <Edit2 size={14} />
                    </button>
                    <button 
                      className="item-action-btn danger"
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm('Delete this conversation?')) onDelete(c.id)
                      }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        })}
      </div>
    </div>
  )
}
