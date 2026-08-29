# GitHub Configuration

## Purpose

This folder contains GitHub-specific automation for the PDF archive repository.

## Contents

- `workflows/` — release and manually triggered GitHub Actions definitions.

## Responsibilities

Repository automation, pull-request templates, and other GitHub-hosted project
configuration belong here. Archive content and maintenance scripts do not.

## Important notes

The current workflow is a generic SLSA example. It signs placeholder artifacts
and must not be treated as provenance for the PDFs until its build step is wired
to the actual archive outputs.
