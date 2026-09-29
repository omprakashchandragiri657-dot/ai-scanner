import type { Expense, Group, User } from "./types";

const BASE = "/api";

class ApiClient {
  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
    if (!response.ok) {
      const payload = (await response.json().catch(() => ({}))) as {
        error?: string;
      };
      throw new Error(payload.error || `Request failed (${response.status})`);
    }
    return (await response.json()) as T;
  }

  users(): Promise<User[]> {
    return this.request<{ users: User[] }>("/users").then((d) => d.users);
  }

  expenses(groupId: number): Promise<Expense[]> {
    return this.request<{ expenses: Expense[] }>(
      `/expenses?group_id=${groupId}`,
    ).then((d) => d.expenses);
  }

  groups(): Promise<Group[]> {
    return this.request<{ groups: Group[] }>("/groups").then((d) => d.groups);
  }
}

export const client = new ApiClient();
