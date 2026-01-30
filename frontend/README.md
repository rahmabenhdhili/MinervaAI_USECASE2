# MinervaAI Frontend

React frontend for the MinervaAI unified platform.

## Setup

```bash
npm install
```

## Development

```bash
npm run dev
```

Server runs on http://localhost:3000

## Build

```bash
npm run build
```

## Structure

```
src/
├── components/     # Reusable components
│   └── Layout.jsx  # Main layout with navigation
├── pages/          # Page components
│   ├── HomePage.jsx
│   ├── B2CPage.jsx
│   ├── B2BPage.jsx
│   ├── UsershopPage.jsx
│   └── ShopGPTPage.jsx
├── utils/          # Utilities
│   └── api.js      # API client
├── App.jsx         # Main app component
├── main.jsx        # Entry point
└── index.css       # Global styles
```

## Color Palette

- `de-york`: #88c695
- `pixie-green`: #b2d0ab
- `foam`: #f5fefb (background)
- `viridian`: #3f8872 (primary)
- `shadow-green`: #9bc8bb
- `silver-tree`: #51ae93
- `moss-green`: #b6d89c
