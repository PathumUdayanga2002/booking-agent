const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000/api";

const AGENT_API_BASE_URL =
  process.env.NEXT_PUBLIC_AGENT_API_BASE_URL || "http://localhost:8000/api";

function normalizeAgentWsUrl(url: string): string {
  // Backward compatibility: accept "/chat/ws" and normalize to "/api/chat/ws"
  if (url.endsWith("/chat/ws") && !url.endsWith("/api/chat/ws")) {
    return url.replace(/\/chat\/ws$/, "/api/chat/ws");
  }
  return url;
}

export const AGENT_WS_URL = normalizeAgentWsUrl(
  process.env.NEXT_PUBLIC_AGENT_WS_URL || "ws://localhost:8000/api/chat/ws"
);

function handleUnauthorizedResponse() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem("hotel_booking_auth");

  const protectedPaths = ["/admin", "/my-bookings", "/chat", "/admin/knowledge"];
  const currentPath = window.location.pathname;
  if (protectedPaths.some((path) => currentPath === path || currentPath.startsWith(`${path}/`))) {
    window.location.href = "/login";
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const method = options.method || "GET";

  console.log(`[API] ${method} ${path}`);

  let response;
  try {
    response = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
      cache: "no-store",
    });
  } catch (networkError) {
    const message = networkError instanceof Error ? networkError.message : "Network error";
    console.error(`[API ERROR] Network failure on ${method} ${path}:`, message);
    throw new Error(`Network error: Could not reach the server. Check your connection and try again.`);
  }

  let payload;
  try {
    payload = await response.json();
  } catch (parseError) {
    // If JSON parsing fails, create a generic error response
    console.error(`[API ERROR] Failed to parse response from ${method} ${path}:`, parseError);
    
    if (response.status === 429) {
      throw new Error("Too many requests. Please wait a moment and try again.");
    }
    
    throw new Error(
      `Server error: Invalid response format from server. Please try again.`
    );
  }

  if (!response.ok) {
    let errorMessage =
      payload?.message ||
      `HTTP ${response.status}: ${response.statusText}`;

    if (response.status === 401) {
      handleUnauthorizedResponse();
    }

    // Handle rate limiting specifically
    if (response.status === 429) {
      errorMessage = "Too many requests. Please wait a moment and try again.";
    }

    console.error(`[API ERROR] ${method} ${path} failed:`, {
      status: response.status,
      message: errorMessage,
      payload,
    });

    throw new Error(errorMessage);
  }

  console.log(`[API SUCCESS] ${method} ${path}`);
  return payload as T;
}

// Document APIs
export async function uploadDocument(file: File, token: string) {
  const formData = new FormData();
  formData.append("file", file);

  const url = `${AGENT_API_BASE_URL}/admin/documents/upload`;
  console.log(`[API] POST /admin/documents/upload`);
  console.log(`[API] File: ${file.name}, Token: ${token.substring(0, 20)}...`);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
      cache: "no-store",
    });

    const payload = await response.json();

    if (!response.ok) {
      const errorMsg = payload.detail || payload.message || `Upload failed: ${response.status}`;
      console.error(`[API ERROR] Upload failed with status ${response.status}:`, errorMsg);
      console.error(`[API DEBUG] Full response:`, payload);
      throw new Error(errorMsg);
    }

    console.log(`[API SUCCESS] Document uploaded`);
    return payload;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Upload failed";
    console.error(`[API ERROR] Document upload failed:`, message);
    throw error;
  }
}

export async function listDocuments(token: string) {
  const url = `${AGENT_API_BASE_URL}/admin/documents/list`;
  console.log(`[API] GET /admin/documents/list`);
  console.log(`[API] Token: ${token.substring(0, 20)}...`);

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    const payload = await response.json();

    if (!response.ok) {
      const errorMsg = payload.detail || payload.message || `Fetch failed: ${response.status}`;
      console.error(`[API ERROR] List failed with status ${response.status}:`, errorMsg);
      console.error(`[API DEBUG] Full response:`, payload);
      console.error(`[API DEBUG] Full payload details:`, JSON.stringify(payload, null, 2));
      throw new Error(errorMsg);
    }

    console.log(`[API SUCCESS] Documents fetched`);
    return payload;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Fetch failed";
    console.error(`[API ERROR] Document list failed:`, message);
    throw error;
  }
}

export async function deleteDocument(docId: string, token: string) {
  const url = `${AGENT_API_BASE_URL}/admin/documents/${docId}`;
  console.log(`[API] DELETE /admin/documents/${docId}`);

  try {
    const response = await fetch(url, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.message || `Delete failed: ${response.status}`);
    }

    console.log(`[API SUCCESS] Document deleted`);
    return { success: true };
  } catch (error) {
    const message = error instanceof Error ? error.message : "Delete failed";
    console.error(`[API ERROR] Document deletion failed:`, message);
    throw error;
  }
}

export { API_BASE_URL };
