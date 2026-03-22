# PathReview Frontend

A React + TypeScript frontend for PathReview, an AI-powered portfolio review assistant.

## Tech Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS (via CDN)
- Lucide React (icons)
- React Router v6
- Vitest (testing)

## Quick Start

### Prerequisites

- Node.js 16+ and npm/yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The frontend will run at `http://localhost:5173` and automatically proxy API calls to `http://localhost:8000`.

### Build

```bash
npm run build
```

### Testing

```bash
npm run test
npm run test:coverage
```

## Project Structure

```
src/
├── components/          # Reusable UI components
├── context/            # Auth context and providers
├── hooks/              # Custom React hooks
├── pages/              # Page components (routes)
├── services/           # API client
├── test/               # Test setup
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
├── App.tsx             # Main app component with routing
├── main.tsx            # Entry point
└── index.css           # Global styles
```

## Key Features

- User authentication (login/register)
- Portfolio profile creation
- AI-powered review process with real-time status polling
- Review history with pagination and search
- Expandable feedback sections with accessibility support
- Export and share functionality
- Responsive design with Tailwind CSS

## API Integration

The frontend communicates with the backend API at `http://localhost:8000`. All requests include JWT authentication via the `Authorization` header.

### Main API Endpoints

- `POST /token` - Login
- `POST /register` - Register
- `POST /profiles` - Create profile
- `POST /reviews` - Create review
- `GET /reviews/{id}` - Get review details
- `GET /reviews/{id}/status` - Get review status (for polling)
- `GET /reviews` - List reviews (with pagination)

## Authentication

JWT tokens are stored in localStorage and automatically attached to all API requests. The auth context manages user state and login/logout.

## Styling

All styling uses Tailwind CSS utility classes. The CDN is loaded in `index.html`, so no build-time CSS processing is needed.
