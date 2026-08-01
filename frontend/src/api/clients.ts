import type { Client } from "../types/clients"

const BASE = "/api/v1/clients"

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? "Request failed")
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const clientsApi = {
  list: () => request<Client[]>(""),
  get: (id: number) => request<Client>(`/${id}`),
  create: (name: string) =>
    request<Client>("", { method: "POST", body: JSON.stringify({ name }) }),
  update: (id: number, name: string) =>
    request<Client>(`/${id}`, { method: "PATCH", body: JSON.stringify({ name }) }),
  delete: (id: number) => request<void>(`/${id}`, { method: "DELETE" }),
}
