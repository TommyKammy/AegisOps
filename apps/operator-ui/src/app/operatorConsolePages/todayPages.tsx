import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import { Alert, Chip, Grid, Stack, Typography } from "@mui/material";
import { useMemo } from "react";
import {
  asRecord,
  asRecordArray,
  asString,
  AuditedRouteButton,
  EmptyState,
  ErrorState,
  formatLabel,
  LoadingState,
  PageFrame,
  SectionCard,
  statusTone,
  useOperatorRecord,
} from "./shared";

const TODAY_LANES = [
  {
    key: "priority",
    title: "Priority",
    subtitle: "Highest-priority AegisOps-owned records for review.",
  },
  {
    key: "stale_work",
    title: "Stale work",
    subtitle: "Authoritative lifecycle timestamps that need attention.",
  },
  {
    key: "pending_approvals",
    title: "Pending approvals",
    subtitle: "Approval-bound action reviews awaiting approver decision.",
  },
  {
    key: "degraded_sources",
    title: "Degraded sources",
    subtitle: "Subordinate source-health context that affects review confidence.",
  },
  {
    key: "reconciliation_mismatches",
    title: "Reconciliation mismatches",
    subtitle: "Directly linked reconciliation records that remain unresolved.",
  },
  {
    key: "evidence_gaps",
    title: "Evidence gaps",
    subtitle: "Required evidence, custody, or scope-binding records are absent.",
  },
  {
    key: "ai_suggested_focus",
    title: "AI-suggested focus",
    subtitle: "Advisory-only focus hints anchored to directly linked records.",
  },
] as const;

interface OperatorTaskCardDefinition {
  anchor: Record<string, unknown> | null;
  boundary: string;
  label: string;
  route: string;
  state: string | null;
  title: string;
}

function TodayProjectionUnavailable() {
  return (
    <PageFrame
      subtitle="The browser refuses to promote unverified Today projection output to workflow guidance."
      title="Today projection unavailable"
    >
      <Alert severity="error" variant="outlined">
        The backend projection was stale or malformed, so the browser refused
        to present it as current workflow guidance.
      </Alert>
    </PageFrame>
  );
}

function anchorRoute(anchor: Record<string, unknown> | null) {
  const family = asString(anchor?.family);
  const id = asString(anchor?.id);

  if (family === "alert" && id) {
    return `/operator/alerts/${encodeURIComponent(id)}`;
  }
  if (family === "case" && id) {
    return `/operator/cases/${encodeURIComponent(id)}`;
  }
  if (family === "action_review" && id) {
    return `/operator/action-review/${encodeURIComponent(id)}`;
  }
  if (family === "reconciliation") {
    return "/operator/reconciliation";
  }
  if (family === "source") {
    return "/operator/readiness";
  }

  return "/operator/queue";
}

function firstLaneItem(
  lanes: Record<string, unknown> | null,
  lane: (typeof TODAY_LANES)[number]["key"],
) {
  return asRecordArray(lanes?.[lane])[0] ?? null;
}

function taskCardFromLane({
  boundary,
  fallbackRoute,
  label,
  lanes,
  lane,
  title,
}: {
  boundary: string;
  fallbackRoute?: string;
  label: string;
  lanes: Record<string, unknown> | null;
  lane: (typeof TODAY_LANES)[number]["key"];
  title: string;
}): OperatorTaskCardDefinition {
  const item = firstLaneItem(lanes, lane);
  const anchor = asRecord(item?.authoritative_record);

  return {
    anchor,
    boundary,
    label,
    route: item ? anchorRoute(anchor) : (fallbackRoute ?? "/operator/queue"),
    state: asString(item?.state),
    title,
  };
}

function buildOperatorTaskCards(
  lanes: Record<string, unknown> | null,
): OperatorTaskCardDefinition[] {
  return [
    taskCardFromLane({
      boundary: "Open the anchored alert or case and use only reviewed casework surfaces.",
      label: "Review stale work",
      lane: "stale_work",
      lanes,
      title: "Review stale work",
    }),
    taskCardFromLane({
      boundary: "Open the existing action-review route; approval remains backend-authoritative.",
      label: "Inspect pending approvals",
      lane: "pending_approvals",
      lanes,
      title: "Inspect pending approvals",
    }),
    taskCardFromLane({
      boundary: "Open the anchored case; any evidence update must use reviewed write paths.",
      label: "Resolve evidence gaps",
      lane: "evidence_gaps",
      lanes,
      title: "Resolve evidence gaps",
    }),
    taskCardFromLane({
      boundary: "Open readiness; source-health posture stays subordinate context.",
      fallbackRoute: "/operator/readiness",
      label: "Check degraded sources",
      lane: "degraded_sources",
      lanes,
      title: "Check degraded sources",
    }),
    taskCardFromLane({
      boundary: "Open reconciliation visibility; mismatch state is not resolved by display.",
      fallbackRoute: "/operator/reconciliation",
      label: "Inspect mismatches",
      lane: "reconciliation_mismatches",
      lanes,
      title: "Inspect mismatches",
    }),
    {
      anchor: null,
      boundary:
        "Open the reviewed handoff view; handoff notes cannot close cases or override lifecycle state.",
      label: "Prepare handoff",
      route: "/operator/handoff",
      state: null,
      title: "Prepare handoff",
    },
  ];
}

function OperatorTaskCards({
  cards,
}: {
  cards: OperatorTaskCardDefinition[];
}) {
  return (
    <SectionCard
      subtitle="Repeated daily tasks are route launchers and guidance only; they do not add a write authority surface."
      title="Operator task cards"
    >
      <Stack spacing={2}>
        <Alert severity="info" variant="outlined">
          Task cards launch reviewed routes or bounded write surfaces; they
          cannot approve, execute, reconcile, close, or treat UI state as task
          completion truth.
        </Alert>
        <Grid container spacing={2}>
          {cards.map((card) => {
            const anchorFamily = asString(card.anchor?.family);
            const anchorId = asString(card.anchor?.id);

            return (
              <Grid key={card.label} size={{ xs: 12, md: 6, xl: 4 }}>
                <Stack
                  spacing={1.25}
                  sx={{
                    border: "1px solid",
                    borderColor: "divider",
                    borderRadius: 1,
                    height: "100%",
                    p: 1.5,
                  }}
                >
                  <Stack direction="row" flexWrap="wrap" gap={1}>
                    {card.state ? (
                      <Chip
                        color={statusTone(card.state)}
                        label={formatLabel(card.state)}
                        size="small"
                        variant="filled"
                      />
                    ) : null}
                    <Chip
                      color="warning"
                      label="State remains unresolved"
                      size="small"
                      variant="outlined"
                    />
                  </Stack>
                  <Typography variant="subtitle2">{card.title}</Typography>
                  <Typography color="text.secondary" variant="body2">
                    {card.boundary}
                  </Typography>
                  <Typography color="text.secondary" variant="caption">
                    Anchor: {anchorFamily ?? "daily_queue"}:
                    {anchorId ?? "reviewed_handoff"}
                  </Typography>
                  <Stack direction="row">
                    <AuditedRouteButton label={card.label} to={card.route}>
                      {card.label}
                    </AuditedRouteButton>
                  </Stack>
                </Stack>
              </Grid>
            );
          })}
        </Grid>
      </Stack>
    </SectionCard>
  );
}

function TodayLaneItem({
  item,
  lane,
}: {
  item: Record<string, unknown>;
  lane: string;
}) {
  const title = asString(item.title) ?? "Untitled Today item";
  const reason = asString(item.reason);
  const state = asString(item.state);
  const anchor = asRecord(item.authoritative_record);
  const anchorFamily = asString(anchor?.family);
  const anchorId = asString(anchor?.id);
  const advisoryOnly = lane === "ai_suggested_focus";

  return (
    <Stack
      spacing={1}
      sx={{
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        p: 1.5,
      }}
    >
      <Stack direction="row" flexWrap="wrap" gap={1}>
        {state ? (
          <Chip
            color={statusTone(state)}
            label={formatLabel(state)}
            size="small"
            variant={state === "normal" ? "outlined" : "filled"}
          />
        ) : null}
        {advisoryOnly ? (
          <Chip
            color="info"
            icon={<AutoAwesomeOutlinedIcon />}
            label="Advisory only"
            size="small"
            variant="outlined"
          />
        ) : null}
      </Stack>
      <Typography variant="subtitle2">{title}</Typography>
      {reason ? (
        <Typography color="text.secondary" variant="body2">
          {reason}
        </Typography>
      ) : null}
      <Typography color="text.secondary" variant="caption">
        Authoritative anchor: {anchorFamily ?? "record"}:{anchorId ?? "missing"}
      </Typography>
    </Stack>
  );
}

function TodayLane({
  items,
  lane,
  subtitle,
  title,
}: {
  items: Record<string, unknown>[];
  lane: string;
  subtitle: string;
  title: string;
}) {
  return (
    <SectionCard subtitle={subtitle} title={title}>
      {items.length > 0 ? (
        <Stack spacing={1.5}>
          {items.map((item) => (
            <TodayLaneItem
              item={item}
              key={asString(item.id) ?? JSON.stringify(item)}
              lane={lane}
            />
          ))}
        </Stack>
      ) : (
        <EmptyState
          message={`No ${title.toLowerCase()} items in the current backend projection.`}
        />
      )}
    </SectionCard>
  );
}

export function TodayPage() {
  const meta = useMemo(() => ({}), []);
  const { data, error, loading } = useOperatorRecord(
    "todayView",
    "current",
    meta,
  );
  const lanes = asRecord(data?.lanes);
  const totalItems = TODAY_LANES.reduce(
    (total, lane) => total + asRecordArray(lanes?.[lane.key]).length,
    0,
  );

  if (loading && !data) {
    return (
      <PageFrame
        subtitle="Daily SOC Workbench loads one backend-owned work-focus projection for the current operating day."
        title="Today"
      >
        <LoadingState label="Loading Today workbench" />
      </PageFrame>
    );
  }

  if (error) {
    return <TodayProjectionUnavailable />;
  }

  return (
    <PageFrame
      subtitle="Daily SOC Workbench. Today display state, ordering, badges, browser state, local cache, and AI focus hints remain operator guidance only; backend AegisOps records remain authoritative."
      title="Today"
    >
      {error ? <ErrorState error={error} /> : null}
      <Stack spacing={3}>
        <Typography variant="subtitle1">Daily SOC Workbench</Typography>
        <Alert severity="info" variant="outlined">
          AI focus hints are advisory-only and cannot approve, close, execute,
          reconcile, gate, release, or mutate work.
        </Alert>

        <OperatorTaskCards cards={buildOperatorTaskCards(lanes)} />

        {totalItems === 0 ? (
          <SectionCard
            subtitle="The backend returned an explicit empty Today projection."
            title="Today work focus"
          >
            <Stack spacing={1}>
              <EmptyState message="No eligible AegisOps work is in the Today projection." />
              <Typography color="text.secondary" variant="body2">
                Empty Today output is not production readiness, approval,
                execution, reconciliation, or closeout truth.
              </Typography>
            </Stack>
          </SectionCard>
        ) : null}

        <Grid container spacing={2}>
          {TODAY_LANES.map((lane) => (
            <Grid key={lane.key} size={{ xs: 12, lg: 6 }}>
              <TodayLane
                items={asRecordArray(lanes?.[lane.key])}
                lane={lane.key}
                subtitle={lane.subtitle}
                title={lane.title}
              />
            </Grid>
          ))}
        </Grid>
      </Stack>
    </PageFrame>
  );
}
