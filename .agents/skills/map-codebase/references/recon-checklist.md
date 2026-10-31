# Recon checklist

Read when the manifest or test runner is not obvious from the tree. One pass,
in this order; every claim in the map traces to what you actually saw.

## Find the build and test surface

| Signal | Look at | Test command pattern |
|---|---|---|
| `package.json` | `scripts`, `workspaces` | the `test` script, runner flags in CI config |
| `pyproject.toml` / `setup.py` / `requirements*.txt` | `[tool.pytest]`, deps | `pytest` (or the tox/nox default) |
| `go.mod` | module path, `cmd/` | `go test ./...` |
| `Cargo.toml` | `[workspace]`, bins | `cargo test` |
| `pom.xml` / `build.gradle*` | modules, plugins | the wrapper (`./mvnw test`, `./gradlew test`) |
| `Makefile` / `justfile` | named targets | the target CI actually calls |
| CI config (`.github/workflows/`, similar) | the real pipeline | whatever CI runs IS the truth |

Decision rules:

- The CI config outranks the README: record what CI runs, note the
  discrepancy if the README says something else.
- Suite does not run at all → record why in one line (missing service, env,
  generated code) and list the parts that do run. Never silently claim green.
- Monorepo → map per-package test commands, not one misleading root command.

## Find entry points

Walk these, whichever exist: declared bins/scripts in the manifest, `main()`
or framework boot files, route/controller registries, job or daemon
definitions, Docker/entrypoint files, `docs/agents/*.md` claims (verify one).

## Find candidate seams

A seam is where a later change can attach without ripping surrounding code:

- Interfaces/protocols with multiple implementations (DI registrations show
  them).
- Test directories mirroring source layout — the tests name the seams in use.
- Adapter/boundary dirs (`adapters/`, `gateways/`, `ports/`) and generated
  client wrappers.
- Public API surface: exported symbols, route tables, published schemas.

Name seams by their contract (interface name), not by file path — paths rot,
per the durability rule.

## Keep recon bounded

Read a connected slice, not the whole repo: entry points, the modules they
pull in, one representative test per seam. Stop when the map's five sections
are answerable; depth beyond that belongs to the spec stage.
