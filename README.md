# ReThread AI — Generative Clothing Redesign Studio

> **"Give Your Clothes a Second Life."**  
> *Upload a garment. Reimagine its style. Discover a new look with AI.*

A complete, working Hackathon MVP that empowers users to reimagine old, plain, or damaged clothing into bespoke fashion pieces using state-of-the-art image-conditioned generative AI.

---

## 👕 1. What is ReThread AI?

Fast fashion generates millions of tons of textile waste every year. **ReThread AI** bridges sustainable fashion and generative AI by allowing users to upload a photo of any garment they already own, select a tailored redesign aesthetic (e.g. Streetwear, Floral Embroidery, Vintage, Minimalist, Patchwork, Artistic, or Custom), and receive a high-fidelity visual redesign that preserves the original silhouette, cut, and seam structure while applying bespoke fashion transformations.

### Core User Journey
$$\text{Upload Garment} \longrightarrow \text{Select Style} \longrightarrow \text{Generate Redesign} \longrightarrow \text{Compare \& Download}$$

---

## 🛠️ 2. Technology Stack

- **Frontend:**
  - **React 19 + TypeScript** — High-performance, reactive UI architecture.
  - **Vite 8** — Ultra-fast development server with automatic API proxying.
  - **Tailwind CSS v4** — Clean, bespoke minimalist styling tailored for modern fashion tech (warm white backgrounds `#faf8f5`, deep forest green `#1d4a38`, refined typography).
  - **Lucide Icons** — Lightweight, consistent iconography.
- **Backend:**
  - **Python 3.10+ / FastAPI** — Lightweight, asynchronous REST API.
  - **Pillow (PIL)** — Image validation, EXIF orientation correction, dimension normalization, and format sanitization.
  - **HTTPX** — Resilient asynchronous HTTP client for AI provider integration.
- **AI Integrations:**
  - **Stability AI (SD3.5 Image-to-Image)** *(Primary)* — High-fidelity garment conditioning with configurable transformation strength.
  - **Replicate (InstructPix2Pix)** *(Alternative)* — Direct instruction-based image-to-image editing.

---

## 🚀 3. Quickstart Guide (Beginner Friendly)

### Prerequisites
1. **Python 3.10 or higher** (verify with `python --version`)
2. **Node.js 18 or higher** (verify with `node --version`)

---

### Step 1: Configure Your AI API Key

ReThread AI uses genuine image-to-image AI generation.

1. Navigate to the `backend/` directory.
2. Locate the `.env` file (or copy `.env.example` to `.env`):
   ```bash
   # In backend/.env
   STABILITY_API_KEY=your_stability_api_key_here
   ```
3. **Get an API Key:**
   - Stability AI: Sign up and generate a key at [platform.stability.ai/account/keys](https://platform.stability.ai/account/keys).
   - *(Optional alternative)* Replicate: [replicate.com/account/api-tokens](https://replicate.com/account/api-tokens).

> 💡 **No key right now?** You can still run the entire application! The interface includes a full **API Setup Guide modal**, 1-click garment presets, and validation tests. Once you add your key to `.env`, the backend detects it immediately without restarting.

---

### Step 2: Start the Servers

#### Option A: 1-Click Launch (Windows)
Double-click `start_all.bat` in the project root. This launches both the backend and frontend in separate command windows.

#### Option B: Manual Command Line

**Terminal 1 — Backend (FastAPI):**
```powershell
# From the project root
cd backend
python run.py
```
*Backend runs at:* `http://127.0.0.1:8000` (Health Check: `http://127.0.0.1:8000/api/health`)

**Terminal 2 — Frontend (Vite):**
```powershell
# In a second terminal from project root
cd frontend
npm run dev
```
*Frontend runs at:* `http://localhost:5173`

---

## 🧪 4. Testing & Verification

Automated unit and integration test suites are included to verify all components, image processing pipelines, and API endpoints.

### Run Backend Unit & Integration Tests:
```powershell
python backend/tests/run_tests.py
```
or with pytest:
```powershell
python -m pytest backend/tests
```

**Test Suite Coverage:**
- ✅ `test_health_endpoint`: Validates server status, provider detection, and supported presets.
- ✅ `test_image_utils_valid`: Verifies Pillow aspect-ratio preservation and PNG normalization.
- ✅ `test_image_utils_unsupported_format`: Rejects non-image and corrupted uploads with HTTP 400.
- ✅ `test_image_utils_oversized`: Rejects files exceeding the 10 MB limit.
- ✅ `test_redesign_invalid_style`: Validates style preset restrictions.
- ✅ `test_redesign_missing_api_key`: Asserts clear guidance response when API key is unconfigured.
- ✅ `test_redesign_and_download_flow_mocked`: Validates complete redesign execution, base64 payload, and download cache retrieval.

---

## 🎨 5. Key Design & UX Features

1. **Fashion-Tech Aesthetic:** Warm off-white background (`#faf8f5`), deep charcoal typography (`#181c1a`), rich forest green accents (`#1d4a38`), and Playfair Display serif headings.
2. **Instant 1-Click Test Garments:** Don't have a garment photo handy? Click "Denim Jacket", "Cotton White T-Shirt", or "Vintage Hoodie" directly in the upload card for immediate testing.
3. **Interactive Side-by-Side & Flip Views:** Easily inspect the original reference garment and AI redesign side-by-side or use Flip View to switch back and forth.
4. **Resilient Error Handling:** In the event of network disruption or missing credentials, the uploaded image, selected style, and prompt are preserved—users never lose their progress.
5. **Real High-Resolution Download:** One-click download button saves the generated redesign directly to the user's computer with an organized filename.

---

## 🎬 6. 3-Minute Hackathon Demo Script

Follow this step-by-step checklist when recording your hackathon demo:

| Time | Action | What to Say / Show |
| :--- | :--- | :--- |
| **0:00 – 0:30** | Introduce Problem & Solution | "Every year millions of wearable garments are discarded. ReThread AI gives your clothes a second life through AI-powered redesign." Show the clean studio interface. |
| **0:30 – 1:00** | Upload Reference Garment | Drag and drop a garment photo (or click one of the 1-click test garments like *Denim Jacket*). Point out the file size indicator and preview. |
| **1:00 – 1:40** | Select Style Preset & Instruction | Click **"Floral Embroidery"** or **"Streetwear"**. Add a custom prompt: *"Add colorful wildflower needlework to the chest pockets."* Adjust the redesign intensity slider. |
| **1:40 – 2:20** | Generate Redesign | Click **"Generate Redesign"**. Highlight the loading state that preserves the original reference image. Show the generated result appear! |
| **2:20 – 2:45** | Compare & Flip Views | Switch between **Side-by-Side** and **Flip View** to show how the original garment silhouette is preserved while the texture and detailing are transformed. |
| **2:45 – 3:00** | Download & Wrap-up | Click **"Download Redesign"** to verify high-res export. Conclude: "ReThread AI makes circular fashion personal, creative, and accessible." |

---

## 📂 7. Project Structure

```
ReThreadAI/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py            # Environment settings and provider detection
│   │   ├── image_utils.py       # Pillow processing, orientation & validation
│   │   ├── ai_service.py        # Stability AI & Replicate image-to-image clients
│   │   └── main.py              # FastAPI endpoints & CORS configuration
│   ├── tests/
│   │   ├── test_api.py          # Pytest test suite
│   │   └── run_tests.py         # Standalone unittest runner
│   ├── .env.example             # Configuration template
│   ├── .env                     # Local environment variables
│   ├── requirements.txt         # Python dependencies
│   └── run.py                   # Uvicorn backend starter
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx       # Wordmark, live AI status & reset action
│   │   │   ├── Hero.tsx         # Vision statement & quick-step flow
│   │   │   ├── UploadZone.tsx   # Drag & drop upload + 1-click test garments
│   │   │   ├── StyleSelector.tsx# 7 style presets, vision prompt & slider
│   │   │   ├── RedesignViewer.tsx# Side-by-side comparison & export
│   │   │   └── ApiKeyModal.tsx  # Beginner setup guide for API keys
│   │   ├── types.ts             # TypeScript definitions
│   │   ├── App.tsx              # Main application orchestrator
│   │   ├── index.css            # Tailwind CSS v4 & custom design tokens
│   │   └── main.tsx             # React entry point
│   ├── package.json             # Node dependencies
│   └── vite.config.ts           # Vite proxy configuration
├── start_all.bat                # 1-Click launcher for both servers
├── start_backend.bat            # Standalone backend launcher
├── start_frontend.bat           # Standalone frontend launcher
├── .gitignore                   # Git ignore patterns
└── README.md                    # Project documentation
```

---

## 🔒 8. Security & Privacy

- **Server-Side API Keys:** Provider credentials reside exclusively in `backend/.env` on your local server. They are never bundled into client JavaScript or sent in HTTP headers to browsers.
- **In-Memory Image Processing:** Uploaded images and generated redesigns are processed in-memory and cached with an automatic 1-hour expiration purge to prevent server disk bloat or persistent storage leaks.
