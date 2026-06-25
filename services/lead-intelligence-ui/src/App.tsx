import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  Building2,
  CheckCircle2,
  Coins,
  ExternalLink,
  Flame,
  Key,
  Lightbulb,
  Loader2,
  MapPin,
  Package,
  PauseCircle,
  Phone,
  Plus,
  PlayCircle,
  Search,
  ShoppingBag,
  Sparkles,
  TrendingUp,
  User,
  X,
} from "lucide-react";

type LeadStatus = "new" | "in_work" | "archived";
type LeadType = "office" | "warehouse" | "retail" | "production" | "residential";
type LeadCategory = "it" | "logistics" | "food" | "production" | "retail" | "finance" | "services";

type Lead = {
  id: number | string;
  company: string;
  inn: string;
  category: LeadCategory;
  categoryLabel: string;
  city: string;
  score: number;
  status: LeadStatus;
  manager?: string;
  reason: string;
  phone: string;
  site: string;
  requestType: LeadType;
  requestLabel: string;
  deal: "аренда" | "покупка";
  source: string;
  age: string;
  createdAt: string;
  signalTitle?: string;
  signalText?: string;
  signalUrl?: string;
  signalDate?: string;
};

type Scenario = {
  id: string;
  title: string;
  description: string;
  meta: string;
  icon: string;
  isActive: boolean;
};

type FunnelItem = {
  name: string;
  value: number;
  color: string;
};

type Integration = {
  name: string;
  state: string;
  online: boolean;
};

type Metrics = {
  new24h: number;
  hot: number;
  inWork: number;
  offerConversion: string;
  hotShare: string;
};

type Scheduler = {
  enabled: boolean;
  intervalMinutes: number;
  lookbackDays: number;
  activeScenarios: number;
  running: boolean;
  lastStartedAt: string;
  lastFinishedAt: string;
  lastCreated: number;
  lastError: string;
};

type Bootstrap = {
  leads: Lead[];
  scenarios: Scenario[];
  metrics: Metrics;
  funnel: FunnelItem[];
  integrations: Integration[];
  scheduler: Scheduler;
};

type ScenarioTab = "signals" | "direct";

const directScenarioIds = new Set(["direct-warehouse", "direct-commercial", "direct-residential"]);

const iconMap = {
  Building2,
  Package,
  ShoppingBag,
  TrendingUp,
  Key,
  Coins,
  Search,
};

const apiPath = (path: string) => `${import.meta.env.BASE_URL}${path.replace(/^\//, "")}`;

const scoreClass = (score: number) => {
  if (score >= 80) return "text-emerald-600 dark:text-emerald-500";
  if (score >= 60) return "text-amber-600 dark:text-amber-500";
  return "text-zinc-500 dark:text-zinc-400";
};

const avatarClass: Record<LeadCategory, string> = {
  it: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  logistics: "bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300",
  food: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  production: "bg-stone-200 text-stone-700 dark:bg-stone-800 dark:text-stone-200",
  retail: "bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300",
  finance: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  services: "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
};

const badgeClass: Record<LeadCategory, string> = {
  it: "bg-blue-50 text-blue-700 ring-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:ring-blue-900",
  logistics: "bg-cyan-50 text-cyan-700 ring-cyan-200 dark:bg-cyan-950 dark:text-cyan-300 dark:ring-cyan-900",
  food: "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:ring-amber-900",
  production: "bg-stone-100 text-stone-700 ring-stone-200 dark:bg-stone-900 dark:text-stone-300 dark:ring-stone-800",
  retail: "bg-violet-50 text-violet-700 ring-violet-200 dark:bg-violet-950 dark:text-violet-300 dark:ring-violet-900",
  finance: "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:ring-emerald-900",
  services: "bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-950 dark:text-rose-300 dark:ring-rose-900",
};

const requestLabel: Record<LeadType, string> = {
  office: "Офис",
  warehouse: "Склад",
  retail: "Торговля",
  production: "Производство",
  residential: "Жилая",
};

const types = ["Все типы", "Офис", "Склад", "Торговля", "Производство", "Жилая"];

const schedulerIntervalLabel = (minutes: number) => {
  if (minutes < 60) return `${minutes} мин`;
  const hours = minutes / 60;
  return Number.isInteger(hours) ? `${hours} ч` : `${minutes} мин`;
};

function initials(name: string) {
  return name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function Toast({ message }: { message: string }) {
  if (!message) return null;

  return (
    <div className="fixed right-6 top-20 z-50 rounded-lg border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-900 shadow-sm dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100">
      {message}
    </div>
  );
}

function MetricCard({ label, value, delta, tone }: { label: string; value: string; delta: string; tone: string }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="text-xs text-zinc-500 dark:text-zinc-400">{label}</div>
      <div className="mt-3 text-2xl font-medium tracking-tight text-zinc-950 dark:text-zinc-50">{value}</div>
      <div className={`mt-2 text-xs ${tone}`}>{delta}</div>
    </div>
  );
}

function Pill({ active, children, onClick }: { active: boolean; children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      className={`inline-flex h-8 items-center gap-1.5 rounded-lg px-3 text-sm transition focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-zinc-950 ${
        active
          ? "bg-blue-600 text-white"
          : "border border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-300 dark:hover:bg-zinc-900"
      }`}
      type="button"
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function SmallBadge({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`inline-flex h-6 items-center rounded-md px-2 text-xs ring-1 ring-inset ${className}`}>
      {children}
    </span>
  );
}

function LeadCard({ lead, onAction }: { lead: Lead; onAction: (lead: Lead, action: string, message: string) => void }) {
  return (
    <article className="rounded-xl border border-zinc-200 bg-white transition hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:bg-zinc-900">
      <div className="flex flex-col gap-5 p-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex min-w-0 gap-3">
          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-sm font-medium ${avatarClass[lead.category]}`}>
            {initials(lead.company)}
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="truncate text-[15px] font-medium text-zinc-950 dark:text-zinc-50">{lead.company}</h3>
              <SmallBadge className={badgeClass[lead.category]}>{lead.categoryLabel}</SmallBadge>
              <SmallBadge className="bg-zinc-50 text-zinc-600 ring-zinc-200 dark:bg-zinc-900 dark:text-zinc-300 dark:ring-zinc-800">{lead.city}</SmallBadge>
              {lead.status === "in_work" && lead.manager && (
                <SmallBadge className="bg-blue-50 text-blue-700 ring-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:ring-blue-900">
                  в работе · {lead.manager}
                </SmallBadge>
              )}
            </div>
            <div className="mt-2 flex items-start gap-2 text-sm text-zinc-600 dark:text-zinc-400">
              <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" aria-hidden />
              <p className="line-clamp-2">{lead.reason}</p>
            </div>
            {lead.signalTitle && (
              <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
                <div className="font-medium">Сигнал: {lead.signalTitle}</div>
                <div className="mt-1 text-xs text-amber-800 dark:text-amber-200">
                  {lead.signalDate ? `Дата: ${lead.signalDate.slice(0, 10)}` : "Дата не указана"}
                  {lead.signalUrl && (
                    <a className="ml-3 inline-flex items-center gap-1 underline underline-offset-2" href={lead.signalUrl} target="_blank" rel="noreferrer">
                      источник <ExternalLink className="h-3 w-3" aria-hidden />
                    </a>
                  )}
                </div>
              </div>
            )}
            <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-xs text-zinc-500 dark:text-zinc-400">
              {lead.phone && <span className="inline-flex items-center gap-1.5"><Phone className="h-3.5 w-3.5" aria-hidden />{lead.phone}</span>}
              {lead.site && <span className="inline-flex items-center gap-1.5"><ExternalLink className="h-3.5 w-3.5" aria-hidden />{lead.site}</span>}
              <span className="inline-flex items-center gap-1.5"><Building2 className="h-3.5 w-3.5" aria-hidden />{lead.requestLabel} · {lead.deal}</span>
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-end justify-between gap-5 lg:block lg:text-right">
          <div>
            <div className={`text-[22px] font-medium leading-none ${scoreClass(lead.score)}`}>
              {lead.score}<span className="text-sm text-zinc-400 dark:text-zinc-500">/100</span>
            </div>
            <div className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">{lead.source} · {lead.age}</div>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-zinc-200 px-4 py-3 dark:border-zinc-800">
        <button className="rounded-lg border border-zinc-200 px-2.5 py-1.5 text-xs text-zinc-700 transition hover:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-950" type="button" onClick={() => onAction(lead, "work", `${lead.company}: добавлено в работу`)}>
          В работу
        </button>
        <button className="rounded-lg border border-zinc-200 px-2.5 py-1.5 text-xs text-zinc-700 transition hover:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-950" type="button" onClick={() => onAction(lead, "match", `${lead.company}: подбор объекта запущен`)}>
          Подобрать объект
        </button>
        <button className="rounded-lg border border-zinc-200 px-2.5 py-1.5 text-xs text-zinc-700 transition hover:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-950" type="button" onClick={() => onAction(lead, "offer", `${lead.company}: офер подготовлен`)}>
          Офер
        </button>
        <button className="ml-auto inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 px-2.5 py-1.5 text-xs text-zinc-500 transition hover:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-950" type="button" onClick={() => onAction(lead, "trash", `${lead.company}: помечено как мусор`)}>
          <X className="h-3.5 w-3.5" aria-hidden />
          Мусор
        </button>
      </div>
    </article>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"all" | "hot" | LeadStatus>("all");
  const [city, setCity] = useState("Все города");
  const [type, setType] = useState("Все типы");
  const [sort, setSort] = useState("score");
  const [toast, setToast] = useState("");
  const [scenarioTab, setScenarioTab] = useState<ScenarioTab>("signals");
  const [runningGroup, setRunningGroup] = useState(false);
  const [groupProgress, setGroupProgress] = useState("");
  const [leads, setLeads] = useState<Lead[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [funnel, setFunnel] = useState<FunnelItem[]>([]);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [scheduler, setScheduler] = useState<Scheduler>({
    enabled: false,
    intervalMinutes: 180,
    lookbackDays: 1,
    activeScenarios: 0,
    running: false,
    lastStartedAt: "",
    lastFinishedAt: "",
    lastCreated: 0,
    lastError: "",
  });
  const [metrics, setMetrics] = useState<Metrics>({
    new24h: 0,
    hot: 0,
    inWork: 0,
    offerConversion: "0%",
    hotShare: "0% от потока",
  });
  const [loading, setLoading] = useState(true);

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2200);
  };

  const applyBootstrap = (data: Bootstrap) => {
    setLeads(data.leads);
    setScenarios(data.scenarios);
    setMetrics(data.metrics);
    setFunnel(data.funnel);
    setIntegrations(data.integrations);
    if (data.scheduler) setScheduler(data.scheduler);
  };

  useEffect(() => {
    fetch(apiPath("api/bootstrap"))
      .then((response) => {
        if (!response.ok) throw new Error("API недоступен");
        return response.json() as Promise<Bootstrap>;
      })
      .then(applyBootstrap)
      .catch(() => showToast("API недоступен, данные не загружены"))
      .finally(() => setLoading(false));
  }, []);

  const runScenario = async (scenario: Scenario) => {
    try {
      const response = await fetch(apiPath(`api/scenarios/${scenario.id}/run`), { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "scenario failed");
      applyBootstrap(data.bootstrap);
      showToast(`Сбор по сценарию «${scenario.title}» запущен`);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Не удалось запустить сценарий");
    }
  };

  const toggleScenario = async (scenario: Scenario, active: boolean) => {
    try {
      const response = await fetch(apiPath(`api/scenarios/${scenario.id}/toggle`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "toggle failed");
      applyBootstrap(data.bootstrap);
      showToast(active ? `Сценарий «${scenario.title}» включен` : `Сценарий «${scenario.title}» поставлен на паузу`);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Не удалось изменить сценарий");
    }
  };

  const setScenarioGroupActive = async (active: boolean) => {
    const queue = visibleScenarios;
    if (queue.length === 0) {
      showToast("В этой вкладке нет сценариев");
      return;
    }
    setRunningGroup(true);
    setGroupProgress(`0/${queue.length}`);
    try {
      for (const [index, scenario] of queue.entries()) {
        setGroupProgress(`${index + 1}/${queue.length}`);
        if (scenario.isActive === active) continue;
        const response = await fetch(apiPath(`api/scenarios/${scenario.id}/toggle`), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ active }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || `Не удалось изменить «${scenario.title}»`);
        applyBootstrap(data.bootstrap);
      }
      showToast(`${scenarioTab === "direct" ? "Прямые запросы" : "Сценарии сигналов"}: автосбор ${active ? "включен" : "выключен"}`);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Не удалось изменить группу сценариев");
    } finally {
      setRunningGroup(false);
      setGroupProgress("");
    }
  };

  const leadAction = async (lead: Lead, action: string, message: string) => {
    try {
      const response = await fetch(apiPath(`api/leads/${lead.id}/action`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      if (!response.ok) throw new Error("action failed");
      const data = await response.json();
      applyBootstrap(data.bootstrap);
    } catch {
      showToast("Действие не сохранено: API недоступен");
      return;
    }
    showToast(message);
  };

  const filteredLeads = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const result = leads.filter((lead) => {
      const matchesSearch = !normalized || [lead.company, lead.inn, lead.site].some((value) => value.toLowerCase().includes(normalized));
      const matchesStatus =
        status === "all" ||
        (status === "hot" && lead.score >= 80) ||
        lead.status === status;
      const matchesCity = city === "Все города" || lead.city === city;
      const matchesType = type === "Все типы" || requestLabel[lead.requestType] === type;

      return matchesSearch && matchesStatus && matchesCity && matchesType;
    });

    return [...result].sort((a, b) => {
      if (sort === "date") return b.createdAt.localeCompare(a.createdAt);
      if (sort === "city") return a.city.localeCompare(b.city);
      return b.score - a.score;
    });
  }, [city, leads, query, sort, status, type]);

  const availableCities = useMemo(() => ["Все города", ...Array.from(new Set(leads.map((lead) => lead.city)))], [leads]);
  const visibleScenarios = useMemo(
    () => scenarios.filter((scenario) => directScenarioIds.has(scenario.id) === (scenarioTab === "direct")),
    [scenarioTab, scenarios],
  );

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-950 dark:bg-zinc-950 dark:text-zinc-50">
      <Toast message={toast} />

      <header className="sticky top-0 z-40 border-b border-zinc-200 bg-white/90 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/90">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-5">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-white dark:bg-white dark:text-zinc-950">
              <Sparkles className="h-4 w-4" aria-hidden />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-medium">Lead Intelligence</div>
              <div className="text-xs text-zinc-500 dark:text-zinc-400">/intelligence/</div>
            </div>
          </div>

          <label className="relative mx-auto hidden w-full max-w-xl md:block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" aria-hidden />
            <input
              className="h-10 w-full rounded-lg border border-zinc-200 bg-zinc-50 pl-9 pr-3 text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-blue-600 focus:ring-2 focus:ring-blue-100 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100 dark:focus:border-blue-500 dark:focus:ring-blue-950"
              placeholder="Поиск компании, ИНН, сайта…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>

          <div className="ml-auto flex items-center gap-3">
            <div className="hidden items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400 sm:flex">
              <span className={`h-2 w-2 rounded-full ${loading ? "bg-amber-500" : "bg-emerald-500"}`} />
              {loading ? "загрузка данных" : "коллектор online"}
            </div>
            <button className="inline-flex h-10 items-center gap-2 rounded-lg bg-blue-600 px-3 text-sm font-medium text-white transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-zinc-950" type="button" onClick={() => showToast("Новый поиск запущен")}>
              <Plus className="h-4 w-4" aria-hidden />
              Новый поиск
            </button>
            <button className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-200 bg-white text-zinc-600 transition hover:bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-300 dark:hover:bg-zinc-900" type="button" aria-label="Профиль пользователя">
              <User className="h-4 w-4" aria-hidden />
            </button>
          </div>
        </div>

        <div className="border-t border-zinc-200 px-5 py-3 dark:border-zinc-800 md:hidden">
          <label className="relative block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" aria-hidden />
            <input
              className="h-10 w-full rounded-lg border border-zinc-200 bg-zinc-50 pl-9 pr-3 text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 dark:border-zinc-800 dark:bg-zinc-900 dark:focus:ring-blue-950"
              placeholder="Поиск компании, ИНН, сайта…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-5 py-6">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Новых сигналов" value={String(metrics.new24h)} delta="после фильтра качества" tone="text-emerald-600" />
          <MetricCard label="Score 80+" value={String(metrics.hot)} delta={metrics.hotShare} tone="text-blue-600" />
          <MetricCard label="В работе" value={String(metrics.inWork)} delta="у менеджеров" tone="text-amber-600" />
          <MetricCard label="Конверсия в офер" value={metrics.offerConversion} delta="+1.8 п.п. за неделю" tone="text-emerald-600" />
        </section>

        <section className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
          <div className="border-b border-zinc-200 p-5 dark:border-zinc-800">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div className="min-w-0">
              <h1 className="text-[22px] font-medium tracking-tight">Активность поиска</h1>
              <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                Управление двумя независимыми направлениями: косвенные B2B-сигналы и прямые запросы рынка.
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
                <SmallBadge className={scheduler.enabled ? "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:ring-emerald-900" : "bg-zinc-100 text-zinc-500 ring-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:ring-zinc-700"}>
                  {scheduler.running ? "планировщик выполняет сбор" : scheduler.enabled ? "планировщик online" : "планировщик выключен"}
                </SmallBadge>
                <span>активных сценариев: {scheduler.activeScenarios}</span>
                <span>проверка каждые {schedulerIntervalLabel(scheduler.intervalMinutes)}</span>
                {scheduler.lastFinishedAt && <span>последний запуск: {scheduler.lastFinishedAt.slice(0, 16)}</span>}
                {scheduler.lastError && <span className="text-amber-600 dark:text-amber-400">последняя ошибка: {scheduler.lastError}</span>}
              </div>
            </div>
            <div className="flex w-full flex-col gap-3 xl:w-auto xl:items-end">
              <div className="grid h-10 w-full grid-cols-2 rounded-lg border border-zinc-200 bg-zinc-100 p-1 dark:border-zinc-800 dark:bg-zinc-900 xl:w-[360px]">
                <button
                  className={`flex h-8 items-center justify-center rounded-md px-2 text-sm transition focus:outline-none focus:ring-2 focus:ring-blue-500 ${scenarioTab === "signals" ? "bg-white text-zinc-950 shadow-sm dark:bg-zinc-950 dark:text-zinc-50" : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"}`}
                  type="button"
                  onClick={() => setScenarioTab("signals")}
                >
                  Сценарии сигналов
                </button>
                <button
                  className={`flex h-8 items-center justify-center rounded-md px-2 text-sm transition focus:outline-none focus:ring-2 focus:ring-blue-500 ${scenarioTab === "direct" ? "bg-white text-zinc-950 shadow-sm dark:bg-zinc-950 dark:text-zinc-50" : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"}`}
                  type="button"
                  onClick={() => setScenarioTab("direct")}
                >
                  Прямые запросы
                </button>
              </div>
              <div className="grid w-full grid-cols-2 gap-2 xl:w-[360px]">
                <button
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-emerald-600 px-3 text-sm font-medium text-white transition hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:cursor-wait disabled:bg-zinc-300 disabled:text-zinc-500 dark:focus:ring-offset-zinc-950 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-500"
                  type="button"
                  onClick={() => setScenarioGroupActive(true)}
                  disabled={runningGroup || visibleScenarios.length === 0}
                >
                  {runningGroup ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <PlayCircle className="h-4 w-4" aria-hidden />}
                  {runningGroup ? groupProgress : "Включить все"}
                </button>
                <button
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-rose-600 px-3 text-sm font-medium text-white transition hover:bg-rose-700 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 disabled:cursor-wait disabled:bg-zinc-300 disabled:text-zinc-500 dark:focus:ring-offset-zinc-950 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-500"
                  type="button"
                  onClick={() => setScenarioGroupActive(false)}
                  disabled={runningGroup || visibleScenarios.length === 0}
                >
                  {runningGroup ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <PauseCircle className="h-4 w-4" aria-hidden />}
                  Выключить все
                </button>
              </div>
            </div>
            </div>
          </div>
          <div className="flex min-h-[52px] items-start gap-3 border-b border-zinc-200 bg-zinc-50 px-5 py-3 text-sm text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
            <Activity className="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" aria-hidden />
            <p>
              {scenarioTab === "direct"
                ? `Собрать сейчас: разовый поиск по текущей выдаче прямых фраз. Включить автосбор: только этот сценарий попадет в фоновую проверку каждые ${schedulerIntervalLabel(scheduler.intervalMinutes)} за последние ${scheduler.lookbackDays} дн.; повторные лиды отсекаются дедупликацией.`
                : `Собрать сейчас: ручная проверка за последние 30 дней по публичным сигналам. Включить автосбор: только этот сценарий попадет в фоновую проверку каждые ${schedulerIntervalLabel(scheduler.intervalMinutes)} за последние ${scheduler.lookbackDays} дн.; старые дубли повторно не добавляются.`}
            </p>
          </div>
          <div className="grid gap-3 p-5 md:grid-cols-2 xl:grid-cols-3">
            {visibleScenarios.map((scenario) => {
              const Icon = iconMap[scenario.icon as keyof typeof iconMap] || Building2;
              return (
                <div
                  className={`rounded-xl border p-4 transition ${
                    scenario.isActive
                      ? "border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
                      : "border-zinc-200 bg-zinc-50 opacity-75 dark:border-zinc-800 dark:bg-zinc-900"
                  }`}
                  key={scenario.id}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zinc-200 text-zinc-700 dark:border-zinc-800 dark:text-zinc-300">
                      <Icon className="h-4 w-4" aria-hidden />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="text-base font-medium">{scenario.title}</h2>
                        <SmallBadge className={scenario.isActive ? "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:ring-emerald-900" : "bg-zinc-100 text-zinc-500 ring-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:ring-zinc-700"}>
                          {scenario.isActive ? "автосбор активен" : "автосбор на паузе"}
                        </SmallBadge>
                      </div>
                      <p className="mt-1 truncate text-sm text-zinc-500 dark:text-zinc-400">{scenario.description}</p>
                      <p className="mt-3 text-xs text-zinc-400 dark:text-zinc-500">{scenario.meta}</p>
                    </div>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <button
                      className="inline-flex h-9 flex-1 items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-zinc-300 disabled:text-zinc-500 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-500"
                      type="button"
                      onClick={() => runScenario(scenario)}
                      title="Ручной поиск прямо сейчас. Для сценариев сигналов период 30 дней; для прямых запросов используется текущая поисковая выдача."
                    >
                      <PlayCircle className="h-4 w-4" aria-hidden />
                      Собрать сейчас
                    </button>
                    <button
                      className="inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-zinc-200 bg-white px-3 text-sm text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-300 dark:hover:bg-zinc-900"
                      type="button"
                      onClick={() => toggleScenario(scenario, !scenario.isActive)}
                      title={`Включает или выключает сценарий в фоновом расписании: каждые ${schedulerIntervalLabel(scheduler.intervalMinutes)}.`}
                    >
                      {scenario.isActive ? <PauseCircle className="h-4 w-4" aria-hidden /> : <PlayCircle className="h-4 w-4" aria-hidden />}
                      {scenario.isActive ? "Пауза автосбора" : "Включить автосбор"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="rounded-xl border border-zinc-200 bg-zinc-100 p-3 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-wrap gap-2">
              <Pill active={status === "all"} onClick={() => setStatus("all")}>Все</Pill>
              <Pill active={status === "hot"} onClick={() => setStatus("hot")}><Flame className="h-3.5 w-3.5" aria-hidden />Горячие 80+</Pill>
              <Pill active={status === "new"} onClick={() => setStatus("new")}>Новые</Pill>
              <Pill active={status === "in_work"} onClick={() => setStatus("in_work")}>В работе</Pill>
              <Pill active={status === "archived"} onClick={() => setStatus("archived")}>Архив</Pill>
            </div>

            <div className="grid gap-2 sm:grid-cols-2">
              <select className="h-9 rounded-lg border border-zinc-200 bg-white px-3 text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 dark:border-zinc-800 dark:bg-zinc-950 dark:focus:ring-blue-950" value={city} onChange={(event) => setCity(event.target.value)} aria-label="Фильтр по городу">
                {availableCities.map((item) => <option key={item}>{item}</option>)}
              </select>
              <select className="h-9 rounded-lg border border-zinc-200 bg-white px-3 text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 dark:border-zinc-800 dark:bg-zinc-950 dark:focus:ring-blue-950" value={type} onChange={(event) => setType(event.target.value)} aria-label="Фильтр по типу">
                {types.map((item) => <option key={item}>{item}</option>)}
              </select>
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-medium">Очередь сигналов · {filteredLeads.length} показано</h2>
              <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">Обычная вакансия комплектовщика не считается сигналом без признаков роста или повторяемости.</p>
            </div>
            <select className="h-9 rounded-lg border border-zinc-200 bg-white px-3 text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 dark:border-zinc-800 dark:bg-zinc-950 dark:focus:ring-blue-950" value={sort} onChange={(event) => setSort(event.target.value)} aria-label="Сортировка сигналов">
              <option value="score">score ↓</option>
              <option value="date">дата ↓</option>
              <option value="city">город</option>
            </select>
          </div>

          <div className="space-y-2.5">
            {filteredLeads.map((lead) => (
              <LeadCard key={lead.id} lead={lead} onAction={leadAction} />
            ))}
            {filteredLeads.length === 0 && (
              <div className="rounded-xl border border-dashed border-zinc-300 p-10 text-center text-sm text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
                По текущим фильтрам сигналов нет.
              </div>
            )}
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
          <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
            <div className="mb-5">
              <h2 className="text-lg font-medium">Воронка за неделю</h2>
              <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">Путь от найденного сигнала до подготовленного офера.</p>
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnel} margin={{ top: 20, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" vertical={false} />
                  <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fill: "#71717a", fontSize: 12 }} />
                  <YAxis tickLine={false} axisLine={false} tick={{ fill: "#a1a1aa", fontSize: 12 }} />
                  <Tooltip cursor={{ fill: "#f4f4f5" }} />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]} label={{ position: "top", fill: "#52525b", fontSize: 12 }}>
                    {funnel.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="text-lg font-medium">Источники и интеграции</h2>
            <div className="mt-5 space-y-4">
              {integrations.map((integration) => (
                <div className="flex items-center justify-between gap-4 border-b border-zinc-100 pb-4 last:border-0 last:pb-0 dark:border-zinc-800" key={integration.name}>
                  <div className="flex items-center gap-3">
                    <span className={`h-2 w-2 rounded-full ${integration.online ? "bg-emerald-500" : "bg-zinc-400"}`} />
                    <span className="text-sm text-zinc-800 dark:text-zinc-200">{integration.name}</span>
                  </div>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">{integration.state}</span>
                </div>
              ))}
            </div>
            <div className="mt-5 rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
              <CheckCircle2 className="mb-3 h-4 w-4 text-emerald-600" aria-hidden />
              Сервис собирает только открытые B2B-источники и передает спорные контакты на ручное подтверждение.
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
