# Migrate Frontend from Create React App to Vite

## Why Vite?

- ⚡ **10-100x faster** than Create React App
- 🔥 **Instant hot module replacement** (HMR)
- 📦 **Smaller bundle sizes**
- 🚀 **Faster build times**
- 🎯 **Better developer experience**

## Migration Steps

### Option 1: Automatic Migration (Recommended)

Run the migration script:

```bash
# From project root
MIGRATE_TO_VITE.bat
```

### Option 2: Manual Migration

Follow these steps:

#### Step 1: Create New Vite Project

```bash
# From project root
npm create vite@latest frontend-vite -- --template react
cd frontend-vite
npm install
```

#### Step 2: Install Dependencies

```bash
npm install axios
```

#### Step 3: Copy Your Components

```bash
# Copy components
xcopy /E /I ..\frontend\src\components src\components

# Copy CSS
copy ..\frontend\src\App.css src\App.css
```

#### Step 4: Update Imports

Vite uses ES modules, so update your imports:

- Remove `%PUBLIC_URL%` references
- Update asset imports to use relative paths
- No need for `process.env.PUBLIC_URL`

#### Step 5: Configure Vite

Create `vite.config.js` (see below)

#### Step 6: Update package.json scripts

Already done in the new project

#### Step 7: Test

```bash
npm run dev
```

## What I'll Create for You

I'll create a complete Vite-based frontend with:

1. **vite.config.js** - Vite configuration with proxy
2. **Updated App.jsx** - Main app component
3. **Updated components** - All your components migrated
4. **package.json** - With correct dependencies
5. **index.html** - Vite entry point

## Files Structure

```
frontend-vite/
├── index.html          # Entry point (moved from public/)
├── vite.config.js      # Vite configuration
├── package.json        # Dependencies
├── src/
│   ├── main.jsx       # Entry point (was index.js)
│   ├── App.jsx        # Main component
│   ├── App.css        # Styles
│   └── components/
│       ├── UploadModeUpdated.jsx
│       ├── UploadModeUpdated.css
│       └── ...
└── public/            # Static assets
```

## Key Differences

### Create React App vs Vite

| Feature | CRA | Vite |
|---------|-----|------|
| Dev Server Start | 10-30s | 1-2s |
| HMR | 1-5s | Instant |
| Build Time | 30-60s | 5-10s |
| Bundle Size | Larger | Smaller |
| Config | Hidden | Visible |

### Code Changes

**Before (CRA):**
```javascript
import logo from './logo.svg';
const url = process.env.PUBLIC_URL + '/image.png';
```

**After (Vite):**
```javascript
import logo from './logo.svg';
const url = '/image.png';
```

## Running the New Frontend

```bash
cd frontend-vite
npm run dev
```

Opens at: `http://localhost:5173` (Vite default port)

## Building for Production

```bash
npm run build
npm run preview  # Preview production build
```

## Troubleshooting

### Port Already in Use

Vite uses port 5173 by default. To change:

```javascript
// vite.config.js
export default {
  server: {
    port: 3000
  }
}
```

### Proxy Not Working

Check `vite.config.js`:

```javascript
export default {
  server: {
    proxy: {
      '/api': 'http://localhost:5000'
    }
  }
}
```

### Import Errors

- Use `.jsx` extension for JSX files
- Update imports to use relative paths
- Remove `%PUBLIC_URL%` references

## Benefits You'll See

1. **Faster Development**
   - Dev server starts in 1-2 seconds
   - Instant hot reload
   - No more waiting!

2. **Better Performance**
   - Smaller bundle sizes
   - Faster page loads
   - Better user experience

3. **Modern Tooling**
   - Native ES modules
   - Better error messages
   - Cleaner configuration

## Next Steps

After migration:

1. Test all components
2. Update documentation
3. Update deployment scripts
4. Enjoy the speed! 🚀

## Rollback

If you need to go back:

```bash
# Keep both folders
# Use frontend/ for CRA
# Use frontend-vite/ for Vite
```

## Support

- Vite Docs: https://vitejs.dev/
- Migration Guide: https://vitejs.dev/guide/migration.html
