import type { OperationAcceptedResponse } from "../../types/admin";

/** Shared shape passed to card components for action buttons */
export interface ActionState {
  isRunning: boolean;
  lastResult: OperationAcceptedResponse | null;
  lastError: string | null;
  trigger: () => void;
}
