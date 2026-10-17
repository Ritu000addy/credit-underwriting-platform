import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  Bell,
  BrainCircuit,
  Building2,
  CheckCircle2,
  ChevronDown,
  CircleDollarSign,
  ClipboardCheck,
  Clock3,
  CreditCard,
  FileSearch,
  FileText,
  LayoutDashboard,
  LifeBuoy,
  Menu,
  Plus,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Users,
  Wallet,
  X,
} from 'lucide-react'

import {
  getOperationsDashboard,
  getUnderwritingResult,
  getManualReviews,
  startManualReview,
  submitManualReviewRecommendation,
  submitManualReviewCheckerDecision,
  login,
  getCurrentUser,
  type OperationsDashboard,
  type UnderwritingResult,
  type ManualReview,
  type AuthUser,
} from './dashboardApi'

import {
  getApplications,
  type ApplicationItem,
} from './applicationsApi'

const navigation = [
  { label: 'Overview', icon: LayoutDashboard, section: 'WORKSPACE' },
  { label: 'Applications', icon: FileText },
  { label: 'Borrower', icon: Users },
  { label: 'Underwriting', icon: BrainCircuit },
  { label: 'Review queue', icon: ClipboardCheck, badge: '12' },
  { label: 'Disbursements', icon: Wallet, badge: '4' },
  { label: 'Repayments', icon: CircleDollarSign },
  { label: 'Documents', icon: FileSearch },
]

const management = [
  { label: 'Risk & policies', icon: ShieldCheck },
  { label: 'Reports & analytics', icon: Activity },
  { label: 'Audit trail', icon: ClipboardCheck },
  { label: 'Settings', icon: Settings },
]

const volume = [
  { month: 'May', value: 42 },
  { month: 'Jun', value: 57 },
  { month: 'Jul', value: 49 },
  { month: 'Aug', value: 72 },
  { month: 'Sep', value: 63 },
  { month: 'Oct', value: 86 },
]


const REASON_CODE_EXPLANATIONS: Record<string, string> = {
  BUREAU_SCORE_ACCEPTABLE:
    'Credit bureau score meets the configured assessment criteria.',
  LOW_PROBABILITY_OF_DEFAULT:
    'The model-estimated probability of default is low.',
  AFFORDABILITY_ACCEPTABLE:
    'Affordability assessment meets the configured criteria.',
  FOIR_WITHIN_LIMIT:
    'Fixed-obligation-to-income ratio is within the configured limit.',
  WEAK_REPAYMENT_HISTORY:
    'Repayment history requires further review.',
  STABLE_INCOME:
    'Income stability assessment is satisfactory.',
  POLICY_DATA_INCOMPLETE:
    'Required policy information is incomplete.',
  FRAUD_ASSESSMENT_INCOMPLETE:
    'Fraud assessment is incomplete.',
};


function App() {
  const [activePage, setActivePage] = useState('Overview')
  const [search, setSearch] = useState('')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [lastUpdated, setLastUpdated] = useState('Just now')


  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [loginUsername, setLoginUsername] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)

  const [dashboard, setDashboard] = useState<OperationsDashboard | null>(null)
  const [dashboardError, setDashboardError] = useState('')

  const [applications, setApplications] = useState<ApplicationItem[]>([])
  const [applicationsTotal, setApplicationsTotal] = useState(0)
  const [applicationsError, setApplicationsError] = useState('')

  const [applicationSearch, setApplicationSearch] = useState('')
  const [applicationStatusFilter, setApplicationStatusFilter] = useState('ALL')
  const [applicationDecisionFilter, setApplicationDecisionFilter] = useState('ALL')

  const [selectedApplication, setSelectedApplication] =
    useState<ApplicationItem | null>(null)


  const [manualReviews, setManualReviews] = useState<ManualReview[]>([])
  const [manualReviewsError, setManualReviewsError] = useState('')

  const [reviewActionError, setReviewActionError] = useState('');
  const [reviewActionMessage, setReviewActionMessage] = useState('');
  const [reviewActionLoading, setReviewActionLoading] = useState<string | null>(null);

  const [underwritingResults, setUnderwritingResults] = useState<
    Record<string, UnderwritingResult>
  >({});
  const [underwritingLoading, setUnderwritingLoading] = useState<string | null>(null);
  const [underwritingErrors, setUnderwritingErrors] = useState<Record<string, string>>({});
  const [expandedDecisionId, setExpandedDecisionId] = useState<string | null>(null);

  const [makerDecision, setMakerDecision] = useState<'APPROVE' | 'REJECT'>('APPROVE');
  const [makerRemarks, setMakerRemarks] = useState('');

  const [checkerDecision, setCheckerDecision] = useState<'APPROVE' | 'REJECT'>('APPROVE');
  const [checkerRemarks, setCheckerRemarks] = useState('');


  useEffect(() => {
    if (!accessToken) return
    let cancelled = false

    async function loadDashboard() {
      try {
        const data = await getOperationsDashboard(accessToken!)

        if (!cancelled) {
          setDashboard(data)
          setDashboardError('')
          setLastUpdated(
            new Date(data.generated_at).toLocaleTimeString(),
          )
        }
      } catch (error) {
        if (!cancelled) {
          setDashboardError(
            error instanceof Error
              ? error.message
              : 'Unable to load dashboard data',
          )
        }
      }
    }

    void loadDashboard()

    return () => {
      cancelled = true
    }
  }, [accessToken])


  useEffect(() => {
    if (!accessToken) return

    let cancelled = false

    async function loadApplications() {
      try {
        const data = await getApplications(accessToken!)

        if (!cancelled) {
          setApplications(data.items)
          setApplicationsTotal(data.total)
          setApplicationsError('')
        }
      } catch (error) {
        if (!cancelled) {
          setApplicationsError(
            error instanceof Error
              ? error.message
              : 'Unable to load applications',
          )
        }
      }
    }

    void loadApplications()

    return () => {
      cancelled = true
    }
  }, [accessToken])


  useEffect(() => {
    if (!accessToken) return

    let cancelled = false

    async function loadManualReviews() {
      try {
        const data = await getManualReviews(accessToken!)

        if (!cancelled) {
          setManualReviews(data)
          setManualReviewsError('')
        }
      } catch (error) {
        if (!cancelled) {
          setManualReviewsError(
            error instanceof Error
              ? error.message
              : 'Unable to load manual reviews',
          )
        }
      }
    }

    void loadManualReviews()

    return () => {
      cancelled = true
    }
  }, [accessToken])

  const refreshManualReviews = async () => {
    if (!accessToken) return;

    const data = await getManualReviews(accessToken);
    setManualReviews(data);
  };


  const handleLoadUnderwritingResult = async (applicationId: string) => {
    if (!accessToken) return;

    // Toggle the details panel closed if it is already open.
    if (expandedDecisionId === applicationId) {
      setExpandedDecisionId(null);
      return;
    }

    setExpandedDecisionId(applicationId);

    // Use the cached result if it has already been loaded.
    if (underwritingResults[applicationId]) return;

    setUnderwritingLoading(applicationId);
    setUnderwritingErrors((current) => {
      const next = { ...current };
      delete next[applicationId];
      return next;
    });

    try {
      const result = await getUnderwritingResult(applicationId, accessToken);

      setUnderwritingResults((current) => ({
        ...current,
        [applicationId]: result as UnderwritingResult,
      }));
    } catch (error) {
      setUnderwritingErrors((current) => ({
        ...current,
        [applicationId]:
          error instanceof Error
            ? error.message
            : 'Unable to load the underwriting result.',
      }));
    } finally {
      setUnderwritingLoading(null);
    }
  };


  const handleStartReview = async (applicationId: string) => {
    if (!accessToken || !currentUser) return;

    setReviewActionLoading(applicationId);
    setReviewActionError('');
    setReviewActionMessage('');

    try {
      await startManualReview(
        applicationId,
        currentUser.username,
        accessToken,
      );

      await refreshManualReviews();
      setReviewActionMessage(`Review started for ${applicationId}.`);
    } catch (error) {
      setReviewActionError(
        error instanceof Error ? error.message : 'Unable to start review.',
      );
    } finally {
      setReviewActionLoading(null);
    }
  };

  const handleMakerRecommendation = async (applicationId: string) => {
    if (!accessToken || !currentUser) return;

    setReviewActionLoading(applicationId);
    setReviewActionError('');
    setReviewActionMessage('');

    try {
      await submitManualReviewRecommendation(
        applicationId,
        currentUser.username,
        makerDecision,
        makerRemarks,
        accessToken,
      );

      await refreshManualReviews();
      setMakerRemarks('');
      setReviewActionMessage(`Recommendation submitted for ${applicationId}.`);
    } catch (error) {
      setReviewActionError(
        error instanceof Error
          ? error.message
          : 'Unable to submit maker recommendation.',
      );
    } finally {
      setReviewActionLoading(null);
    }
  };

  const handleCheckerDecision = async (applicationId: string) => {
    if (!accessToken || !currentUser) return;

    setReviewActionLoading(applicationId);
    setReviewActionError('');
    setReviewActionMessage('');

    try {
      await submitManualReviewCheckerDecision(
        applicationId,
        currentUser.username,
        checkerDecision,
        checkerRemarks,
        accessToken,
      );

      await refreshManualReviews();
      setCheckerRemarks('');
      setReviewActionMessage(`Checker decision submitted for ${applicationId}.`);
    } catch (error) {
      setReviewActionError(
        error instanceof Error
          ? error.message
          : 'Unable to submit checker decision.',
      );
    } finally {
      setReviewActionLoading(null);
    }
  };

  const filteredApplications = useMemo(() => {
    const query = search.trim().toLowerCase()
    if (!query) return applications
    return applications.filter((item) =>
      [
        item.application_id,
        item.customer_id,
        item.product,
        item.status,
        item.decision ?? '',
      ]
        .join(' ')
        .toLowerCase()
        .includes(query),
    )
  }, [search, applications])


  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoginError('')
    setLoginLoading(true)

    try {
      const tokenResponse = await login(loginUsername.trim(), loginPassword)
      const user = await getCurrentUser(tokenResponse.access_token)

      if (!user.is_active) {
        throw new Error('AUTH_USER_INACTIVE')
      }

      setAccessToken(tokenResponse.access_token)
      setCurrentUser(user)
      setLoginPassword('')
    } catch (error) {
      setLoginError(
        error instanceof Error ? error.message : 'Unable to sign in',
      )
    } finally {
      setLoginLoading(false)
    }
  }

  const handleLogout = () => {
    setAccessToken(null)
    setCurrentUser(null)
    setLoginUsername('')
    setLoginPassword('')
    setLoginError('')
    setActivePage('Overview')
  }


  const selectPage = (page: string) => {
    setActivePage(page)
    setMobileNavOpen(false)
  }

  const renderNavigation = (items: typeof navigation) =>
    items.map((item) => {
      const Icon = item.icon
      const active = activePage === item.label
      return (
        <button
          key={item.label}
          onClick={() => selectPage(item.label)}
          className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-[13px] transition ${active
            ? 'bg-blue-600 font-semibold text-white shadow-sm shadow-blue-950/10'
            : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
        >
          <Icon size={17} strokeWidth={1.8} />
          <span className="flex-1">{item.label}</span>
          {'badge' in item && item.badge && (
            <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${active ? 'bg-white/20 text-white' : 'bg-slate-700 text-slate-300'
              }`}>
              {item.badge}
            </span>
          )}
        </button>
      )
    })

  const pageDescriptions: Record<string, string> = {
    Applications: 'Track applications from intake through final credit decision.',
    Borrowers: 'Review borrower profiles and consolidated financial information.',
    Underwriting: 'Assess affordability, risk signals and policy compliance.',
    'Review queue': 'Manage applications awaiting an authorised credit officer.',
    Disbursements: 'Monitor sanction fulfilment and disbursement operations.',
    Repayments: 'Monitor repayment schedules, collections and reconciliation.',
    Documents: 'Review submitted documents and verification status.',
    'Risk & policies': 'Review policy controls, model governance and risk thresholds.',
    'Reports & analytics': 'Explore portfolio performance and operational trends.',
    'Audit trail': 'Trace important actions and changes across the platform.',
    Settings: 'Manage platform configuration and access controls.',
  }

  if (!accessToken || !currentUser) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f5f7fb] px-4 py-10">
        <form
          onSubmit={handleLogin}
          className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-lg"
        >
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white">
              <Building2 size={25} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">
                CredenceFlow
              </h1>
              <p className="text-sm text-slate-500">
                Lender Operations Workspace
              </p>
            </div>
          </div>

          <h2 className="text-lg font-semibold text-slate-900">
            Sign in
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Use your authorised platform account.
          </p>

          <label
            htmlFor="login-username"
            className="mt-6 block text-sm font-medium text-slate-700"
          >
            Username
          </label>
          <input
            id="login-username"
            autoComplete="username"
            value={loginUsername}
            onChange={(event) => setLoginUsername(event.target.value)}
            required
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />

          <label
            htmlFor="login-password"
            className="mt-4 block text-sm font-medium text-slate-700"
          >
            Password
          </label>
          <input
            id="login-password"
            type="password"
            autoComplete="current-password"
            value={loginPassword}
            onChange={(event) => setLoginPassword(event.target.value)}
            required
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />

          {loginError && (
            <div
              role="alert"
              className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
            >
              {loginError}
            </div>
          )}

          <button
            type="submit"
            disabled={loginLoading}
            className="mt-6 w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loginLoading ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="mt-4 text-center text-xs text-slate-400">
            Access is subject to your assigned platform permissions.
          </p>
        </form>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#f5f7fb] text-slate-800">
      {mobileNavOpen && (
        <button
          aria-label="Close navigation overlay"
          onClick={() => setMobileNavOpen(false)}
          className="fixed inset-0 z-30 bg-slate-950/50 lg:hidden"
        />
      )}

      <aside className={`fixed inset-y-0 left-0 z-40 flex w-[250px] flex-col bg-[#111c32] text-white transition-transform duration-200 ${mobileNavOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}>
        <div className="flex h-[76px] items-center gap-3 border-b border-white/10 px-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500 shadow-lg shadow-blue-950/40">
            <Building2 size={22} />
          </div>
          <div>
            <p className="text-[15px] font-bold tracking-tight">Credence<span className="text-blue-400">Flow</span></p>
            <p className="mt-0.5 text-[10px] font-medium uppercase tracking-[0.16em] text-slate-400">Lending intelligence</p>
          </div>
          <button aria-label="Close menu" onClick={() => setMobileNavOpen(false)} className="ml-auto rounded-lg p-1 text-slate-400 hover:bg-slate-800 lg:hidden">
            <X size={19} />
          </button>
        </div>

        <div className="border-b border-white/10 px-4 py-4">
          <button className="flex w-full items-center gap-3 rounded-xl border border-white/10 bg-white/[0.04] p-3 text-left hover:bg-white/[0.08]">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-400/15 text-indigo-300">
              <Building2 size={18} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold">Lending Operations</p>
              <p className="mt-1 text-[10px] text-slate-400">Primary workspace</p>
            </div>
            <ChevronDown size={15} className="text-slate-400" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-5">
          <p className="mb-2 px-3 text-[10px] font-bold tracking-[0.17em] text-slate-500">WORKSPACE</p>
          <div className="space-y-1">
            {renderNavigation(navigation.slice(0, 1))}
            {renderNavigation(navigation.slice(1))}
          </div>

          <p className="mb-2 mt-7 px-3 text-[10px] font-bold tracking-[0.17em] text-slate-500">GOVERNANCE</p>
          <div className="space-y-1">{renderNavigation(management)}</div>

          <div className="mt-7 rounded-xl border border-blue-400/20 bg-blue-500/[0.08] p-3.5">
            <div className="flex items-center gap-2 text-blue-300">
              <ShieldCheck size={17} />
              <span className="text-xs font-semibold">Platform controls</span>
            </div>
            <p className="mt-2 text-[11px] leading-5 text-slate-400">
              Credit decisions require authorised workflows. AI insights are advisory.
            </p>
          </div>
        </nav>

        <div className="border-t border-white/10 p-4">
          <button className="flex w-full items-center gap-3 rounded-lg p-2 text-left hover:bg-white/[0.05]">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-700 text-xs font-bold text-white">CO</div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold">Credit Operations</p>
              <p className="mt-1 text-[10px] text-slate-400">Workspace preview</p>
            </div>
            <LifeBuoy size={16} className="text-slate-400" />
          </button>
        </div>
      </aside>

      <div className="min-h-screen lg:pl-[250px]">
        <header className="sticky top-0 z-20 flex h-[76px] items-center justify-between gap-3 border-b border-slate-200/80 bg-white/95 px-4 backdrop-blur sm:px-7">
          <div className="flex min-w-0 items-center gap-3">
            <button aria-label="Open navigation" onClick={() => setMobileNavOpen(true)} className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden">
              <Menu size={20} />
            </button>
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-[11px] text-slate-400">
                <span>Workspace</span><span>/</span><span className="truncate text-slate-600">{activePage}</span>
              </div>
              <h1 className="mt-1 truncate text-[17px] font-bold tracking-tight text-slate-900 sm:text-lg">{activePage}</h1>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <label className="hidden h-9 w-56 items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 md:flex">
              <Search size={15} className="shrink-0 text-slate-400" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search applications..."
                className="min-w-0 flex-1 bg-transparent text-xs outline-none placeholder:text-slate-400"
              />
              <kbd className="rounded border border-slate-200 bg-white px-1 text-[9px] text-slate-400">⌘ K</kbd>
            </label>
            <button aria-label="Refresh dashboard" onClick={() => setLastUpdated('Just now')} className="hidden rounded-lg border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50 sm:block">
              <RefreshCw size={16} />
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
            >
              Sign out
            </button>
            <button aria-label="Notifications" className="relative rounded-lg border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50">
              <Bell size={17} />
              <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full border-2 border-white bg-rose-500" />
            </button>
            <div className="hidden h-8 w-px bg-slate-200 sm:block" />
            <button className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-slate-50">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">CO</div>
              <div className="hidden text-left sm:block">
                <p className="text-xs font-semibold text-slate-800">Credit Officer</p>
                <p className="mt-0.5 text-[10px] text-slate-400">Operations</p>
              </div>
              <ChevronDown size={14} className="hidden text-slate-400 sm:block" />
            </button>
          </div>
        </header>

        <main className="mx-auto max-w-[1600px] px-4 py-6 sm:px-7 sm:py-8">
          {activePage === 'Overview' ? (
            <>
              <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
                <div>
                  <div className="mb-2 flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Operations overview</span>
                  </div>
                  <h2 className="text-2xl font-bold tracking-tight text-slate-950 sm:text-[28px]">Good evening, Credit Team</h2>
                  <p className="mt-2 text-sm text-slate-500">Here's what's happening across your lending operations today.</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600">
                    <Clock3 size={14} className="text-slate-400" /> 16 Oct 2026
                  </span>
                  <button onClick={() => selectPage('Applications')} className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-blue-700">
                    <Plus size={15} /> New application
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard
                  title="Total applications"
                  value={dashboard ? dashboard.applications.total.toLocaleString() : '—'}
                  change={dashboard ? `${dashboard.applications.by_status['RECEIVED'] ?? 0} received` : 'Loading…'}
                  detail="Live application portfolio"
                  icon={FileText}
                  iconClass="bg-blue-50 text-blue-600"
                  trend="up"
                />
                <MetricCard
                  title="Approved decisions"
                  value={dashboard ? (dashboard.underwriting.by_status['APPROVE'] ?? 0).toLocaleString() : '—'}
                  change={dashboard ? `${dashboard.underwriting.total.toLocaleString()} evaluated` : 'Loading…'}
                  detail="Underwriting decisions"
                  icon={CheckCircle2}
                  iconClass="bg-emerald-50 text-emerald-600"
                  trend="up"
                />
                <MetricCard
                  title="Pending reviews"
                  value={dashboard ? (dashboard.manual_review.by_status['OPEN'] ?? 0).toLocaleString() : '—'}
                  change={dashboard ? `${dashboard.exceptions.by_status['OPEN'] ?? 0} open exceptions` : 'Loading…'}
                  detail="Require officer attention"
                  icon={ClipboardCheck}
                  iconClass="bg-amber-50 text-amber-600"
                  trend="warning"
                />
                <MetricCard
                  title="Disbursements processed"
                  value={dashboard ? (dashboard.disbursements.by_status['PROCESSED'] ?? 0).toLocaleString() : '—'}
                  change={dashboard ? `${dashboard.disbursements.total.toLocaleString()} total records` : 'Loading…'}
                  detail="Live disbursement status"
                  icon={CreditCard}
                  iconClass="bg-violet-50 text-violet-600"
                  trend="up"
                />
              </div>

              {dashboardError && (
                <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  Dashboard API error: {dashboardError}
                </div>
              )}

              <div className="mt-6 grid grid-cols-1 gap-5 xl:grid-cols-3">
                <section className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6 xl:col-span-2">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">Application volume</h3>
                      <p className="mt-1 text-xs text-slate-500">Monthly application intake across all products</p>
                    </div>
                    <button className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50">
                      Last 6 months <ChevronDown size={13} />
                    </button>
                  </div>
                  <div className="mt-7 flex items-end gap-3">
                    <p className="text-3xl font-bold tracking-tight text-slate-950">1,284</p>
                    <span className="mb-1 flex items-center gap-1 text-xs font-semibold text-emerald-600"><ArrowUpRight size={14} /> 12.8%</span>
                  </div>
                  <p className="mt-1 text-[11px] text-slate-400">Applications received</p>
                  <div className="mt-5 grid h-[190px] grid-cols-6 items-end gap-3 border-b border-slate-100 pb-0 sm:gap-5">
                    {volume.map((item) => (
                      <div key={item.month} className="flex h-full flex-col items-center justify-end gap-2">
                        <span className="text-[10px] font-medium text-slate-400">{item.value * 15}</span>
                        <div className="flex h-[145px] w-full items-end overflow-hidden rounded-t-md bg-slate-50">
                          <div
                            className={`w-full rounded-t-md transition-all ${item.month === 'Oct' ? 'bg-blue-600' : 'bg-blue-200 hover:bg-blue-300'}`}
                            style={{ height: `${item.value}%` }}
                            title={`${item.month}: ${item.value * 15} applications`}
                          />
                        </div>
                        <span className={`pb-2 text-[11px] ${item.month === 'Oct' ? 'font-bold text-blue-700' : 'text-slate-500'}`}>{item.month}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex items-center gap-2 text-[11px] text-slate-400">
                    <span className="h-2 w-2 rounded-sm bg-blue-600" /> Current month
                    <span className="ml-3 h-2 w-2 rounded-sm bg-blue-200" /> Previous months
                  </div>
                </section>

                <section className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">Application outcomes</h3>
                      <p className="mt-1 text-xs text-slate-500">Decision distribution</p>
                    </div>
                    <button aria-label="View outcome details" onClick={() => selectPage('Reports & analytics')} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100">
                      <ArrowRight size={16} />
                    </button>
                  </div>
                  <div className="flex items-center justify-center py-6">
                    <div className="relative flex h-40 w-40 items-center justify-center rounded-full" style={{ background: 'conic-gradient(#2563eb 0% 68.4%, #f59e0b 68.4% 85%, #e2e8f0 85% 100%)' }}>
                      <div className="flex h-[112px] w-[112px] flex-col items-center justify-center rounded-full bg-white">
                        <span className="text-2xl font-bold tracking-tight text-slate-900">68.4%</span>
                        <span className="mt-1 text-[10px] text-slate-400">Approval rate</span>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <OutcomeRow color="bg-blue-600" label="Approved" value="68.4%" count="879" />
                    <OutcomeRow color="bg-amber-400" label="Referred for review" value="16.6%" count="213" />
                    <OutcomeRow color="bg-slate-200" label="Other outcomes" value="15.0%" count="192" />
                  </div>
                  <p className="mt-5 rounded-lg bg-slate-50 p-3 text-[10px] leading-4 text-slate-500">
                    Illustrative dashboard figures. Live values will come from the lending platform API.
                  </p>
                </section>
              </div>


              <div className="mt-6 grid grid-cols-1 gap-5 xl:grid-cols-3">
                {applicationsError && (
                  <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                    Applications API error: {applicationsError}
                  </div>
                )}
                <section className="overflow-hidden rounded-xl border border-slate-200/80 bg-white shadow-sm xl:col-span-2">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-5 sm:px-6">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">Recent applications</h3>
                      <p className="mt-1 text-xs text-slate-500">Latest activity from your application pipeline</p>
                    </div>
                    <button onClick={() => selectPage('Applications')} className="flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800">
                      View all <ArrowRight size={14} />
                    </button>
                  </div>
                  <div className="border-b border-slate-100 px-5 py-3 md:hidden">
                    <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
                      <Search size={15} className="text-slate-400" />
                      <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search applications..." className="min-w-0 flex-1 bg-transparent text-xs outline-none" />
                    </label>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[690px] text-left">
                      <thead>
                        <tr className="bg-slate-50/80 text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400">
                          <th className="px-5 py-3 sm:px-6">Application / Customer ID</th>
                          <th className="px-4 py-3">Requested amount / Product</th>
                          <th className="px-4 py-3">Decision / Risk grade</th>
                          <th className="px-4 py-3">Application status</th>
                          <th className="px-5 py-3 sm:px-6">Created date</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {filteredApplications.map((item) => (
                          <tr key={item.application_id} className="transition hover:bg-slate-50/70">
                            <td className="whitespace-nowrap px-5 py-4 sm:px-6">
                              <p className="text-xs font-semibold text-slate-800">
                                {item.application_id}
                              </p>
                              <p className="mt-1 text-[10px] text-slate-400">
                                Customer: {item.customer_id}
                              </p>
                            </td>

                            <td className="px-5 py-4 sm:px-6">
                              <p className="text-xs font-semibold text-slate-800">
                                {'₹'}{Number(item.requested_amount).toLocaleString('en-IN')}
                              </p>
                              <p className="mt-1 text-[10px] text-slate-500">
                                {item.product.replaceAll('_', ' ')}
                              </p>
                            </td>

                            <td className="whitespace-nowrap px-5 py-4 sm:px-6">
                              <span className="text-xs font-medium text-slate-700">
                                {item.decision ?? 'Pending'}
                              </span>
                              {item.risk_grade && (
                                <p className="mt-1 text-[10px] text-slate-500">
                                  Risk grade: {item.risk_grade}
                                </p>
                              )}
                            </td>

                            <td className="whitespace-nowrap px-5 py-4 sm:px-6">
                              <span className="inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-semibold text-slate-700">
                                {item.status.replaceAll('_', ' ')}
                              </span>
                            </td>

                            <td className="whitespace-nowrap px-5 py-4 text-[11px] text-slate-500 sm:px-6">
                              {new Date(item.created_at).toLocaleDateString('en-IN', {
                                day: '2-digit',
                                month: 'short',
                                year: 'numeric',
                              })}
                            </td>
                          </tr>
                        ))}
                        {filteredApplications.length === 0 && (
                          <tr><td colSpan={5} className="px-5 py-10 text-center text-xs text-slate-400">No matching applications found.</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                  <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3 sm:px-6">
                    <span className="text-[10px] text-slate-400">Showing {filteredApplications.length} of {applicationsTotal} applications</span>
                    <button onClick={() => setSearch('')} className="text-[10px] font-semibold text-blue-600 hover:text-blue-800">Clear search</button>
                  </div>
                </section>

                <section className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">Attention required</h3>
                      <p className="mt-1 text-xs text-slate-500">Items needing follow-up</p>
                    </div>
                    <span className="rounded-md bg-rose-50 px-2 py-1 text-[10px] font-bold text-rose-600">3 alerts</span>
                  </div>
                  <div className="mt-5 space-y-4">
                    <AlertItem icon={ClipboardCheck} iconClass="bg-amber-50 text-amber-600" title="Credit reviews pending" description="12 applications are marked urgent." count="12" onClick={() => selectPage('Review queue')} />
                    <AlertItem icon={FileSearch} iconClass="bg-blue-50 text-blue-600" title="Documents outstanding" description="8 applications need documents." count="08" onClick={() => selectPage('Documents')} />
                    <AlertItem icon={AlertTriangle} iconClass="bg-rose-50 text-rose-600" title="Payment exceptions" description="3 disbursement items need review." count="03" onClick={() => selectPage('Disbursements')} />
                  </div>
                  <button onClick={() => selectPage('Review queue')} className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 py-2.5 text-xs font-semibold text-slate-600 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700">
                    Open operations queue <ArrowRight size={14} />
                  </button>
                </section>
              </div>

              <div className="mt-6 flex flex-col justify-between gap-2 border-t border-slate-200/80 pt-4 text-[10px] text-slate-400 sm:flex-row sm:items-center">
                <span>CredenceFlow · Lender Operations Workspace</span>
                <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> UI preview · Updated {lastUpdated}</span>
              </div>
            </>
          ) : activePage === 'Review queue' ? (
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
              <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Manual review queue</h2>
                  <p className="mt-1 text-xs text-slate-500">
                    Live records requiring authorised credit-officer review.
                  </p>
                </div>
                <button
                  onClick={() => window.location.reload()}
                  className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  <RefreshCw size={14} /> Refresh
                </button>
              </div>

              {manualReviewsError && (
                <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  Manual review API error: {manualReviewsError}
                </div>
              )}

              {reviewActionError && (
                <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {reviewActionError}
                </div>
              )}

              {reviewActionMessage && (
                <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                  {reviewActionMessage}
                </div>
              )}

              <div className="mt-5 overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-y border-slate-100 bg-slate-50 text-[10px] uppercase tracking-wider text-slate-500">
                      <th className="px-4 py-3 font-semibold">Application ID</th>
                      <th className="px-4 py-3 font-semibold">Review status</th>
                      <th className="px-4 py-3 font-semibold">Review reason</th>
                      <th className="px-4 py-3 font-semibold">Maker-checker</th>
                      <th className="px-4 py-3 font-semibold">Created</th>
                      <th className="px-4 py-3 text-left">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {manualReviews.map((review) => (
                      <tr key={review.review_id} className="align-top hover:bg-slate-50/70">
                        <td className="whitespace-nowrap px-4 py-4 text-xs font-semibold text-slate-800">
                          {review.application_id}
                        </td>
                        <td className="whitespace-nowrap px-4 py-4">
                          <span className={`rounded-md px-2 py-1 text-[10px] font-bold ${review.review_status === 'OPEN'
                            ? 'bg-amber-50 text-amber-700'
                            : 'bg-emerald-50 text-emerald-700'
                            }`}>
                            {review.review_status.replaceAll('_', ' ')}
                          </span>
                        </td>
                        <td className="min-w-64 max-w-md px-4 py-4 text-xs leading-5 text-slate-600">
                          {review.review_reason || 'No reason provided'}
                        </td>
                        <td className="whitespace-nowrap px-4 py-4 text-xs text-slate-600">
                          {review.maker_checker_required ? 'Required' : 'Not required'}
                        </td>
                        <td className="whitespace-nowrap px-4 py-4 text-xs text-slate-500">
                          {new Date(review.created_at).toLocaleDateString('en-IN', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </td>

                        <td className="px-4 py-3">

                          <button
                            type="button"
                            onClick={() => handleLoadUnderwritingResult(review.application_id)}
                            disabled={underwritingLoading === review.application_id}
                            className="mb-2 rounded-lg border border-indigo-200 px-3 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-50 disabled:opacity-50"
                          >
                            {underwritingLoading === review.application_id
                              ? 'Loading decision...'
                              : expandedDecisionId === review.application_id
                                ? 'Hide decision details'
                                : 'View decision details'}
                          </button>

                          {underwritingErrors[review.application_id] && (
                            <p className="mb-2 text-xs text-red-600">
                              {underwritingErrors[review.application_id]}
                            </p>
                          )}

                          {expandedDecisionId === review.application_id &&
                            underwritingResults[review.application_id] && (
                              <div className="mb-3 min-w-64 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs">

                                <div className="mb-4">
                                  <h4 className="mb-2 font-semibold text-slate-800">
                                    Risk summary
                                  </h4>

                                  <div className="grid grid-cols-2 gap-2">
                                    <div className="rounded-lg border border-slate-200 bg-white p-3">
                                      <p className="text-slate-500">Credit score</p>
                                      <p className="mt-1 text-lg font-bold text-slate-900">
                                        {underwritingResults[review.application_id].credit_score ?? 'N/A'}
                                      </p>
                                    </div>

                                    <div className="rounded-lg border border-slate-200 bg-white p-3">
                                      <p className="text-slate-500">Probability of default</p>
                                      <p className="mt-1 text-lg font-bold text-slate-900">
                                        {underwritingResults[review.application_id].probability_of_default == null
                                          ? 'N/A'
                                          : `${(Number(underwritingResults[review.application_id].probability_of_default) * 100).toFixed(2)}%`}
                                      </p>
                                    </div>

                                    <div className="rounded-lg border border-slate-200 bg-white p-3">
                                      <p className="text-slate-500">Affordability score</p>
                                      <p className="mt-1 text-lg font-bold text-slate-900">
                                        {underwritingResults[review.application_id].affordability_score == null
                                          ? 'N/A'
                                          : `${Number(underwritingResults[review.application_id].affordability_score).toFixed(1)}%`}
                                      </p>
                                    </div>

                                    <div className="rounded-lg border border-slate-200 bg-white p-3">
                                      <p className="text-slate-500">FOIR</p>
                                      <p className="mt-1 text-lg font-bold text-slate-900">
                                        {underwritingResults[review.application_id].foir == null
                                          ? 'N/A'
                                          : `${Number(underwritingResults[review.application_id].foir).toFixed(2)}%`}
                                      </p>
                                    </div>
                                  </div>
                                </div>



                                <div className="mb-4 rounded-lg border border-slate-200 bg-white p-3">
                                  <h4 className="mb-3 font-semibold text-slate-900">
                                    Review workflow
                                  </h4>

                                  <div className="space-y-3">
                                    <div>
                                      <p className="text-slate-500">Model decision</p>
                                      <p className="font-semibold text-slate-800">
                                        {underwritingResults[review.application_id].decision}
                                      </p>
                                    </div>

                                    <div>
                                      <p className="text-slate-500">Maker recommendation</p>

                                      <span
                                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${!review.reviewer_decision
                                          ? 'bg-slate-100 text-slate-600'
                                          : review.reviewer_decision === 'APPROVE'
                                            ? 'bg-green-100 text-green-800'
                                            : review.reviewer_decision === 'REJECT'
                                              ? 'bg-red-100 text-red-800'
                                              : review.reviewer_decision === 'REFER'
                                                ? 'bg-amber-100 text-amber-800'
                                                : 'bg-slate-100 text-slate-700'
                                          }`}
                                      >
                                        {review.reviewer_decision ?? 'Not submitted'}
                                      </span>

                                      {review.reviewer_id && (
                                        <p className="mt-1 break-words text-slate-500">
                                          Submitted by: {review.reviewer_id}
                                        </p>
                                      )}
                                      {review.reviewer_remarks && (
                                        <p className="mt-1 break-words text-slate-600">
                                          Remarks: {review.reviewer_remarks}
                                        </p>
                                      )}
                                    </div>

                                    {review.maker_checker_required && (
                                      <div>
                                        <p className="text-slate-500">Checker decision</p>

                                        <span
                                          className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${!review.checker_decision
                                            ? 'bg-amber-100 text-amber-800'
                                            : review.checker_decision === 'APPROVE'
                                              ? 'bg-green-100 text-green-800'
                                              : review.checker_decision === 'REJECT'
                                                ? 'bg-red-100 text-red-800'
                                                : review.checker_decision === 'REFER'
                                                  ? 'bg-amber-100 text-amber-800'
                                                  : 'bg-slate-100 text-slate-700'
                                            }`}
                                        >
                                          {review.checker_decision ?? 'Pending checker decision'}
                                        </span>

                                        {review.checker_id && (
                                          <p className="mt-1 break-words text-slate-500">
                                            Checked by: {review.checker_id}
                                          </p>
                                        )}
                                        {review.checker_remarks && (
                                          <p className="mt-1 break-words text-slate-600">
                                            Remarks: {review.checker_remarks}
                                          </p>
                                        )}
                                      </div>
                                    )}

                                    <div>
                                      <p className="text-slate-500">Review status</p>

                                      <span
                                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${review.review_status === 'OPEN'
                                          ? 'bg-amber-100 text-amber-800'
                                          : 'bg-slate-100 text-slate-700'
                                          }`}
                                      >
                                        {review.review_status.replaceAll('_', ' ')}
                                      </span>

                                    </div>
                                  </div>
                                </div>


                                <div className="grid grid-cols-2 gap-3">

                                  <div>
                                    <p className="text-slate-500">Model decision</p>
                                    <span
                                      className={`mt-1 inline-flex rounded-full px-3 py-1 text-xs font-bold ${underwritingResults[review.application_id].decision === 'APPROVE'
                                        ? 'bg-green-100 text-green-800'
                                        : underwritingResults[review.application_id].decision === 'REJECT'
                                          ? 'bg-red-100 text-red-800'
                                          : underwritingResults[review.application_id].decision === 'REFER'
                                            ? 'bg-amber-100 text-amber-800'
                                            : 'bg-slate-100 text-slate-800'
                                        }`}
                                    >
                                      {underwritingResults[review.application_id].decision}
                                    </span>
                                  </div>


                                  <div>
                                    <p className="text-slate-500">Risk grade</p>
                                    <p className="font-semibold text-slate-900">
                                      {underwritingResults[review.application_id].risk_grade ?? 'N/A'}
                                    </p>
                                  </div>

                                  <div>
                                    <p className="text-slate-500">Credit score</p>
                                    <p className="font-semibold text-slate-900">
                                      {underwritingResults[review.application_id].credit_score ?? 'N/A'}
                                    </p>
                                  </div>

                                  <div>
                                    <p className="text-slate-500">Probability of default</p>
                                    <p className="font-semibold text-slate-900">
                                      {underwritingResults[review.application_id].probability_of_default == null
                                        ? 'N/A'
                                        : `${(underwritingResults[review.application_id].probability_of_default! * 100).toFixed(2)}%`}
                                    </p>
                                  </div>

                                  <div>
                                    <p className="text-slate-500">Recommended amount</p>
                                    <p className="font-semibold text-slate-900">
                                      {underwritingResults[review.application_id].recommended_amount == null
                                        ? 'N/A'
                                        : `₹${Number(underwritingResults[review.application_id].recommended_amount).toLocaleString('en-IN')}`}
                                    </p>
                                  </div>

                                  <div>
                                    <p className="text-slate-500">Recommended tenure</p>
                                    <p className="font-semibold text-slate-900">
                                      {underwritingResults[review.application_id].recommended_tenure == null
                                        ? 'N/A'
                                        : `${underwritingResults[review.application_id].recommended_tenure} months`}
                                    </p>
                                  </div>

                                  <div>
                                    <p className="text-slate-500">Recommended EMI</p>
                                    <p className="font-semibold text-slate-900">
                                      {underwritingResults[review.application_id].recommended_emi == null
                                        ? 'N/A'
                                        : `₹${Number(underwritingResults[review.application_id].recommended_emi).toLocaleString('en-IN')}`}
                                    </p>
                                  </div>

                                  <div>
                                    <p className="text-slate-500">FOIR</p>
                                    <p className="font-semibold text-slate-900">
                                      {underwritingResults[review.application_id].foir == null
                                        ? 'N/A'
                                        : `${(Number(underwritingResults[review.application_id].foir).toFixed(2))}%`}
                                    </p>
                                  </div>


                                  <div>
                                    <p className="text-slate-500">Affordability score</p>
                                    <p className="font-semibold text-slate-900">
                                      {underwritingResults[review.application_id].affordability_score == null
                                        ? 'N/A'
                                        : `${Number(underwritingResults[review.application_id].affordability_score).toFixed(1)}%`}
                                    </p>
                                  </div>

                                  <div>
                                    <p className="text-slate-500">Income stability score</p>
                                    <p className="font-semibold text-slate-900">
                                      {underwritingResults[review.application_id].income_stability_score == null
                                        ? 'N/A'
                                        : `${Number(underwritingResults[review.application_id].income_stability_score).toFixed(1)}%`}
                                    </p>
                                  </div>

                                </div>


                                <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
                                  <h4 className="font-semibold text-amber-900">
                                    Assessment completeness
                                  </h4>

                                  <ul className="mt-2 space-y-1 text-sm text-amber-900">
                                    {(underwritingResults[review.application_id].reason_codes ?? [])
                                      .includes('POLICY_DATA_INCOMPLETE') && (
                                        <li>• Policy data is incomplete.</li>
                                      )}

                                    {(underwritingResults[review.application_id].reason_codes ?? [])
                                      .includes('FRAUD_ASSESSMENT_INCOMPLETE') && (
                                        <li>• Fraud assessment is incomplete.</li>
                                      )}

                                    {underwritingResults[review.application_id].fraud_score == null && (
                                      <li>• Fraud score is not available.</li>
                                    )}

                                    {underwritingResults[review.application_id].confidence == null && (
                                      <li>• Model confidence has not been calculated.</li>
                                    )}

                                    {(underwritingResults[review.application_id].reason_codes ?? [])
                                      .every((code) =>
                                        ![
                                          'POLICY_DATA_INCOMPLETE',
                                          'FRAUD_ASSESSMENT_INCOMPLETE',
                                        ].includes(code),
                                      ) &&
                                      underwritingResults[review.application_id].fraud_score != null &&
                                      underwritingResults[review.application_id].confidence != null && (
                                        <li>No missing assessments identified by these indicators.</li>
                                      )}
                                  </ul>
                                </div>


                                <div className="mt-3 border-t border-slate-200 pt-3">
                                  <p className="font-semibold text-slate-800">Reason codes</p>
                                  <div className="mt-2 space-y-3">
                                    {(underwritingResults[review.application_id].reason_codes ?? []).length > 0 ? (
                                      (underwritingResults[review.application_id].reason_codes ?? []).map(
                                        (code) => (
                                          <div
                                            key={code}
                                            className="rounded-md border border-slate-200 bg-white p-3"
                                          >
                                            <p className="break-words font-mono text-xs text-slate-500">
                                              {code}
                                            </p>
                                            <p className="mt-1 text-sm text-slate-800">
                                              {REASON_CODE_EXPLANATIONS[code] ??
                                                'Additional review may be required. Refer to the original reason code.'}
                                            </p>
                                          </div>
                                        ),
                                      )
                                    ) : (
                                      <p className="text-slate-800">No reason codes provided.</p>
                                    )}
                                  </div>
                                  <p className="mt-1 break-words text-slate-800">
                                    {(underwritingResults[review.application_id].reason_codes ?? []).length > 0
                                      ? (underwritingResults[review.application_id].reason_codes ?? []).join(', ')
                                      : 'No reason codes provided'}
                                  </p>

                                  <p className="mt-2 text-slate-500">Model / policy version</p>
                                  <p className="mt-1 break-words text-slate-800">
                                    {underwritingResults[review.application_id].model_version ?? 'N/A'}
                                    {' / '}
                                    {underwritingResults[review.application_id].policy_version ?? 'N/A'}
                                  </p>

                                  <p className="mt-2 text-slate-500">Decision confidence</p>
                                  <p className="mt-1 font-semibold text-slate-900">
                                    {underwritingResults[review.application_id].confidence == null
                                      ? 'Not calculated by model'
                                      : `${(underwritingResults[review.application_id].confidence! * 100).toFixed(1)}%`}
                                  </p>
                                </div>
                              </div>
                            )}

                          {review.review_status === 'OPEN' && (
                            <button
                              type="button"
                              disabled={reviewActionLoading === review.application_id}
                              onClick={() => void handleStartReview(review.application_id)}
                              className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
                            >
                              {reviewActionLoading === review.application_id ? 'Working...' : 'Start review'}
                            </button>
                          )}

                          {review.review_status === 'IN_PROGRESS' && (
                            <div className="min-w-52 space-y-2">
                              <select
                                value={makerDecision}
                                onChange={(event) =>
                                  setMakerDecision(event.target.value as 'APPROVE' | 'REJECT')
                                }
                                className="w-full rounded-lg border border-slate-300 px-2 py-2 text-xs"
                              >
                                <option value="APPROVE">Recommend approval</option>
                                <option value="REJECT">Recommend rejection</option>
                              </select>

                              <textarea
                                value={makerRemarks}
                                onChange={(event) => setMakerRemarks(event.target.value)}
                                placeholder="Maker remarks (optional)"
                                rows={2}
                                className="w-full rounded-lg border border-slate-300 px-2 py-2 text-xs"
                              />

                              <button
                                type="button"
                                disabled={reviewActionLoading === review.application_id}
                                onClick={() => void handleMakerRecommendation(review.application_id)}
                                className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
                              >
                                Submit recommendation
                              </button>
                            </div>
                          )}

                          {review.review_status === 'PENDING_CHECKER' && (
                            <div className="min-w-52 space-y-2">
                              <select
                                value={checkerDecision}
                                onChange={(event) =>
                                  setCheckerDecision(event.target.value as 'APPROVE' | 'REJECT')
                                }
                                className="w-full rounded-lg border border-slate-300 px-2 py-2 text-xs"
                              >
                                <option value="APPROVE">Approve final decision</option>
                                <option value="REJECT">Reject final decision</option>
                              </select>

                              <textarea
                                value={checkerRemarks}
                                onChange={(event) => setCheckerRemarks(event.target.value)}
                                placeholder="Checker remarks (optional)"
                                rows={2}
                                className="w-full rounded-lg border border-slate-300 px-2 py-2 text-xs"
                              />

                              <button
                                type="button"
                                disabled={reviewActionLoading === review.application_id}
                                onClick={() => void handleCheckerDecision(review.application_id)}
                                className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
                              >
                                Submit checker decision
                              </button>
                            </div>
                          )}

                          {!['OPEN', 'IN_PROGRESS', 'PENDING_CHECKER'].includes(review.review_status) && (
                            <span className="text-xs text-slate-500">No action available</span>
                          )}
                        </td>

                      </tr>
                    ))}
                    {manualReviews.length === 0 && !manualReviewsError && (
                      <tr>
                        <td colSpan={6} className="px-4 py-10 text-center text-xs text-slate-400">
                          No manual-review records loaded.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
                Showing {manualReviews.length} manual-review records
              </div>
            </section>
          ) : activePage === 'Applications' ? (
            <section className="space-y-6">
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-blue-600">
                    Lending workspace
                  </p>
                  <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
                    Applications
                  </h2>
                  <p className="mt-2 text-sm text-slate-500">
                    Track applications from intake through final credit decision.
                  </p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
                  <p className="text-xs text-slate-500">Total applications</p>
                  <p className="mt-1 text-xl font-bold text-slate-950">
                    {applicationsTotal}
                  </p>
                </div>
              </div>

              <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-200 px-5 py-4">
                  <h3 className="text-sm font-semibold text-slate-900">
                    Application register
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Showing {filteredApplications.length} of {applications.length} loaded applications
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-3 border-b border-slate-200 p-4 md:grid-cols-3">
                  <input
                    type="text"
                    value={applicationSearch}
                    onChange={(event) => setApplicationSearch(event.target.value)}
                    placeholder="Search application, customer, product..."
                    aria-label="Search applications"
                    className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  />

                  <select
                    value={applicationStatusFilter}
                    onChange={(event) => setApplicationStatusFilter(event.target.value)}
                    aria-label="Filter by application status"
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                  >
                    <option value="ALL">All application statuses</option>
                    {Array.from(new Set(applications.map((item) => item.status)))
                      .sort()
                      .map((status) => (
                        <option key={status} value={status}>{status}</option>
                      ))}
                  </select>

                  <select
                    value={applicationDecisionFilter}
                    onChange={(event) => setApplicationDecisionFilter(event.target.value)}
                    aria-label="Filter by credit decision"
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                  >
                    <option value="ALL">All credit decisions</option>
                    {Array.from(
                      new Set(
                        applications
                          .map((item) => item.decision)
                          .filter((decision): decision is string => Boolean(decision)),
                      ),
                    )
                      .sort()
                      .map((decision) => (
                        <option key={decision} value={decision}>{decision}</option>
                      ))}
                  </select>
                </div>

                {applicationsError ? (
                  <div className="p-6 text-sm text-red-600">
                    Unable to load applications: {applicationsError}
                  </div>
                ) : filteredApplications.length === 0 ? (
                  <div className="p-10 text-center text-sm text-slate-500">
                    No applications found.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-[1050px] w-full text-left text-xs">
                      <thead className="bg-slate-50 text-[10px] uppercase tracking-wider text-slate-500">
                        <tr>
                          <th className="px-5 py-3 font-semibold">Application ID</th>
                          <th className="px-5 py-3 font-semibold">Customer ID</th>
                          <th className="px-5 py-3 text-right font-semibold">Requested amount</th>
                          <th className="px-5 py-3 font-semibold">Status</th>
                          <th className="px-5 py-3 font-semibold">Decision</th>
                          <th className="px-5 py-3 font-semibold">Risk grade</th>
                          <th className="px-5 py-3 font-semibold">Created</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {filteredApplications.map((application) => (
                          <tr
                            key={application.application_id}
                            onClick={() => setSelectedApplication(application)}
                            onKeyDown={(event) => {
                              if (event.key === 'Enter') {
                                setSelectedApplication(application)
                              }
                            }}
                            tabIndex={0}
                            role="button"
                            aria-label={`View application ${application.application_id}`}
                            className="cursor-pointer transition hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
                          >
                            <td className="whitespace-nowrap px-5 py-4 font-semibold text-slate-800">
                              {application.application_id}
                            </td>
                            <td className="whitespace-nowrap px-5 py-4 text-slate-600">
                              {application.customer_id}
                            </td>
                            <td className="whitespace-nowrap px-5 py-4 text-right font-medium tabular-nums text-slate-800">
                              ₹{Number(application.requested_amount).toLocaleString('en-IN')}
                            </td>
                            <td className="whitespace-nowrap px-5 py-4">
                              <span className="inline-flex rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-700">
                                {application.status}
                              </span>
                            </td>
                            <td className="whitespace-nowrap px-5 py-4 text-slate-600">
                              {application.decision ?? '—'}
                            </td>
                            <td className="whitespace-nowrap px-5 py-4 text-slate-600">
                              {application.risk_grade ?? '—'}
                            </td>
                            <td className="whitespace-nowrap px-5 py-4 text-slate-600">
                              {new Date(application.created_at).toLocaleDateString('en-IN')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

              </div>

              {selectedApplication && (
                <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                  <div className="flex flex-col justify-between gap-3 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-blue-600">
                        Application details
                      </p>
                      <h3 className="mt-1 text-lg font-bold text-slate-950">
                        {selectedApplication.application_id}
                      </h3>
                      <p className="mt-1 text-xs text-slate-500">
                        Customer: {selectedApplication.customer_id}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSelectedApplication(null)}
                      className="self-start rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 sm:self-auto"
                    >
                      Close details
                    </button>
                  </div>

                  <div className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2 lg:grid-cols-3">
                    <div className="rounded-lg bg-slate-50 p-4">
                      <p className="text-xs text-slate-500">Requested amount</p>
                      <p className="mt-2 text-lg font-bold text-slate-950">
                        ₹{Number(selectedApplication.requested_amount).toLocaleString('en-IN')}
                      </p>
                    </div>

                    <div className="rounded-lg bg-slate-50 p-4">
                      <p className="text-xs text-slate-500">Application status</p>
                      <p className="mt-2 text-lg font-bold text-slate-950">
                        {selectedApplication.status}
                      </p>
                    </div>

                    <div className="rounded-lg bg-slate-50 p-4">
                      <p className="text-xs text-slate-500">Credit decision</p>
                      <p className="mt-2 text-lg font-bold text-slate-950">
                        {selectedApplication.decision ?? 'Pending'}
                      </p>
                    </div>

                    <div className="rounded-lg border border-slate-100 p-4">
                      <p className="text-xs text-slate-500">Customer ID</p>
                      <p className="mt-2 break-all text-sm font-semibold text-slate-800">
                        {selectedApplication.customer_id}
                      </p>
                    </div>

                    <div className="rounded-lg border border-slate-100 p-4">
                      <p className="text-xs text-slate-500">Product</p>
                      <p className="mt-2 text-sm font-semibold text-slate-800">
                        {selectedApplication.product || '—'}
                      </p>
                    </div>

                    <div className="rounded-lg border border-slate-100 p-4">
                      <p className="text-xs text-slate-500">Risk grade</p>
                      <p className="mt-2 text-sm font-semibold text-slate-800">
                        {selectedApplication.risk_grade ?? 'Not available'}
                      </p>
                    </div>

                    <div className="rounded-lg border border-slate-100 p-4">
                      <p className="text-xs text-slate-500">Manual review</p>
                      <p className="mt-2 text-sm font-semibold text-slate-800">
                        {selectedApplication.manual_review_status ?? 'No review status'}
                      </p>
                    </div>

                    <div className="rounded-lg border border-slate-100 p-4">
                      <p className="text-xs text-slate-500">Disbursement</p>
                      <p className="mt-2 text-sm font-semibold text-slate-800">
                        {selectedApplication.disbursement_status ?? 'Not available'}
                      </p>
                    </div>

                    <div className="rounded-lg border border-slate-100 p-4">
                      <p className="text-xs text-slate-500">Created date</p>
                      <p className="mt-2 text-sm font-semibold text-slate-800">
                        {new Date(selectedApplication.created_at).toLocaleString('en-IN')}
                      </p>
                    </div>
                  </div>

                  <div className="border-t border-slate-200 bg-slate-50 px-5 py-3 text-xs text-slate-500">
                    Read-only application summary. Credit decisions and disbursement actions must use their authorised backend workflows.
                  </div>
                </section>
              )}
            </section>

          ) : activePage === 'Underwriting' ? (
            <section className="space-y-6">
              <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">
                    Credit risk workspace
                  </p>
                  <h2 className="mt-1 text-xl font-bold text-slate-950">
                    Underwriting assessments
                  </h2>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                    Review persisted model assessments, risk indicators and reason codes.
                    Model recommendations are advisory; authorised credit workflows remain separate.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setUnderwritingResults({});
                    setUnderwritingErrors({});
                    setExpandedDecisionId(null);
                  }}
                  className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Refresh loaded assessments
                </button>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-xs text-slate-500">Loaded applications</p>
                  <p className="mt-2 text-2xl font-bold text-slate-950">
                    {applications.length}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-xs text-slate-500">Assessments loaded</p>
                  <p className="mt-2 text-2xl font-bold text-slate-950">
                    {Object.keys(underwritingResults).length}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-xs text-slate-500">Assessments requiring attention</p>
                  <p className="mt-2 text-2xl font-bold text-amber-700">
                    {Object.values(underwritingResults).filter(
                      (result) =>
                        result.decision === 'REFER' ||
                        result.reason_codes.includes('POLICY_DATA_INCOMPLETE') ||
                        result.reason_codes.includes('FRAUD_ASSESSMENT_INCOMPLETE') ||
                        result.fraud_score == null,
                    ).length}
                  </p>
                  <p className="mt-1 text-[11px] text-slate-400">
                    Based only on loaded assessment indicators
                  </p>
                </div>
              </div>

              <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-200 p-4 sm:p-5">
                  <h3 className="font-semibold text-slate-900">Applications and assessments</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Select an application to retrieve its saved underwriting result.
                  </p>
                </div>

                {applicationsError ? (
                  <div className="p-5 text-sm text-red-600">
                    Unable to load applications: {applicationsError}
                  </div>
                ) : applications.length === 0 ? (
                  <div className="p-10 text-center text-sm text-slate-500">
                    No applications are currently available.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[850px] text-left">
                      <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
                        <tr>
                          <th className="px-5 py-3 font-semibold">Application</th>
                          <th className="px-5 py-3 font-semibold">Product</th>
                          <th className="px-5 py-3 font-semibold">Requested amount</th>
                          <th className="px-5 py-3 font-semibold">Application status</th>
                          <th className="px-5 py-3 font-semibold">Model decision</th>
                          <th className="px-5 py-3 font-semibold">Assessment</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {applications.map((application) => {
                          const result = underwritingResults[application.application_id];
                          const isLoading =
                            underwritingLoading === application.application_id;
                          const error =
                            underwritingErrors[application.application_id];

                          return (
                            <tr
                              key={application.application_id}
                              className="align-top hover:bg-slate-50/70"
                            >
                              <td className="px-5 py-4">
                                <p className="text-xs font-semibold text-slate-900">
                                  {application.application_id}
                                </p>
                                <p className="mt-1 text-[11px] text-slate-500">
                                  Customer: {application.customer_id}
                                </p>
                              </td>
                              <td className="px-5 py-4 text-xs text-slate-700">
                                {application.product || '—'}
                              </td>
                              <td className="px-5 py-4 text-xs font-semibold text-slate-800">
                                {Number(application.requested_amount).toLocaleString(
                                  'en-IN',
                                  { style: 'currency', currency: 'INR', maximumFractionDigits: 0 },
                                )}
                              </td>
                              <td className="px-5 py-4 text-xs text-slate-700">
                                {application.status}
                              </td>
                              <td className="px-5 py-4">
                                {result ? (
                                  <span
                                    className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold ${result.decision === 'APPROVE'
                                      ? 'bg-emerald-100 text-emerald-800'
                                      : result.decision === 'REJECT'
                                        ? 'bg-red-100 text-red-800'
                                        : result.decision === 'REFER'
                                          ? 'bg-amber-100 text-amber-800'
                                          : 'bg-slate-100 text-slate-700'
                                      }`}
                                  >
                                    {result.decision}
                                  </span>
                                ) : (
                                  <span className="text-xs text-slate-400">Not loaded</span>
                                )}
                              </td>
                              <td className="px-5 py-4">
                                <button
                                  type="button"
                                  disabled={isLoading}
                                  onClick={() => {
                                    void handleLoadUnderwritingResult(
                                      application.application_id,
                                    );
                                  }}
                                  className="rounded-lg border border-indigo-200 px-3 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-50 disabled:cursor-wait disabled:opacity-50"
                                >
                                  {isLoading
                                    ? 'Loading…'
                                    : result
                                      ? expandedDecisionId === application.application_id
                                        ? 'Hide details'
                                        : 'View details'
                                      : 'Load assessment'}
                                </button>
                                {error && (
                                  <p className="mt-2 max-w-48 text-xs text-red-600">
                                    {error}
                                  </p>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>

              {expandedDecisionId && underwritingResults[expandedDecisionId] && (
                <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                  {(() => {
                    const result = underwritingResults[expandedDecisionId];
                    const metric = (value: number | string | null, suffix = '') =>
                      value == null
                        ? 'N/A'
                        : `${Number(value).toLocaleString('en-IN', {
                          maximumFractionDigits: 2,
                        })}${suffix}`;

                    return (
                      <>
                        <div className="flex flex-col justify-between gap-3 border-b border-slate-100 pb-4 sm:flex-row sm:items-start">
                          <div>
                            <p className="text-xs text-slate-500">Application</p>
                            <h3 className="mt-1 break-all text-lg font-bold text-slate-950">
                              {expandedDecisionId}
                            </h3>
                            <p className="mt-1 text-xs text-slate-500">
                              Saved assessment created{' '}
                              {new Date(result.created_at).toLocaleString('en-IN')}
                            </p>
                          </div>
                          <span className="inline-flex w-fit rounded-full bg-indigo-50 px-3 py-1.5 text-xs font-bold text-indigo-800">
                            Model decision: {result.decision}
                          </span>
                        </div>

                        <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
                          {[
                            ['Credit score', metric(result.credit_score)],
                            ['Risk grade', result.risk_grade ?? 'N/A'],
                            ['Probability of default', metric(
                              result.probability_of_default == null
                                ? null
                                : Number(result.probability_of_default) * 100,
                              '%',
                            )],
                            ['Affordability score', metric(result.affordability_score, '%')],
                            ['FOIR', metric(result.foir, '%')],
                            ['Income stability', metric(result.income_stability_score, '%')],
                            ['Fraud score', metric(result.fraud_score)],
                            ['Repayment propensity', metric(result.repayment_propensity)],
                            ['Recommended amount', result.recommended_amount == null
                              ? 'N/A'
                              : Number(result.recommended_amount).toLocaleString('en-IN', {
                                style: 'currency',
                                currency: 'INR',
                                maximumFractionDigits: 0,
                              })],
                            ['Recommended tenure', result.recommended_tenure == null
                              ? 'N/A'
                              : `${result.recommended_tenure} months`],
                            ['Recommended EMI', result.recommended_emi == null
                              ? 'N/A'
                              : Number(result.recommended_emi).toLocaleString('en-IN', {
                                style: 'currency',
                                currency: 'INR',
                                maximumFractionDigits: 0,
                              })],
                            ['Decision confidence', metric(
                              result.confidence == null
                                ? null
                                : Number(result.confidence) * 100,
                              '%',
                            )],
                          ].map(([label, value]) => (
                            <div
                              key={label}
                              className="rounded-lg border border-slate-100 bg-slate-50 p-4"
                            >
                              <p className="text-xs text-slate-500">{label}</p>
                              <p className="mt-2 break-words text-sm font-bold text-slate-900">
                                {value}
                              </p>
                            </div>
                          ))}
                        </div>

                        <div className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-4">
                          <h4 className="text-sm font-semibold text-amber-950">
                            Assessment completeness indicators
                          </h4>
                          <ul className="mt-2 space-y-1 text-xs leading-5 text-amber-900">
                            {result.reason_codes.includes('POLICY_DATA_INCOMPLETE') && (
                              <li>• Required policy information is incomplete.</li>
                            )}
                            {result.reason_codes.includes('FRAUD_ASSESSMENT_INCOMPLETE') && (
                              <li>• Fraud assessment is incomplete.</li>
                            )}
                            {result.fraud_score == null && (
                              <li>• Fraud score is unavailable.</li>
                            )}
                            {result.confidence == null && (
                              <li>• Model confidence was not calculated.</li>
                            )}
                            {!result.reason_codes.includes('POLICY_DATA_INCOMPLETE') &&
                              !result.reason_codes.includes('FRAUD_ASSESSMENT_INCOMPLETE') &&
                              result.fraud_score != null &&
                              result.confidence != null && (
                                <li>No missing assessments identified by these indicators.</li>
                              )}
                          </ul>
                        </div>

                        <div className="mt-5">
                          <h4 className="text-sm font-semibold text-slate-900">
                            Reason codes and explanations
                          </h4>
                          {result.reason_codes.length > 0 ? (
                            <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
                              {result.reason_codes.map((code) => (
                                <div
                                  key={code}
                                  className="rounded-lg border border-slate-200 p-4"
                                >
                                  <p className="break-all text-xs font-bold text-slate-800">
                                    {code}
                                  </p>
                                  <p className="mt-1 text-xs leading-5 text-slate-600">
                                    {REASON_CODE_EXPLANATIONS[code] ??
                                      'No explanation is currently configured for this reason code.'}
                                  </p>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="mt-2 text-xs text-slate-500">
                              No reason codes were returned by the backend.
                            </p>
                          )}
                        </div>

                        <div className="mt-5 border-t border-slate-100 pt-4">
                          <p className="text-xs text-slate-500">Model version / policy version</p>
                          <p className="mt-1 break-all text-sm font-semibold text-slate-800">
                            {result.model_version ?? 'N/A'} / {result.policy_version ?? 'N/A'}
                          </p>
                          <p className="mt-3 text-xs leading-5 text-slate-500">
                            This is a persisted model assessment, not proof of final loan
                            authorisation. Follow the existing manual-review and maker-checker
                            workflow for any required human decision.
                          </p>
                          <button
                            type="button"
                            onClick={() => selectPage('Review queue')}
                            className="mt-4 rounded-lg bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-indigo-700"
                          >
                            Open Review Queue
                          </button>
                        </div>
                      </>
                    );
                  })()}
                </section>
              )}
            </section>
          ) : (
            <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm sm:p-12">
              <div className="mx-auto max-w-lg text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                  {activePage === 'Disbursements' ? <Wallet size={25} /> : <FileText size={25} />}
                </div>
                <p className="mt-5 text-[10px] font-bold uppercase tracking-[0.16em] text-blue-600">
                  Lending workspace
                </p>
                <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
                  {activePage}
                </h2>
                <p className="mt-3 text-sm leading-6 text-slate-500">
                  {pageDescriptions[activePage] ?? 'Explore your lending operations workspace.'}
                </p>
                <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-left">
                  <p className="text-xs font-semibold text-amber-900">
                    Workspace under construction
                  </p>
                  <p className="mt-1 text-xs leading-5 text-amber-800">
                    This module has not yet been connected to backend data or implemented.
                  </p>
                </div>
                <button
                  onClick={() => selectPage('Overview')}
                  className="mt-6 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-blue-700"
                >
                  <LayoutDashboard size={15} /> Return to overview
                </button>
              </div>
            </section>
          )}
        </main>
      </div>
    </div >
  )
}

function MetricCard({
  title,
  value,
  change,
  detail,
  icon: Icon,
  iconClass,
  trend,
}: {
  title: string
  value: string
  change: string
  detail: string
  icon: typeof FileText
  iconClass: string
  trend: 'up' | 'warning'
}) {
  return (
    <section className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-medium text-slate-500">{title}</p>
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${iconClass}`}><Icon size={18} strokeWidth={1.8} /></div>
      </div>
      <p className="mt-4 text-[27px] font-bold tracking-tight text-slate-950">{value}</p>
      <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1">
        <span className={`inline-flex items-center gap-0.5 text-[10px] font-bold ${trend === 'warning' ? 'text-amber-600' : 'text-emerald-600'}`}>
          {trend === 'warning' ? <AlertTriangle size={12} /> : <ArrowUpRight size={13} />}
          {change}
        </span>
        <span className="text-[10px] text-slate-400">{detail}</span>
      </div>
    </section>
  )
}

function OutcomeRow({ color, label, value, count }: { color: string; label: string; value: string; count: string }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className={`h-2.5 w-2.5 shrink-0 rounded-sm ${color}`} />
      <span className="flex-1 text-[11px] text-slate-600">{label}</span>
      <span className="text-[11px] font-semibold text-slate-800">{value}</span>
      <span className="w-9 text-right text-[10px] text-slate-400">{count}</span>
    </div>
  )
}

function AlertItem({
  icon: Icon,
  iconClass,
  title,
  description,
  count,
  onClick,
}: {
  icon: typeof ClipboardCheck
  iconClass: string
  title: string
  description: string
  count: string
  onClick: () => void
}) {
  return (
    <button onClick={onClick} className="flex w-full items-start gap-3 rounded-lg p-2 text-left transition hover:bg-slate-50">
      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${iconClass}`}><Icon size={17} /></div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold text-slate-800">{title}</p>
        <p className="mt-1 text-[11px] leading-4 text-slate-500">{description}</p>
      </div>
      <span className="rounded-md bg-slate-100 px-1.5 py-1 text-[10px] font-semibold text-slate-600">{count}</span>
    </button>
  )
}

export default App