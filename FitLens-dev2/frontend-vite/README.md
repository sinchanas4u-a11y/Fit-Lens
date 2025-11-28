# Body Measurement Frontend - Vite

Lightning-fast React frontend built with Vite.

## Features

- ⚡ **10-100x faster** than Create React App
- 🔥 Instant hot module replacement
- 📦 Optimized production builds
- 🎯 Modern development experience

## Quick Start

### Install Dependencies

```bash
npm install
```

### Start Development Server

```bash
npm run dev
```

Opens at: http://localhost:3000

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── main.jsx              # Entry point
├── App.jsx               # Main component
├── App.css               # App styles
├── index.css             # Global styles
└── components/
    ├── UploadMode.jsx    # Upload component
    └── UploadMode.css    # Component styles
```

## Configuration

### vite.config.js

- **Port**: 3000
- **Proxy**: `/api` → `http://localhost:5000`
- **Build**: Output to `dist/`

## Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |

## Backend Integration

The frontend connects to the backend API at `http://localhost:5000`.

Make sure the backend is running:

```bash
cd ../backend
python app_updated.py
```

## Environment Variables

Create `.env` file:

```
VITE_API_URL=http://localhost:5000
```

Use in code:

```javascript
const apiUrl = import.meta.env.VITE_API_URL;
```

## Deployment

### Build

```bash
npm run build
```

### Deploy

The `dist/` folder contains static files ready to deploy to:

- **Netlify**: Drag and drop `dist/` folder
- **Vercel**: Connect GitHub repo
- **GitHub Pages**: Use `gh-pages` package
- **Any static hosting**: Upload `dist/` contents

## Troubleshooting

### Port Already in Use

```bash
# Change port in vite.config.js
server: {
  port: 3001
}
```

### Proxy Not Working

1. Check backend is running on port 5000
2. Verify `vite.config.js` proxy configuration
3. Restart dev server

### Build Errors

```bash
# Clear cache
rm -rf node_modules dist
npm install
npm run build
```

## Performance

- **Dev server start**: 1-2 seconds
- **HMR**: Instant
- **Build time**: 5-10 seconds
- **Bundle size**: Optimized with tree-shaking

## Learn More

- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [Vite + React Guide](https://vitejs.dev/guide/)

## License

MIT
