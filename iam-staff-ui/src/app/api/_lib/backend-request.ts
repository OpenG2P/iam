import "server-only";
import { randomUUID } from "crypto";
import { BackendRequest, RequestBody, RequestHeader } from "./backend-types";
import { getBackendConfig } from "./backend-config";

export function generateRequestId(): string {
  return randomUUID();
}

export function generateTimestamp(): string {
  return new Date().toISOString();
}

export function createBackendRequest(
  payload: RequestBody,
  origin: string,
): BackendRequest {
  const { applicationMnemonic } = getBackendConfig();

  const requestHeader: RequestHeader = {
    sender_app_mnemonic: applicationMnemonic,
    sender_app_url: origin,
    request_id: generateRequestId(),
    request_timestamp: generateTimestamp(),
  };

  return {
    request_header: requestHeader,
    request_body: payload,
  };
}
