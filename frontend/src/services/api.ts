const API_BASE = '/api';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  response_mode?: 'simple' | 'verified' | 'research' | 'document';
  confidence?: ConfidenceScore;
  evidence?: EvidenceEntry[];
}

export interface ConfidenceScore {
  evidence_support: number;
  requirement_match: number;
  hallucination_risk: number;
  approved: boolean;
}

export interface EvidenceEntry {
  claim: string;
  source?: string;
  page?: number;
  section?: string;
  confidence: number;
}

export interface RequirementLock {
  allowed_topics: string[];
  forbidden_topics: string[];
  assumptions_allowed: string[];
  assumptions_forbidden: string[];
  confidence: number;
}

export interface Conversation {
  id: string;
  title: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface PipelineEvent {
  event: string;
  data: {
    node?: string;
    status?: string;
    progress?: number;
    intent?: any;
    plan?: any;
    lock?: RequirementLock;
    approved?: boolean;
    confidence?: ConfidenceScore;
    response?: string;
    response_mode?: 'simple' | 'verified' | 'research' | 'document';
    evidence_ledger?: EvidenceEntry[];
    reason?: string;
  };
}

export async function sendMessage(
  message: string,
  conversationId?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.statusText}`);
  return res.json();
}

export async function streamMessage(
  message: string,
  conversationId: string | undefined,
  onEvent: (event: PipelineEvent) => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });

  if (!res.ok) throw new Error(`Stream failed: ${res.statusText}`);

  const reader = res.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) return;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event = JSON.parse(line.slice(6));
          onEvent(event);
        } catch {
          // skip malformed events
        }
      }
    }
  }
}

export async function getConversations(): Promise<Conversation[]> {
  const res = await fetch(`${API_BASE}/history/conversations`);
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return res.json();
}

export async function getMessages(conversationId: string): Promise<ChatMessage[]> {
  const res = await fetch(`${API_BASE}/history/conversations/${conversationId}/messages`);
  if (!res.ok) throw new Error('Failed to fetch messages');
  return res.json();
}

export async function updateConversation(
  conversationId: string,
  data: { title?: string; is_archived?: boolean }
): Promise<Conversation> {
  const res = await fetch(`${API_BASE}/history/conversations/${conversationId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update conversation');
  return res.json();
}

export async function deleteConversation(conversationId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/history/conversations/${conversationId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete conversation');
}

export async function uploadFile(
  file: File,
  conversationId?: string
): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  if (conversationId) {
    formData.append('conversation_id', conversationId);
  }

  const res = await fetch(`${API_BASE}/files/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('File upload failed');
  return res.json();
}
