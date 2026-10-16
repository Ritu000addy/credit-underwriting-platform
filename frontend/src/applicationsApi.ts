
import { api } from "./api";

export type ApplicationItem = {
    application_id: string;
    customer_id: string;
    product: string;
    requested_amount: string;
    status: string;
    created_at: string;
    decision: string | null;
    risk_grade: string | null;
    manual_review_status: string | null;
    disbursement_status: string | null;
};

type ApiResponse<T> = {
    success: boolean;
    message: string;
    data: T | null;
    error: unknown;
    meta: unknown;
};

type ApplicationsData = {
    total: number;
    limit: number;
    offset: number;
    items: ApplicationItem[];
};

export async function getApplications(): Promise<ApplicationsData> {
    const response = await api.get<ApiResponse<ApplicationsData>>(
        "/operations/applications?limit=50&offset=0",
    );

    if (!response.success || response.data === null) {
        throw new Error(
            response.message || "Unable to load applications",
        );
    }

    return response.data;
}
