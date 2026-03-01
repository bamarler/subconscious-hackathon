# Shell configuration for git bash compatibility
ifeq ($(OS),Windows_NT)
    SHELL := C:/Program Files/Git/bin/bash.exe
    ifeq ($(wildcard $(SHELL)),)
        SHELL := C:/Program Files/Git/usr/bin/bash.exe
    endif
    ifeq ($(wildcard $(SHELL)),)
        SHELL := C:/Program Files (x86)/Git/bin/bash.exe
    endif
    ifeq ($(wildcard $(SHELL)),)
        SHELL := C:/Program Files (x86)/Git/usr/bin/bash.exe
    endif
    export PATH := C:/Program Files/Git/usr/bin:$(PATH)
else
    SHELL := /bin/bash
endif
.SHELLFLAGS := -euo pipefail -c

.PHONY: help check-deps init-env init up down

# Colors for output
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m # No Color
CHECKMARK := [OK]
CROSSMARK := [NO]

# Project settings
PROJECT_NAME := lecture-to-comic

help: ## Show this help message
	@printf "$(CYAN)====================================================\n$(NC)"
	@printf "$(CYAN)  Lecture-to-Comic - Development Commands\n$(NC)"
	@printf "$(CYAN)====================================================\n\n$(NC)"
	@awk 'BEGIN {FS = ":.*##"; section=""} \
		/^[a-zA-Z_-]+:.*?##/ { \
			printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 \
		}' $(MAKEFILE_LIST)
	@printf "\n"

check-deps: ## Check if all required dependencies are installed
	@printf "$(BLUE)Checking dependencies...\n$(NC)\n"
	@command -v python >/dev/null 2>&1 && \
		printf "  $(GREEN)$(CHECKMARK)$(NC) Python:      $$(python --version)\n" || \
		printf "  $(RED)$(CROSSMARK)$(NC) Python:      Not found\n"
	@command -v uv >/dev/null 2>&1 && \
		printf "  $(GREEN)$(CHECKMARK)$(NC) uv:          $$(uv --version)\n" || \
		printf "  $(RED)$(CROSSMARK)$(NC) uv:          Not found (install: curl -LsSf https://astral.sh/uv/install.sh | sh)\n"
	@command -v bun >/dev/null 2>&1 && \
		printf "  $(GREEN)$(CHECKMARK)$(NC) Bun:         $$(bun --version)\n" || \
		printf "  $(RED)$(CROSSMARK)$(NC) Bun:         Not found (install: curl -fsSL https://bun.sh/install | bash)\n"
	@printf "\n"

init-env: ## Copy .env.example files to .env
	@printf "$(BLUE)Setting up environment files...\n\n$(NC)"
	@if [ -f backend/.env.example ]; then \
		if [ ! -f backend/.env ]; then \
			cp backend/.env.example backend/.env && \
			printf "  $(GREEN)$(CHECKMARK)$(NC) Created backend/.env\n"; \
		else \
			printf "  $(YELLOW)[WARNING]$(NC)  backend/.env already exists\n"; \
		fi \
	else \
		printf "  $(RED)$(CROSSMARK)$(NC) backend/.env.example not found\n"; \
	fi
	@printf "\n"

init: check-deps init-env ## Initialize the entire project (install deps + env)
	@printf "$(BLUE)Installing backend dependencies...\n$(NC)"
	@uv sync --project backend
	@printf "  $(GREEN)$(CHECKMARK)$(NC) Backend dependencies installed\n\n"
	@printf "$(BLUE)Installing frontend dependencies...\n$(NC)"
	@bun install --cwd frontend
	@printf "  $(GREEN)$(CHECKMARK)$(NC) Frontend dependencies installed\n\n"
	@printf "$(GREEN)$(CHECKMARK) Project initialization complete!\n$(NC)"
	@printf "\n"

up: ## Start backend and frontend dev servers
	@printf "$(BLUE)Starting backend...\n$(NC)"
	@uv run --project backend --directory backend uvicorn app.main:app --reload --port 8000 &
	@printf "$(BLUE)Starting frontend...\n$(NC)"
	@bun run --cwd frontend dev &
	@printf "\n"
	@printf "$(GREEN)$(CHECKMARK) All services started!\n$(NC)"
	@printf "  $(CYAN)API:$(NC)      http://localhost:8000\n"
	@printf "  $(CYAN)Frontend:$(NC) http://localhost:5173\n"
	@printf "\n"
	@wait

down: ## Stop all dev servers
	@printf "$(BLUE)Stopping services...\n$(NC)"
	@-pkill -f "uvicorn app.main:app" 2>/dev/null || true
	@-pkill -f "vite" 2>/dev/null || true
	@printf "  $(GREEN)$(CHECKMARK)$(NC) All services stopped\n"
	@printf "\n"
