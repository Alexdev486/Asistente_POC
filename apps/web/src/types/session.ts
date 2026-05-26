export type SessionState = {
  vin: string | null;
  model: string | null;
  current_symptom: string | null;
  current_node: string | null;
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
};

export type SessionDetailResponse = {
  session_id: string;
  status: string;
  entry_point: string | null;
  steps: number;
  state: SessionState | null;
  state_json: Record<string, unknown>;
};

export type DiagnosticOutput = {
  primary_hypothesis: string;
  alternatives: string[];
  next_check: string;
  short_explanation: string;
  confidence: number;
};
