
const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

type ApiOptions = {
    method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    body?: unknown;
    token?: string;
};

export async function apiRequest<T = unknown>(
    path: string,
    options: ApiOptions = {},
): Promise<T> {
    const headers = new Headers({
        Accept: "application/json",
    });

    if (options.body !== undefined) {
        headers.set("Content-Type", "application/json");
    }

    if (options.token) {
        headers.set("Authorization", `Bearer ${options.token}`);
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
        method: options.method ?? "GET",
        headers,
        body:
            options.body !== undefined
                ? JSON.stringify(options.body)
                : undefined,
    });

    const contentType = response.headers.get("content-type") ?? "";
    const data = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        const detail =
            typeof data === "object" && data !== null && "detail" in data
                ? String(data.detail)
                : typeof data === "string" && data
                    ? data
                    : `Request failed with status ${response.status}`;

        throw new Error(detail);
    }

    return data as T;
}

export const api = {
    get: <T = unknown>(path: string, token?: string) =>
        apiRequest<T>(path, { method: "GET", token }),

    post: <T = unknown>(path: string, body?: unknown, token?: string) =>
        apiRequest<T>(path, { method: "POST", body, token }),
};
