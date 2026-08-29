# Workflows

## Purpose

Contains GitHub Actions used by this repository.

## Contents

- `generator-generic-ossf-slsa3-publish.yml` — runs on releases or manual
  dispatch and invokes OpenSSF's reusable SLSA provenance generator.

## Responsibilities

Workflow files should define archive-specific validation, packaging, or release
automation. Keep local discovery and scraping logic in the root Python tools.

## Important notes

The current build job creates two placeholder text files. Its resulting
attestation does not cover any PDF or JSON manifest. Replace those placeholders
with explicitly selected, validated release artifacts before relying on the
workflow for archive provenance.
