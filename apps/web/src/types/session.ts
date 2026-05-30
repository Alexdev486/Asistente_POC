export type SessionState = {
  vin: string | null;
  model: string | null;
  current_symptom: string | null;
  current_node: string | null;
  photo_url?: string | null;
};

export type StartSessionResponse = {
  session_id: string;
  message: string;
};

export type SessionMessageResponse = {
  session_id: string;
  message: string;
  state: SessionState | null;
  diagnostic_output?: DiagnosticOutput | null;
  quick_replies?: string[] | null;
};

export type SessionDetailResponse = {
  session_id: string;
  status: string;
  entry_point: string | null;
  steps: number;
  state: SessionState | null;
  state_json: Record<string, unknown>;
};

export type MessageItem = {
  message_id: number;
  role: string;
  content: string;
  created_at: string | null;
};

export type MessagesListResponse = {
  session_id: string;
  messages: MessageItem[];
};

export type DiagnosticOutput = {
  primary_hypothesis: string;
  alternatives: string[];
  next_check: string;
  short_explanation: string;
  confidence: number;
};
