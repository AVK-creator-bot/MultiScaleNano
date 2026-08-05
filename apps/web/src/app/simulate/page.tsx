"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Atom,
  CheckCircle2,
  Download,
  Loader2,
  Play,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { HelpTip, StepHeader } from "@/components/HelpTip";
import { ResultsPanel } from "@/components/ResultsPanel";
import { StructurePanel } from "@/components/StructurePanel";
import {
  createDesign,
  checkHealth,
  fetchLipidPresets,
  fetchModules,
  fetchTemplates,
  getRun,
  getRunResults,
  lipidTotalPct,
  LIPID_PRESET_LABELS,
  normalizeLipids,
  resolveDrug,
  startRun,
  exportRunUrl,
  LOADING_LIMITS,
  STRUCTURE_HINTS,
  type DrugPayload,
  type LipidComponent,
  type HealthStatus,
  type ModuleSpec,
  type NanocarrierDesign,
  type ResolvedDrug,
  type RunResults,
  type SimulationRun,
} from "@/lib/api";
import {
  EXAMPLE_PAYLOADS,
  friendlyError,
  STATUS_LABELS,
  WIZARD_STEPS,
} from "@/lib/wizard-copy";

export default function SimulatePage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen flex-col items-center justify-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-[var(--primary)]" />
          <p className="text-sm text-[var(--muted)]">Loading simulator…</p>
        </div>
      }
    >
      <SimulateWizard />
    </Suspense>
  );
}

function SimulateWizard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [step, setStep] = useState(0);
  const [design, setDesign] = useState<NanocarrierDesign | null>(null);
  const [lipidPresetKey, setLipidPresetKey] = useState("mrna_sm102");
  const [modules, setModules] = useState<ModuleSpec[]>([]);
  const [enabledModules, setEnabledModules] = useState<string[]>([]);
  const [simulationMode, setSimulationMode] = useState("standard_md");
  const [run, setRun] = useState<SimulationRun | null>(null);
  const [results, setResults] = useState<RunResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [structureValidated, setStructureValidated] = useState(false);
  const [validating, setValidating] = useState(false);
  const [resolvedDrug, setResolvedDrug] = useState<ResolvedDrug | null>(null);
  const [lipidPresets, setLipidPresets] = useState<Record<string, LipidComponent[]>>({});
  const [runError, setRunError] = useState<string | null>(null);
  const [initError, setInitError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateStructure = useCallback(async (drug: DrugPayload) => {
    setValidating(true);
    setValidationError(null);
    setStructureValidated(false);
    setResolvedDrug(null);
    try {
      const result = await resolveDrug(drug);
      setResolvedDrug(result.resolved);
      setStructureValidated(true);
      return true;
    } catch (e) {
      setValidationError(
        friendlyError(e instanceof Error ? e.message : "Could not validate structure")
      );
      return false;
    } finally {
      setValidating(false);
    }
  }, []);

  const applyExample = useCallback(
    async (exampleId: string) => {
      const example = EXAMPLE_PAYLOADS.find((e) => e.id === exampleId);
      if (!example || !design) return;
      const lipids = lipidPresets[example.presetKey] || design.lipids;
      const newDesign: NanocarrierDesign = {
        ...design,
        name: example.name,
        drug: { ...design.drug, ...example.drug },
        lipids,
      };
      setDesign(newDesign);
      setLipidPresetKey(example.presetKey);
      await validateStructure(newDesign.drug);
    },
    [design, lipidPresets, validateStructure]
  );

  useEffect(() => {
    async function init() {
      try {
        const healthStatus = await checkHealth();
        setHealth(healthStatus);

        const runParam = searchParams.get("run");
        if (runParam) {
          const existing = await getRun(runParam);
          setRun(existing);
          setStep(4);
          if (existing.status === "completed" || existing.status === "failed") {
            const res = await getRunResults(runParam);
            setResults(res);
          }
        }

        const [tmpl, mods, presets] = await Promise.all([
          fetchTemplates(),
          fetchModules(),
          fetchLipidPresets(),
        ]);
        setDesign(tmpl[0].design);
        setLipidPresets(presets);
        setModules(mods);
        setEnabledModules(mods.filter((m) => m.enabled_by_default).map((m) => m.name));
        if (!runParam) {
          await validateStructure(tmpl[0].design.drug);
        }
      } catch (e) {
        setInitError(friendlyError(e instanceof Error ? e.message : "Connection failed"));
      } finally {
        setLoading(false);
      }
    }
    init();
  }, [validateStructure, searchParams]);

  const handleStartRun = useCallback(async () => {
    if (!design || !structureValidated) return;
    setRunError(null);
    try {
      const saved = await createDesign(design);
      const newRun = await startRun(saved.id!, enabledModules, simulationMode);
      setRun(newRun);
      setStep(4);
      router.replace(`/simulate?run=${newRun.id}`);
    } catch (e) {
      setRunError(friendlyError(e instanceof Error ? e.message : "Failed to start simulation"));
    }
  }, [design, enabledModules, simulationMode, structureValidated, router]);

  const handleReset = () => {
    setStep(0);
    setRun(null);
    setResults(null);
    setRunError(null);
    router.replace("/simulate");
  };

  useEffect(() => {
    if (!run || run.status === "completed" || run.status === "failed") return;
    const interval = setInterval(async () => {
      try {
        const updated = await getRun(run.id);
        setRun(updated);
        if (updated.status === "completed") {
          const res = await getRunResults(run.id);
          setResults(res);
        }
        if (updated.status === "failed") {
          const failedMod = updated.modules.find((m) => m.status === "failed" && m.error);
          if (failedMod?.error) setRunError(friendlyError(failedMod.error));
        }
      } catch {
        setRunError("Lost connection while polling — retrying…");
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [run]);

  useEffect(() => {
    if (run?.status === "completed" && !results) {
      getRunResults(run.id).then(setResults);
    }
  }, [run, results]);

  const runProgress = run
    ? Math.round(
        (run.modules.filter((m) => m.status === "completed").length / run.modules.length) * 100
      )
    : 0;

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--primary)]" />
        <p className="text-sm text-[var(--muted)]">Loading simulator…</p>
      </div>
    );
  }

  if (initError || !design) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-5 px-6 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--surface-elevated)]">
          <Atom className="h-7 w-7 text-[var(--primary)]" />
        </div>
        <div>
          <h1 className="text-xl font-semibold">Simulator not running</h1>
          <p className="mt-2 max-w-md text-sm text-[var(--muted)]">
            {initError ||
              "The API and web app need to be started on this machine before you can simulate."}
          </p>
        </div>
        <div className="max-w-md rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 text-left text-xs text-[var(--muted)]">
          <p className="font-medium text-white">Start locally (PowerShell)</p>
          <pre className="mt-2 overflow-x-auto rounded bg-[var(--surface-elevated)] p-3 font-mono text-[11px] text-white">
            cd C:\Users\aryak\Projects\MultiscaleNano{"\n"}.\scripts\start-local.ps1
          </pre>
          <p className="mt-3 font-medium text-white">Or with Docker</p>
          <pre className="mt-2 overflow-x-auto rounded bg-[var(--surface-elevated)] p-3 font-mono text-[11px] text-white">
            docker compose up --build
          </pre>
          <p className="mt-3">Then open http://localhost:3000/simulate</p>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="inline-flex items-center gap-2 rounded-lg bg-[var(--primary)] px-5 py-2.5 text-sm text-white"
        >
          <RefreshCw className="h-4 w-4" />
          Retry connection
        </button>
      </div>
    );
  }

  const currentStep = WIZARD_STEPS[step];

  return (
    <div className="min-h-screen pb-16">
      <header className="border-b border-[var(--border)] bg-[var(--surface)]/80 px-6 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-[var(--muted)] hover:text-white" aria-label="Home">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <Atom className="h-5 w-5 text-[var(--primary)]" />
            <span className="font-semibold">Simulation wizard</span>
          </div>
          {health?.simulations_ready ? (
            <span className="hidden items-center gap-1.5 text-xs text-[var(--success)] sm:flex">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Ready to simulate
            </span>
          ) : health ? (
            <span className="hidden text-xs text-amber-400 sm:block">
              Simulations unavailable
            </span>
          ) : null}
        </div>
      </header>

      {/* Progress steps — mobile friendly */}
      <div className="mx-auto max-w-3xl px-6 py-6">
        <div className="mb-2 flex justify-between text-xs text-[var(--muted)]">
          <span>
            Step {step + 1} of {WIZARD_STEPS.length}
          </span>
          <span>{currentStep.label}</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-[var(--surface-elevated)]">
          <div
            className="h-full rounded-full bg-[var(--primary)] transition-all duration-300"
            style={{ width: `${((step + 1) / WIZARD_STEPS.length) * 100}%` }}
          />
        </div>
        <div className="mt-4 hidden justify-between sm:flex">
          {WIZARD_STEPS.map((s, i) => (
            <span
              key={s.id}
              className={`text-xs ${i <= step ? "text-white" : "text-[var(--muted)]"}`}
            >
              {i < step ? "✓ " : ""}
              {s.label}
            </span>
          ))}
        </div>
      </div>

      <main className="mx-auto max-w-3xl px-6">
        {health && !health.simulations_ready && (
          <div className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            {health.message}
          </div>
        )}
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-8">
          <StepHeader title={currentStep.title} subtitle={currentStep.subtitle} />

          {step === 0 && (
            <div className="space-y-5">
              <HelpTip>
                <strong>New here?</strong> Click an example below — we&apos;ll fill everything in
                and verify your drug structure automatically.
              </HelpTip>

              <div className="grid gap-3 sm:grid-cols-2">
                {EXAMPLE_PAYLOADS.map((ex) => (
                  <button
                    key={ex.id}
                    type="button"
                    onClick={() => applyExample(ex.id)}
                    disabled={validating}
                    className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-4 text-left transition-colors hover:border-[var(--primary)]/50 disabled:opacity-50"
                  >
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-[var(--primary)]" />
                      <span className="font-medium">{ex.name}</span>
                    </div>
                    <p className="mt-1 text-xs text-[var(--muted)]">{ex.description}</p>
                  </button>
                ))}
              </div>

              <Field label="Drug name (for your records)">
                <input
                  className="input"
                  value={design.drug.name}
                  onChange={(e) =>
                    setDesign({ ...design, drug: { ...design.drug, name: e.target.value } })
                  }
                />
              </Field>

              <Field label="What type of payload?">
                <select
                  className="input"
                  value={design.drug.payload_type || "small_molecule"}
                  onChange={(e) => {
                    const payload_type = e.target.value as DrugPayload["payload_type"];
                    const presetKey =
                      payload_type === "mrna"
                        ? "mrna_sm102"
                        : payload_type === "sirna"
                          ? "sirna_mcq"
                          : "small_molecule";
                    setLipidPresetKey(presetKey);
                    const updated = {
                      ...design,
                      drug: {
                        ...design.drug,
                        payload_type,
                        loading_pct: Math.min(
                          design.drug.loading_pct,
                          LOADING_LIMITS[payload_type]
                        ),
                      },
                      lipids: lipidPresets[presetKey] || design.lipids,
                    };
                    setDesign(updated);
                    validateStructure(updated.drug);
                  }}
                >
                  <option value="small_molecule">Small molecule (e.g. chemotherapy drug)</option>
                  <option value="mrna">mRNA</option>
                  <option value="sirna">siRNA</option>
                  <option value="peptide">Peptide</option>
                  <option value="protein">Protein</option>
                </select>
              </Field>

              <Field label="How will you provide the structure?">
                <select
                  className="input"
                  value={design.drug.structure_source_type || "sequence"}
                  onChange={(e) => {
                    const updated = {
                      ...design,
                      drug: {
                        ...design.drug,
                        structure_source_type: e.target
                          .value as DrugPayload["structure_source_type"],
                      },
                    };
                    setDesign(updated);
                    setStructureValidated(false);
                  }}
                >
                  <option value="sequence">Genetic / amino acid sequence</option>
                  <option value="pubchem">PubChem ID (easiest for drugs)</option>
                  <option value="smiles">SMILES string</option>
                  <option value="pdb">PDB structure ID</option>
                  <option value="url">Structure file URL</option>
                </select>
              </Field>

              <Field label="Structure">
                <textarea
                  className="input min-h-[72px] font-mono text-xs"
                  value={design.drug.structure_value || ""}
                  onChange={(e) => {
                    setDesign({
                      ...design,
                      drug: {
                        ...design.drug,
                        structure_value: e.target.value,
                        smiles: e.target.value,
                      },
                    });
                    setStructureValidated(false);
                  }}
                  placeholder={
                    STRUCTURE_HINTS[
                      (design.drug.structure_source_type || "sequence") as keyof typeof STRUCTURE_HINTS
                    ]
                  }
                />
              </Field>

              <Field
                label={`How much drug to load: ${design.drug.loading_pct}% by weight (max ${LOADING_LIMITS[(design.drug.payload_type || "small_molecule") as keyof typeof LOADING_LIMITS]}%)`}
              >
                <input
                  type="range"
                  min={0.5}
                  max={
                    LOADING_LIMITS[
                      (design.drug.payload_type || "small_molecule") as keyof typeof LOADING_LIMITS
                    ]
                  }
                  step={0.5}
                  value={design.drug.loading_pct}
                  onChange={(e) =>
                    setDesign({
                      ...design,
                      drug: { ...design.drug, loading_pct: Number(e.target.value) },
                    })
                  }
                  className="w-full accent-[var(--primary)]"
                />
              </Field>

              <ValidationStatus
                validating={validating}
                validated={structureValidated}
                resolved={resolvedDrug}
                error={validationError}
                onRetry={() => validateStructure(design.drug)}
              />
            </div>
          )}

          {step === 1 && (
            <div className="space-y-5">
              <Field label="Project name">
                <input
                  className="input"
                  value={design.name}
                  onChange={(e) => setDesign({ ...design, name: e.target.value })}
                />
              </Field>

              <Field label={`Particle size: ${design.target_size_nm} nm`}>
                <input
                  type="range"
                  min={40}
                  max={200}
                  value={design.target_size_nm}
                  onChange={(e) =>
                    setDesign({ ...design, target_size_nm: Number(e.target.value) })
                  }
                  className="w-full accent-[var(--primary)]"
                />
                <p className="mt-1 text-xs text-[var(--muted)]">
                  Typical LNPs are 60–100 nm. Larger particles penetrate tissue differently.
                </p>
              </Field>

              <Field label="Lipid recipe (literature-based)">
                <select
                  className="input"
                  value={lipidPresetKey}
                  onChange={(e) => {
                    const key = e.target.value;
                    setLipidPresetKey(key);
                    const preset = lipidPresets[key];
                    if (preset) setDesign({ ...design, lipids: preset });
                  }}
                >
                  {Object.entries(LIPID_PRESET_LABELS).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </Field>

              <div>
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-sm font-medium">Lipid mix</span>
                  <span
                    className={`text-xs font-medium ${
                      Math.abs(lipidTotalPct(design.lipids) - 100) < 2
                        ? "text-[var(--success)]"
                        : "text-amber-400"
                    }`}
                  >
                    {Math.abs(lipidTotalPct(design.lipids) - 100) < 2 ? "✓ " : ""}
                    {lipidTotalPct(design.lipids).toFixed(0)}% total
                  </span>
                </div>
                {design.lipids.map((lipid, i) => (
                  <div key={lipid.name} className="mb-3">
                    <div className="mb-1 flex justify-between text-sm">
                      <span>{lipid.name}</span>
                      <span className="text-[var(--muted)]">{(lipid.ratio * 100).toFixed(0)}%</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={80}
                      step={0.5}
                      value={lipid.ratio * 100}
                      onChange={(e) => {
                        const lipids = [...design.lipids];
                        lipids[i] = { ...lipid, ratio: Number(e.target.value) / 100 };
                        setDesign({ ...design, lipids: normalizeLipids(lipids) });
                      }}
                      className="w-full accent-[var(--primary)]"
                    />
                  </div>
                ))}
              </div>

              <Field label={`PEG coating: ${design.pegylation.mol_pct}%`}>
                <input
                  type="range"
                  min={0}
                  max={10}
                  step={0.5}
                  value={design.pegylation.mol_pct}
                  onChange={(e) =>
                    setDesign({
                      ...design,
                      pegylation: {
                        ...design.pegylation,
                        enabled: Number(e.target.value) > 0,
                        mol_pct: Number(e.target.value),
                      },
                    })
                  }
                  className="w-full accent-[var(--primary)]"
                />
                <p className="mt-1 text-xs text-[var(--muted)]">
                  PEG helps particles circulate longer in blood.
                </p>
              </Field>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-5">
              <Field label={`Body pH: ${design.environment.ph}`}>
                <input
                  type="range"
                  min={5}
                  max={8}
                  step={0.1}
                  value={design.environment.ph}
                  onChange={(e) =>
                    setDesign({
                      ...design,
                      environment: { ...design.environment, ph: Number(e.target.value) },
                    })
                  }
                  className="w-full accent-[var(--primary)]"
                />
              </Field>
              <Field
                label={`Temperature: ${(design.environment.temperature_k - 273.15).toFixed(0)} °C`}
              >
                <input
                  type="range"
                  min={280}
                  max={320}
                  step={0.5}
                  value={design.environment.temperature_k}
                  onChange={(e) =>
                    setDesign({
                      ...design,
                      environment: {
                        ...design.environment,
                        temperature_k: Number(e.target.value),
                      },
                    })
                  }
                  className="w-full accent-[var(--primary)]"
                />
                <p className="mt-1 text-xs text-[var(--muted)]">
                  Used in all MD modules (Langevin thermostat). Default 37 °C.
                </p>
              </Field>
              <Field label="Fluid the particle will encounter">
                <select
                  className="input"
                  value={design.environment.fluid}
                  onChange={(e) =>
                    setDesign({
                      ...design,
                      environment: { ...design.environment, fluid: e.target.value },
                    })
                  }
                >
                  <option value="serum">Blood serum</option>
                  <option value="plasma">Plasma</option>
                  <option value="pbs">PBS buffer (lab conditions)</option>
                  <option value="cell_media">Cell culture media</option>
                </select>
              </Field>
              <Field label="Target tissue">
                <select
                  className="input"
                  value={design.target.tissue || "tumor"}
                  onChange={(e) =>
                    setDesign({
                      ...design,
                      target: { ...design.target, tissue: e.target.value },
                    })
                  }
                >
                  <option value="tumor">Tumor</option>
                  <option value="liver">Liver</option>
                  <option value="muscle">Muscle</option>
                  <option value="brain">Brain</option>
                  <option value="skin">Skin</option>
                </select>
              </Field>
              <Field label="What do you want to optimize?">
                <select
                  className="input"
                  value={design.target.goal}
                  onChange={(e) =>
                    setDesign({
                      ...design,
                      target: { ...design.target, goal: e.target.value },
                    })
                  }
                >
                  <option value="maximize_uptake">Get into cells efficiently</option>
                  <option value="controlled_release">Controlled drug release</option>
                  <option value="maximize_penetration">Deep tissue penetration</option>
                  <option value="minimize_toxicity">Minimize side effects</option>
                </select>
              </Field>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-5">
              <Field label="Simulation depth">
                <select
                  className="input"
                  value={simulationMode}
                  onChange={(e) => setSimulationMode(e.target.value)}
                >
                  <option value="standard_md">Standard — recommended</option>
                  <option value="production_md">Extended — higher accuracy</option>
                </select>
              </Field>

              <p className="text-sm text-[var(--muted)]">
                Each module below runs a real molecular dynamics simulation. Leave the defaults
                checked for a complete analysis.
              </p>

              {modules.map((mod) => (
                <label
                  key={mod.name}
                  className="flex cursor-pointer items-start gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-4 transition-colors hover:border-[var(--primary)]/40"
                >
                  <input
                    type="checkbox"
                    checked={enabledModules.includes(mod.name)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setEnabledModules([...enabledModules, mod.name]);
                      } else {
                        setEnabledModules(enabledModules.filter((m) => m !== mod.name));
                      }
                    }}
                    className="mt-1 accent-[var(--primary)]"
                  />
                  <div>
                    <p className="font-medium">{mod.label}</p>
                    <p className="text-sm text-[var(--muted)]">{mod.question}</p>
                  </div>
                </label>
              ))}

            </div>
          )}

          {step === 4 && run && (
            <div className="space-y-5">
              {run.status === "running" || run.status === "queued" ? (
                <div>
                  <div className="mb-2 flex justify-between text-sm">
                    <span className="text-[var(--muted)]">Overall progress</span>
                    <span className="font-medium">{runProgress}%</span>
                  </div>
                  <div className="h-3 overflow-hidden rounded-full bg-[var(--surface-elevated)]">
                    <div
                      className="h-full rounded-full bg-[var(--primary)] transition-all duration-500"
                      style={{ width: `${Math.max(runProgress, 5)}%` }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-[var(--muted)]">
                    Simulations run on the server — keep this tab open to track progress.
                  </p>
                </div>
              ) : run.status === "completed" ? (
                <div className="flex items-center gap-3 rounded-xl border border-[var(--success)]/30 bg-[var(--success)]/10 px-4 py-3">
                  <CheckCircle2 className="h-5 w-5 text-[var(--success)]" />
                  <p className="text-sm font-medium text-[var(--success)]">
                    All simulations finished successfully
                  </p>
                </div>
              ) : (
                <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                  {runError || "Something went wrong. See details below."}
                </div>
              )}

              <div className="space-y-2">
                {run.modules.map((mod) => (
                  <div
                    key={mod.module}
                    className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] px-4 py-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium capitalize">
                        {mod.module.replace(/_/g, " ")}
                      </span>
                      <StatusBadge status={mod.status} />
                    </div>
                    {mod.status === "failed" && mod.error && (
                      <p className="mt-2 text-xs text-red-400">{friendlyError(mod.error)}</p>
                    )}
                  </div>
                ))}
              </div>

              {results && run.status === "completed" && (
                <div>
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <h3 className="font-semibold">Results</h3>
                    <div className="flex flex-wrap gap-2">
                      <a
                        href={exportRunUrl(run.id, "json")}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-[var(--surface-elevated)]"
                      >
                        <Download className="h-3.5 w-3.5" />
                        JSON
                      </a>
                      <a
                        href={exportRunUrl(run.id, "csv")}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-[var(--surface-elevated)]"
                      >
                        <Download className="h-3.5 w-3.5" />
                        CSV
                      </a>
                      <Link
                        href={`/runs/${run.id}`}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-[var(--surface-elevated)]"
                      >
                        Full report
                      </Link>
                      <Link
                        href="/methodology"
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-[var(--surface-elevated)]"
                      >
                        Methods
                      </Link>
                    </div>
                  </div>
                  <KeyResultsSummary modules={results.modules} />
                  {run?.id && <StructurePanel runId={run.id} modules={results.modules} />}
                  <ResultsPanel modules={results.modules} />
                </div>
              )}

              {(run.status === "completed" || run.status === "failed") && (
                <button
                  onClick={handleReset}
                  className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-4 py-2 text-sm hover:bg-[var(--surface-elevated)]"
                >
                  <RefreshCw className="h-4 w-4" />
                  Start a new simulation
                </button>
              )}
            </div>
          )}
        </div>

        {/* Navigation */}
        {step < 4 && (
          <div className="mt-6 flex items-center justify-between">
            <button
              onClick={() => setStep(Math.max(0, step - 1))}
              disabled={step === 0}
              className="rounded-lg border border-[var(--border)] px-4 py-2.5 text-sm disabled:opacity-30"
            >
              Back
            </button>

            {step < 3 ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={(step === 0 && !structureValidated) || validating}
                className="inline-flex items-center gap-2 rounded-lg bg-[var(--primary)] px-5 py-2.5 text-sm font-medium text-white disabled:opacity-40"
              >
                Continue
                <ArrowRight className="h-4 w-4" />
              </button>
            ) : (
              <button
                onClick={handleStartRun}
                disabled={!structureValidated || !health?.simulations_ready || validating}
                className="inline-flex items-center gap-2 rounded-lg bg-[var(--success)] px-6 py-2.5 text-sm font-medium text-white disabled:opacity-40"
              >
                <Play className="h-4 w-4" />
                Start simulation
              </button>
            )}
          </div>
        )}

        {step === 3 && runError && (
          <p className="mt-3 text-center text-sm text-red-400">{runError}</p>
        )}
        {step === 3 && !health?.simulations_ready && (
          <p className="mt-3 text-center text-xs text-amber-400">
            {health?.message ||
              "Simulations are unavailable — the API could not load OpenMM. Restart with .\\scripts\\start-local.ps1 or docker compose up --build."}
          </p>
        )}
      </main>

      <style jsx global>{`
        .input {
          width: 100%;
          border-radius: 0.625rem;
          border: 1px solid var(--border);
          background: var(--surface-elevated);
          padding: 0.625rem 0.875rem;
          color: var(--foreground);
          font-size: 0.875rem;
        }
        .input:focus {
          outline: none;
          border-color: var(--primary);
          box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium">{label}</label>
      {children}
    </div>
  );
}

function ValidationStatus({
  validating,
  validated,
  resolved,
  error,
  onRetry,
}: {
  validating: boolean;
  validated: boolean;
  resolved: ResolvedDrug | null;
  error: string | null;
  onRetry: () => void;
}) {
  if (validating) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] px-4 py-3">
        <Loader2 className="h-4 w-4 animate-spin text-[var(--primary)]" />
        <span className="text-sm text-[var(--muted)]">Checking structure…</span>
      </div>
    );
  }
  if (validated && resolved) {
    return (
      <div className="rounded-xl border border-[var(--success)]/30 bg-[var(--success)]/10 px-4 py-3">
        <div className="flex items-center gap-2 text-sm font-medium text-[var(--success)]">
          <CheckCircle2 className="h-4 w-4" />
          Structure verified — you&apos;re good to continue
        </div>
        <p className="mt-1 text-xs text-[var(--muted)]">
          Molecular weight: {resolved.molecular_weight.toFixed(0)} Da ·{" "}
          {resolved.bead_count} simulation beads
        </p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
        <p className="text-sm text-red-300">{error}</p>
        <button
          onClick={onRetry}
          className="mt-2 text-xs font-medium text-[var(--primary)] hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }
  return (
    <button
      onClick={onRetry}
      className="w-full rounded-xl border border-dashed border-[var(--border)] px-4 py-3 text-sm text-[var(--muted)] hover:border-[var(--primary)] hover:text-white"
    >
      Verify structure before continuing
    </button>
  );
}

function KeyResultsSummary({
  modules,
}: {
  modules: Record<string, { data: Record<string, unknown> }>;
}) {
  const enc = modules.encapsulation?.data;
  const form = modules.formation?.data;
  const stab = modules.stability?.data;
  const trans = modules.transport?.data;
  const rel = modules.release?.data;

  const cards = [
    enc?.encapsulation_efficiency_estimate != null && {
      label: "Encapsulation efficiency",
      value: `${((enc.encapsulation_efficiency_estimate as number) * 100).toFixed(1)}%`,
    },
    form?.hydrodynamic_radius_nm != null && {
      label: "Hydrodynamic radius",
      value: `${form.hydrodynamic_radius_nm} nm`,
    },
    stab?.stability_score != null && {
      label: "Stability score",
      value: `${((stab.stability_score as number) * 100).toFixed(0)}%`,
    },
    trans?.penetration_depth_um != null && {
      label: "Tissue penetration (1 hr)",
      value: `${trans.penetration_depth_um} µm`,
    },
    rel?.half_life_hours != null && {
      label: "Release half-life",
      value: `${rel.half_life_hours} hrs`,
    },
  ].filter(Boolean) as { label: string; value: string }[];

  if (!cards.length) return null;

  return (
    <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {cards.map((c) => (
        <div
          key={c.label}
          className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-4"
        >
          <p className="text-xs text-[var(--muted)]">{c.label}</p>
          <p className="mt-1 text-xl font-semibold">{c.value}</p>
        </div>
      ))}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    queued: "text-[var(--muted)]",
    running: "text-[var(--warning)]",
    completed: "text-[var(--success)]",
    failed: "text-red-400",
  };
  return (
    <span className={`text-xs font-medium ${colors[status] || ""}`}>
      {status === "running" && <Loader2 className="mr-1 inline h-3 w-3 animate-spin" />}
      {STATUS_LABELS[status] || status}
    </span>
  );
}
