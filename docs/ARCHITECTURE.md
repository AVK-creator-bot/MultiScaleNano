# MultiscaleNano Architecture

## Product vision

One web app. One workflow. One nanocarrier design in, multiscale predictions out.

The researcher never sees GROMACS input files, scale conversion scripts, or job schedulers. They answer scientific questions; the platform runs the right simulations behind the scenes.

---

## User experience (web)

### Primary flow: Simulation Wizard

```
┌─────────────────────────────────────────────────────────────┐
│  1. Drug          SMILES / name / upload structure            │
│  2. Nanocarrier   LNP composition, size, PEG, ligands       │
│  3. Environment   pH, temperature, ionic strength, fluid      │
│  4. Target        Cell type, tissue, delivery goal            │
│  5. Modules       Auto-selected pipeline (user can toggle)    │
│  6. Review        Estimated runtime, compute cost             │
│  7. Run           Progress dashboard with live status         │
│  8. Results       Unified report + downloadable artifacts   │
└─────────────────────────────────────────────────────────────┘
```

### Results dashboard (single pane of glass)

Each completed run produces a **Nanocarrier Report**:

- **3D structure viewer** — assembled LNP morphology
- **Encapsulation score** — drug retention free energy, loading estimate
- **Stability profile** — aggregation risk vs pH / ionic strength
- **Corona composition** — dominant proteins, ligand masking (when enabled)
- **Release curve** — time → fraction released
- **Transport map** — penetration depth in selected tissue template
- **Provenance graph** — every parameter traced to its source simulation

### Design principles

1. **Progressive disclosure** — defaults are sensible; advanced parameters are collapsible
2. **No dead ends** — every step validates inputs before submission
3. **Honest uncertainty** — confidence intervals on translated parameters, not false precision
4. **Reproducibility** — every run is versioned with force fields, random seeds, and engine versions

---

## System architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         WEB TIER                                  │
│  Next.js 15 · React · Tailwind · NGL Viewer (3D) · Recharts      │
└────────────────────────────┬─────────────────────────────────────┘
                             │ REST / SSE
┌────────────────────────────▼─────────────────────────────────────┐
│                      ORCHESTRATION TIER                           │
│  FastAPI                                                          │
│  ├── ProjectService      CRUD for designs + runs                  │
│  ├── WorkflowPlanner     Drug + carrier + target → DAG            │
│  ├── JobDispatcher       Enqueue modules to Redis                 │
│  └── ArtifactRegistry    Store + query simulation outputs         │
└────────────────────────────┬─────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│ PostgreSQL  │    │ Redis           │    │ S3 / local   │
│ projects    │    │ job queue       │    │ artifact     │
│ runs        │    │ pub/sub status  │    │ storage      │
│ provenance  │    │                 │    │              │
└─────────────┘    └────────┬────────┘    └──────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                      WORKER TIER                                    │
│  Simulation Worker (Python)                                         │
│  ├── ModuleRunner        Execute one simulation module              │
│  ├── EngineAdapter         GROMACS CLI wrapper (Docker exec)        │
│  ├── InputBuilder          Design → .gro / .top / .mdp              │
│  └── OutputParser          Trajectory → structured artifact         │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                      ENGINE TIER (Docker)                           │
│  gromacs:2024 + Martini3 force field + lipid/build tools          │
└────────────────────────────────────────────────────────────────────┘
```

---

## Core data model

### NanocarrierDesign

The canonical representation of what the researcher designed. All modules read from and write extensions to this object.

```python
NanocarrierDesign:
  id: UUID
  carrier_type: "lnp" | "liposome" | ...
  drug:
    name: str
    smiles: str
    molecular_weight: float
  composition:
    lipids: [{ name, ratio, charge }]   # e.g. DSPC, cholesterol, ionizable lipid
    pegylation: { enabled, mol_pct, length }
    ligands: [{ name, density_pct, target }]
  geometry:
    target_size_nm: float
    shape: "spherical" | "discoidal"
  payload:
    drug_loading_pct: float
    encapsulation_mode: "core" | "membrane"
  surface:
    zeta_potential_mv: float | null
  environment:
    ph: float
    temperature_k: float
    ionic_strength_m: float
    fluid: "pbs" | "serum" | "plasma"
  target:
    cell_type: str | null
    tissue: str | null
    goal: "maximize_uptake" | "controlled_release" | ...
```

### SimulationRun

```python
SimulationRun:
  id: UUID
  design_id: UUID
  status: "queued" | "running" | "completed" | "failed"
  pipeline: ["encapsulation", "formation", "stability", ...]
  modules: [{ name, status, started_at, completed_at, artifact_id }]
  provenance: { engine_versions, force_fields, seeds }
  created_at: datetime
```

### ScaleArtifact

Every module output is a typed, versioned artifact — the contract between scales.

```python
ScaleArtifact:
  id: UUID
  run_id: UUID
  module: str
  scale: "atomistic" | "coarse_grained" | "mesoscale" | "continuum"
  data: { ... module-specific fields ... }
  uncertainty: { ... confidence intervals ... }
  provenance:
    upstream_artifacts: [UUID]
    translation_method: str
    force_field: str
  files: [{ path, type, description }]
```

---

## Workflow engine

### LNP default pipeline (DAG)

```
encapsulation ──► formation ──► stability ──► corona ──► transport
      │                │              │           │            │
      └────────────────┴──────────────┴───────────┴────────────┘
                              scale bridges
```

Each edge is a **ScaleBridge** that transforms upstream artifacts into downstream module inputs.

### Module specifications

#### 1. Encapsulation (`encapsulation`)

- **Input:** drug SMILES, lipid composition, loading %
- **Engine:** GROMACS atomistic or Martini CG
- **Process:** Build drug + lipid assembly, equilibrate, compute PMF / retention
- **Output artifact:**
  - `drug_retention_free_energy_kcal_mol`
  - `encapsulation_efficiency_estimate`
  - `drug_bead_coupling` (for downstream CG)

#### 2. Formation (`formation`)

- **Input:** lipid composition, size target, drug_bead_coupling from encapsulation
- **Engine:** GROMACS Martini CG self-assembly
- **Process:** Random lipid + drug placement → NPT equilibration → morphology analysis
- **Output artifact:**
  - `hydrodynamic_radius_nm`
  - `morphology` (core-shell, multilamellar, etc.)
  - `structure_file` (.gro)
  - `bead_interaction_matrix` (for stability)

#### 3. Stability (`stability`)

- **Input:** formation artifact, environment sweeps (pH, ionic strength, temperature)
- **Engine:** GROMACS Martini CG
- **Process:** Parameter sweep → aggregation/degradation metrics
- **Output artifact:**
  - `stability_score` (0–1)
  - `aggregation_propensity_by_condition`
  - `drug_leakage_rate`

#### 4. Corona (`corona`) — phase 2

- **Input:** formation artifact, fluid composition (serum protein list)
- **Engine:** CG binding energies + KMC
- **Output artifact:**
  - `effective_radius_nm`
  - `ligand_accessible_fraction`
  - `dominant_proteins`

#### 5. Transport (`transport`)

- **Input:** corona or formation artifact (effective size, charge), tissue template
- **Engine:** Continuum diffusion PDE (Python/NumPy)
- **Output artifact:**
  - `penetration_depth_um`
  - `concentration_profile`
  - `effective_diffusion_coefficient`

---

## Scale bridges (core IP)

Bridges are explicit, testable functions:

```python
class ScaleBridge(Protocol):
    name: str
    input_scale: Scale
    output_scale: Scale

    def translate(self, upstream: ScaleArtifact) -> dict:
        """Return module input parameters derived from upstream artifact."""
        ...

    def validate(self, upstream: ScaleArtifact) -> ValidationResult:
        """Check upstream artifact is within bridge validity domain."""
        ...
```

### v1 bridges

| Bridge | From → To | Method |
|--------|-----------|--------|
| `encapsulation_to_formation` | atomistic → CG | Martini mapping + drug bead coupling |
| `formation_to_stability` | CG → CG | Pass structure + interaction matrix |
| `formation_to_transport` | CG → continuum | Stokes-Einstein D, effective radius |
| `corona_to_transport` | mesoscale → continuum | Corona-adjusted radius + charge |

Every bridge logs its method, inputs, and uncertainty to provenance.

---

## Deployment model

### Local development

- Docker Compose: postgres, redis, gromacs engine
- API + worker + web run on host

### Production (future)

- **Web + API:** containerized on any cloud (Fly.io, Railway, AWS ECS)
- **Workers:** GPU-optional CPU workers on AWS Batch / Modal / dedicated HPC
- **Engine images:** pre-built GROMACS Docker pulled by workers
- **Artifacts:** S3-compatible object storage

### Compute expectations (LNP MVP)

| Module | Typical runtime | Hardware |
|--------|----------------|----------|
| Encapsulation | 1–4 hours | 8 CPU |
| Formation | 2–8 hours | 8 CPU |
| Stability (3 conditions) | 4–12 hours | 8 CPU |
| Transport | < 1 minute | 1 CPU |

Full pipeline: ~8–24 hours per design. Workers run asynchronously; the web UI streams progress via SSE.

---

## Security & multi-tenancy (future)

- Auth: OAuth (Google, institutional SSO)
- Projects scoped to user/organization
- Simulation artifacts isolated per tenant
- Rate limiting on job submission

---

## Roadmap

### Phase 1 — Foundation (current)
- [x] Architecture + schemas
- [ ] Web wizard + API skeleton
- [ ] GROMACS Docker + encapsulation module
- [ ] Formation module (Martini self-assembly)
- [ ] Results dashboard

### Phase 2 — Multiscale
- [ ] Stability sweeps
- [ ] Scale bridges with validation
- [ ] Corona module
- [ ] Transport continuum model

### Phase 3 — Intelligence
- [ ] AI optimization loop (multi-objective)
- [ ] Surrogate models for fast screening
- [ ] Experimental calibration import

### Phase 4 — Expansion
- [ ] Additional carrier types (liposomes, polymeric)
- [ ] Cell interaction module
- [ ] Cloud HPC integration
