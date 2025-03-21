# Microfrontend Monorepo

This is a monorepo containing a FastAPI backend and two React microfrontend applications using module federation.

## Structure

- `apps/api` - FastAPI backend
- `apps/host` - Container application (React)
- `apps/remote` - Remote application exposing components (React)

## Setup and Running

### Install Dependencies

```bash
# Install workspace dependencies
yarn install
```

### Setup API Environment

```bash
cd apps/api
uv sync
```

### Run All Projects at Once

You can run all projects (API, remote, and host) with a single command:

```bash
# Using yarn
yarn dev

# Or using nx
yarn dev:nx

# Or directly with nx
nx run-many --target=dev --all --parallel
```

### Run Individual Projects

If you prefer to run each project separately:

#### Run the API

```bash
cd apps/api
source .venv/bin/activate
python main.py
```

The API will be available at http://localhost:8000

#### Run the Remote App

```bash
cd apps/remote
yarn dev
```

The remote app will be available at http://localhost:3001

#### Run the Host App

```bash
cd apps/host
yarn dev
```

The host app will be available at http://localhost:3000

## Features

- **API**: FastAPI with automatic documentation
- **Module Federation**: Sharing components between apps
- **TypeScript**: Type safety for both React applications
- **Development Servers**: Hot reloading for both front-end apps
