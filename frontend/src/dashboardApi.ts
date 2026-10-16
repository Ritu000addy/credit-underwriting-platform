
import { api } from "./api";

export type StatusCounts = {
    total: number;
    by_status: Record<string, number>;
};

export type OperationsDashboard = {
    generated_at: string;
    applications: StatusCounts;
    underwriting: StatusCounts;
    manual_review: StatusCounts;
    exceptions: StatusCounts;
    disbursements: StatusCounts;
    collections: {
        overdue_schedule_count: number;
        overdue_application_count: number;
        overdue_outstanding_amount: string;
    };
    reconciliation: StatusCounts;
    operations_queue: StatusCounts;
};

type ApiResponse<T> = {
    success: boolean;
    message: string;
    data: T | null;
    error: unknown;
    meta: unknown;
};

export async function getOperationsDashboard(): Promise<OperationsDashboard> {
    const response = await api.get<ApiResponse<OperationsDashboard>>(
        "/operations/dashboard",
    );

    if (!response.success || response.data === null) {
        throw new Error(response.message || "Unable to load operations dashboard");
    }

    return response.data;
}



export type ManualReview = {
    review_id: string;
    application_id: string;
    review_status: string;
    review_reason: string;
    reviewer_id: string | null;
    reviewer_decision: string | null;
    reviewer_remarks: string | null;
    checker_id: string | null;
    checker_decision: string | null;
    checker_remarks: string | null;
    maker_checker_required: boolean;
    created_at: string;
    updated_at: string;
};

export async function getManualReviews(): Promise<ManualReview[]> {
    const response = await api.get<ApiResponse<ManualReview[]>>(
        "/operations/manual-review",
    );

    if (!response.success || response.data === null) {
        throw new Error(response.message || "Unable to load manual reviews");
    }

    return response.data;
}
