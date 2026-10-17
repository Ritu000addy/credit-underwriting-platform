
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

export async function getOperationsDashboard(
    token: string,
): Promise<OperationsDashboard> {
    const response = await api.get<ApiResponse<OperationsDashboard>>(
        "/operations/dashboard",
        token,
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

export async function getManualReviews(
    token: string,
): Promise<ManualReview[]> {
    const response = await api.get<ApiResponse<ManualReview[]>>(
        "/operations/manual-review",
        token,
    );

    if (!response.success || response.data === null) {
        throw new Error(response.message || "Unable to load manual reviews");
    }

    return response.data;
}


export type UnderwritingResult = {
    decision_id: string;
    application_id: string;
    credit_score: number | null;
    risk_grade: string | null;
    probability_of_default: number | null;
    affordability_score: number | null;
    repayment_propensity: number | null;
    fraud_score: number | null;
    income_stability_score: number | null;
    risk_segment: string | null;
    recommended_amount: number | null;
    recommended_tenure: number | null;
    recommended_emi: number | null;
    foir: number | null;
    decision: string;
    confidence: number | null;
    reason_codes: string[];
    model_version: string | null;
    policy_version: string | null;
    created_at: string;
};


export async function getUnderwritingResult(
    applicationId: string,
    token: string,
): Promise<UnderwritingResult> {
    const response = await api.get<ApiResponse<UnderwritingResult>>(
        `/underwriting/${applicationId}`,
        token,
    );

    if (!response.success || response.data == null) {
        throw new Error(
            response.message || 'Unable to load the underwriting result',
        );
    }

    return response.data;
}


export async function startManualReview(
    applicationId: string,
    reviewerId: string,
    token: string,
) {
    return api.post(
        `/manual-review/${applicationId}/start`,
        { reviewer_id: reviewerId },
        token,
    );
}

export async function submitManualReviewRecommendation(
    applicationId: string,
    reviewerId: string,
    reviewerDecision: 'APPROVE' | 'REJECT',
    reviewerRemarks: string,
    token: string,
) {
    return api.post(
        `/manual-review/${applicationId}/recommendation`,
        {
            reviewer_id: reviewerId,
            reviewer_decision: reviewerDecision,
            reviewer_remarks: reviewerRemarks || null,
        },
        token,
    );
}

export async function submitManualReviewCheckerDecision(
    applicationId: string,
    checkerId: string,
    checkerDecision: 'APPROVE' | 'REJECT',
    checkerRemarks: string,
    token: string,
) {
    return api.post(
        `/manual-review/${applicationId}/checker-decision`,
        {
            checker_id: checkerId,
            checker_decision: checkerDecision,
            checker_remarks: checkerRemarks || null,
        },
        token,
    );
}



export type AuthUser = {
    user_id: string;
    username: string;
    email: string | null;
    full_name: string | null;
    role: string;
    is_active: boolean;
    last_login_at: string | null;
};

export type AuthToken = {
    access_token: string;
    token_type: string;
};

type LoginResponse = {
    success: boolean;
    message: string;
    data: AuthToken | null;
    error: unknown;
    meta: unknown;
};

type CurrentUserResponse = {
    success: boolean;
    message: string;
    data: AuthUser | null;
    error: unknown;
    meta: unknown;
};

export async function login(
    username: string,
    password: string,
): Promise<AuthToken> {
    const form = new URLSearchParams();
    form.set("username", username);
    form.set("password", password);

    const response = await api.postForm<LoginResponse>(
        "/auth/login",
        form,
    );

    if (!response.success || response.data === null) {
        throw new Error(response.message || "Login failed");
    }

    return response.data;
}

export async function getCurrentUser(
    token: string,
): Promise<AuthUser> {
    const response = await api.get<CurrentUserResponse>(
        "/auth/me",
        token,
    );

    if (!response.success || response.data === null) {
        throw new Error(
            response.message || "Unable to load current user",
        );
    }

    return response.data;
}
