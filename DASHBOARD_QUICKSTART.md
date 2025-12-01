# Dashboard Quick Start

## 1. Install Dependencies

```bash
cd dashboard
npm install
```

## 2. Start the Dashboard

```bash
npm run dev
```

The dashboard will open at `http://localhost:3000`

## 3. View Mock Incidents

The dashboard comes with mock incident data, so you can immediately see:
- 3 sample incidents with different severity levels
- Risk scores and event counts
- Forensic artifacts
- Blockchain anchoring status
- Response actions

## 4. Connect to Real Backend (Optional)

If you have the backend services running:

```bash
# Terminal 1: Start blockchain gateway
python -m uvicorn blockchain.gateway:app --host 0.0.0.0 --port 8080

# Terminal 2: Start forensics service
cd forensics
uvicorn main:app --host 0.0.0.0 --port 9000

# Terminal 3: Start dashboard
cd dashboard
npm run dev
```

Set environment variables:

```bash
export REACT_APP_API_URL=http://localhost:9000
```

## 5. Features to Explore

- **Incident List**: Click on any incident to view details
- **Risk Visualization**: See risk scores and contributing events
- **Artifacts**: View collected forensic artifacts
- **Verify Integrity**: Click "Verify Integrity" to check blockchain anchoring
- **Response Actions**: See active response measures (isolation, deception, containment)

## 6. Build for Production

```bash
npm run build
```

Output will be in `dist/` directory, ready to deploy.

## Styling

The dashboard uses:
- **TailwindCSS**: Utility-first CSS framework
- **Light Theme**: Clean, modern design with light colors
- **Lucide Icons**: Beautiful, consistent icons
- **Responsive**: Works on desktop, tablet, and mobile

## Customization

- Edit `src/components/` to modify UI
- Update `src/api.js` to connect to real APIs
- Modify `tailwind.config.js` for color/theme changes
- Update mock data in `src/api.js` for demo purposes
