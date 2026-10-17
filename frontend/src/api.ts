
const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

type ApiOptions = {
    method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    body?: unknown;
    token?: string;
    form?: URLSearchParams;
};

export class ApiError extends Error {
    status: number;
    detail: unknown;

    constructor(message: string, status: number, detail?: unknown) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.detail = detail;
    }
}


export async function apiRequest<T = unknown>(
    path: string,
    options: ApiOptions = {},
): Promise<T> {
    const headers = new Headers({
        Accept: "application/json",
    });

    let body: BodyInit | undefined;

    if (options.form !== undefined) {
        headers.set(
            "Content-Type",
            "application/x-www-form-urlencoded");

        body = options.form;
    } else if (options.body !== undefined) {
        headers.set("Content-Type", "application/json");
        body = JSON.stringify(options.body);
    }

    if (options.token) {
        headers.set("Authorization", `Bearer ${options.token}`);
    }

    let response: Response;

    try {
        response = await fetch(`${API_BASE_URL}${path}`, {
            method: options.method ?? "GET",
            headers,
            body,
        });
    } catch {
        throw new ApiError(
            "Unable to connect to the API. Check the backend URL and network connection.",
            0,
        );
    }

    const contentType = response.headers.get("content-type") ?? "";
    let data: unknown = null;

    try {
        if (contentType.includes("application/json")) {
            const text = await response.text();
            data = text ? JSON.parse(text) : null;
        } else {
            data = await response.text();
        }
    } catch {
        data = null;
    }

    if (!response.ok) {
        const detail =
            typeof data === "object" && data !== null && "detail" in data
                ? data.detail
                : typeof data === "object" && data !== null && "message" in data
                    ? data.message
                    : typeof data === "string" && data
                        ? data
                        : `Request failed with status ${response.status}`;

        throw new ApiError(
            String(detail),
            response.status,
            detail,
        );
    }

    return data as T;
}

export const api = {
    get: <T = unknown>(path: string, token?: string) =>
        apiRequest<T>(path, { method: "GET", token }),

    post: <T = unknown>(path: string, body?: unknown, token?: string) =>
        apiRequest<T>(path, { method: "POST", body, token }),

    postForm: <T = unknown>(path: string, form: URLSearchParams) =>
        apiRequest<T>(path, { method: "POST", form }),
};
