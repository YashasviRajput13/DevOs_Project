/**
 * api.ts — Centralized API client
 * All backend requests go through here. Never exposes secrets.
 * Backend URL is read from NEXT_PUBLIC_API_URL env var only.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "APIError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("devos_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { ...headers, ...options.headers },
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const json = await res.json();
      detail = json.detail ?? JSON.stringify(json);
    } catch {}
    throw new APIError(res.status, detail);
  }

  return res.json() as Promise<T>;
}

// ── Types ───────────────────────────────────────────────────────────────────

export interface Repository {
  id: number;
  name: string;
  full_name: string;
  url: string;
  provider: string;
  default_branch: string;
  last_indexed_commit: string | null;
  files_count: number;
  indexed: boolean;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  repositories: Repository[];
  role?: string; // OWNER | MEMBER | VIEWER — present when returned by membership endpoints
}

export interface FileEntry {
  id: number;
  path: string;
  name: string;
  language: string | null;
  extension: string | null;
  size: number | null;
}

export interface FileContent extends FileEntry {
  content: string;
}

export interface OverviewData {
  repository: { id: number; name: string; full_name: string; url: string; default_branch: string };
  statistics: { files: number; chunks: number };
  languages: { name: string; files: number }[];
  directories: { path: string; file_count: number }[];
  important_files: { path: string; name: string; language: string | null }[];
  frameworks: string[];
  summary_context: string;
}

export interface ArchitectureData {
  repository: { id: number; name: string; full_name: string; url: string };
  components: { file_path: string; file_id: number; name: string; start_line: number; end_line: number; bases: string[]; methods: string[] }[];
  files: { id: number; path: string; language: string | null; classes: string[]; routes: number; import_count: number }[];
  dependencies: { source_file: string; target_file: string | null; target_module: string | null; dependency_type: string; symbol_name: string | null; line_number: number | null }[];
  api_routes: { file_path: string; file_id: number; method: string; path: string; handler: string; line: number }[];
  models: { file_path: string; file_id: number; name: string }[];
  services: { file_path: string; file_id: number; name: string; start_line: number; end_line: number }[];
}

export interface Source {
  file_id: number | null;
  repository_name: string | null;
  repository_full_name: string | null;
  repository_url: string | null;
  file_path: string | null;
  file_name: string | null;
  language: string | null;
  start_line: number | null;
  end_line: number | null;
  score: number | null;
}

export interface ChatResponse {
  query: string;
  intent: string;
  answer: string;
  sources: Source[];
  conversation_id?: number;
}

export interface SearchResult {
  chunk_id: number;
  file_id: number;
  content: string;
  start_line: number;
  end_line: number;
  score: number;
  file_path: string | null;
  file_name: string | null;
  language: string | null;
  repository_full_name: string | null;
}

// ── Projects ────────────────────────────────────────────────────────────────

export const api = {
  health: () => request<{ status: string, groq_configured?: boolean, gemini_configured?: boolean }>("/health"),

  auth: {
    login: (username: string, password: string) => {
      // OAuth2PasswordRequestForm needs form-data 
      const fd = new URLSearchParams();
      fd.append("username", username);
      fd.append("password", password);
      return fetch(`${BASE}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body: fd
      }).then(res => {
        if (!res.ok) throw new Error("Invalid login");
        return res.json() as Promise<{access_token: string}>;
      });
    },
    register: (name: string, email: string, password: string) => 
      request<{access_token: string}>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
      }),
    me: () => request<{id: number, name: string, email: string}>("/api/auth/me"),
  },

  projects: {
    list: () => request<Project[]>("/api/projects"),
    get: (id: number) => request<Project>(`/api/projects/${id}`),
    create: (name: string, description?: string) =>
      request<Project>("/api/projects", {
        method: "POST",
        body: JSON.stringify({ name, description }),
      }),
    delete: (id: number) =>
      request<void>(`/api/projects/${id}`, {
        method: "DELETE",
      }),
    members: (id: number) => request<{ members: any[], pending_invitations: any[] }>(`/api/projects/${id}/members`),
    createInvitation: (id: number, role: string) => 
      request<{ id: number, token: string, role: string, expires_at: string }>(`/api/projects/${id}/invitations`, {
        method: "POST", body: JSON.stringify({ role })
      }),
    acceptInvitation: (token: string) => 
      request<{ status: string, project_id: number }>("/api/projects/invitations/accept", {
        method: "POST", body: JSON.stringify({ token })
      }),
  },

  repositories: {
    list: (projectId: number) =>
      request<Repository[]>(`/api/projects/${projectId}/repositories`),
    add: (projectId: number, url: string) =>
      request<Repository>(`/api/projects/${projectId}/repositories`, {
        method: "POST",
        body: JSON.stringify({ url }),
      }),
    index: (projectId: number, repositoryId: number) =>
      request<{ files_indexed: number; chunks_created: number; dependencies_extracted: number }>(
        `/api/projects/${projectId}/repositories/${repositoryId}/index`,
        { method: "POST" }
      ),
    files: (projectId: number, repositoryId: number) =>
      request<{ files: FileEntry[] }>(
        `/api/projects/${projectId}/repositories/${repositoryId}/files`
      ),
    fileContent: (projectId: number, repositoryId: number, fileId: number) =>
      request<FileContent>(
        `/api/projects/${projectId}/repositories/${repositoryId}/files/${fileId}`
      ),
    overview: (projectId: number, repositoryId: number) =>
      request<OverviewData>(
        `/api/projects/${projectId}/repositories/${repositoryId}/overview`
      ),
    architecture: (projectId: number, repositoryId: number) =>
      request<ArchitectureData>(
        `/api/projects/${projectId}/repositories/${repositoryId}/architecture`
      ),
  },

  chat: (query: string, projectId?: number, repositoryId?: number, provider?: string, conversationId?: number) =>
    request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ query, project_id: projectId, repository_id: repositoryId, provider, conversation_id: conversationId }),
    }),

  conversations: {
    list: (projectId: number) =>
      request<any[]>(`/api/chat/conversations?project_id=${projectId}`),
    get: (conversationId: number) =>
      request<any>(`/api/chat/conversations/${conversationId}`),
  },

  search: (query: string, projectId: number, limit = 8) =>
    request<{ query: string; results: SearchResult[] }>("/api/search", {
      method: "POST",
      body: JSON.stringify({ query, limit, project_id: projectId }),
    }),

  agent: {
    plan: (projectId: number, repositoryId: number, query: string) =>
      request<any>("/api/agent/plan", {
        method: "POST",
        body: JSON.stringify({ project_id: projectId, repository_id: repositoryId, query }),
      }),
    apply: (planId: string, approved: boolean) =>
      request<any>("/api/agent/apply", {
        method: "POST",
        body: JSON.stringify({ plan_id: planId, approved }),
      }),
    test: (planId: string, projectId: number, repositoryId: number, workspacePath?: string) =>
      request<any>("/api/agent/test", {
        method: "POST",
        body: JSON.stringify({ 
          plan_id: planId, 
          project_id: projectId, 
          repository_id: repositoryId,
          workspace_path: workspacePath // backend will fallback properly normally 
        }),
      }),
    pr: (planId: string) =>
      request<any>("/api/agent/pr", {
        method: "POST",
        body: JSON.stringify({ plan_id: planId }),
      }),
  }
};

export { APIError };
