# Architecture Document

## Overview
This project uses a modular approach:
- **Runner**: Orchestrates the execution of parts A, B, C.
- **Part A**: Headless browser testing with Playwright.
- **Part B & C**: Native app and desktop checks.
- **LLM Evaluator**: Takes the generated logs and prompts an LLM for build promotion.
