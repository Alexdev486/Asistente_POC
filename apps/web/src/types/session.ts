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
};

