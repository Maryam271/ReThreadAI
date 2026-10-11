import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { UploadZone } from './components/UploadZone';
import { StyleSelector } from './components/StyleSelector';
import { RedesignViewer } from './components/RedesignViewer';
import { ApiKeyModal } from './components/ApiKeyModal';
import type {
  StylePreset,
  RedesignResult,
  HealthStatus,
  EngineMode,
  FashionIntelligenceItem,
  DamageFocusPoint,
} from './types';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export const App: React.FC = () => {
  // State
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [damageLocation, setDamageLocation] = useState<string>('Auto-Detect');
  const [damageFocus, setDamageFocus] = useState<DamageFocusPoint | null>(null);
  const [selectedStyle, setSelectedStyle] = useState<StylePreset>('Streetwear');
  const [selectedEngine, setSelectedEngine] = useState<EngineMode>('auto');
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [strength, setStrength] = useState<number>(0.68);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [result, setResult] = useState<RedesignResult | null>(null);
  const [fashionIntelligence, setFashionIntelligence] = useState<FashionIntelligenceItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isKeyModalOpen, setIsKeyModalOpen] = useState<boolean>(false);

  // Fetch backend health and verified fashion intelligence
  const checkHealth = useCallback(async () => {
    try {
      const [resHealth, resIntel] = await Promise.allSettled([
        fetch(`${API_BASE}/api/health`),
        fetch(`${API_BASE}/api/fashion-intelligence`),
      ]);
      if (resHealth.status === 'fulfilled' && resHealth.value.ok) {
        const data = await resHealth.value.json();
        setHealth(data);
      }
      if (resIntel.status === 'fulfilled' && resIntel.value.ok) {
        const iData = await resIntel.value.json();
        if (iData && iData.resources) {
          setFashionIntelligence(iData.resources);
        }
      }
    } catch (err) {
      console.warn('Backend currently unreachable. Make sure FastAPI server is running.', err);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/api/health`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!cancelled && d) setHealth(d);
      })
      .catch((err) => console.warn('Health check unreachable', err));

    fetch(`${API_BASE}/api/fashion-intelligence`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!cancelled && d && d.resources) setFashionIntelligence(d.resources);
      })
      .catch((err) => console.warn('Fashion intelligence unreachable', err));

    return () => {
      cancelled = true;
    };
  }, []);

  // Handle image selection
  const handleImageSelected = useCallback((file: File) => {
    if (imagePreviewUrl) {
      URL.revokeObjectURL(imagePreviewUrl);
    }
    const newUrl = URL.createObjectURL(file);
    setImageFile(file);
    setImagePreviewUrl(newUrl);
    setResult(null);
    setError(null);
  }, [imagePreviewUrl]);

  // Handle image removal
  const handleImageRemoved = useCallback(() => {
    if (imagePreviewUrl) {
      URL.revokeObjectURL(imagePreviewUrl);
    }
    setImageFile(null);
    setImagePreviewUrl(null);
    setDamageLocation('Auto-Detect');
    setDamageFocus(null);
    setResult(null);
    setError(null);
  }, [imagePreviewUrl]);

  // Handle complete reset
  const handleReset = useCallback(() => {
    if (imagePreviewUrl) {
      URL.revokeObjectURL(imagePreviewUrl);
    }
    setImageFile(null);
    setImagePreviewUrl(null);
    setDamageLocation('Auto-Detect');
    setDamageFocus(null);
    setSelectedStyle('Streetwear');
    setSelectedEngine('auto');
    setCustomPrompt('');
    setStrength(0.68);
    setResult(null);
    setError(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [imagePreviewUrl]);

  // Handle generate redesign with optional engine override
  const handleGenerate = async (overrideEngine?: EngineMode) => {
    if (!imageFile) return;

    const engineToUse = overrideEngine || selectedEngine;
    setIsGenerating(true);
    setError(null);

    // Scroll to results section so user sees the progress
    const resultsElement = document.getElementById('results-view');
    if (resultsElement) {
      resultsElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    try {
      const formData = new FormData();
      formData.append('image', imageFile);
      formData.append('style', selectedStyle);
      if (customPrompt.trim()) {
        formData.append('custom_prompt', customPrompt.trim());
      }
      formData.append('strength', strength.toString());
      formData.append('provider', engineToUse);
      formData.append('damage_location', damageLocation);
      if (damageFocus) {
        formData.append('damage_coords', JSON.stringify(damageFocus));
      }

      const response = await fetch(`${API_BASE}/api/redesign`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errMessage = `Generation failed (${response.status})`;
        try {
          const errData = await response.json();
          if (errData && errData.detail) {
            errMessage = errData.detail;
          }
        } catch {
          // fallback to status text
        }
        throw new Error(errMessage);
      }

      const data = await response.json();
      setResult({
        id: data.id,
        imageData: data.image_data,
        style: data.style,
        provider: data.provider,
        promptUsed: data.prompt_used,
        durationSeconds: data.duration_seconds,
        downloadUrl: data.download_url,
        fallbackUsed: data.fallback_used,
        fallbackReason: data.fallback_reason,
        isDemo: data.is_demo,
        isCached: data.is_cached,
        garmentAnalysis: data.garment_analysis,
        repairPlan: data.repair_plan,
      });

      // Smooth scroll into results view
      setTimeout(() => {
        document.getElementById('results-view')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err: any) {
      console.error('Redesign generation error:', err);
      const rawMsg = err?.message || '';
      let displayError = rawMsg || 'An unexpected error occurred while communicating with the server.';
      if (rawMsg === 'Failed to fetch' || rawMsg.includes('NetworkError') || rawMsg.includes('Load failed')) {
        displayError =
          'Cannot connect to the ReThread AI backend API (http://127.0.0.1:8000). Please ensure the FastAPI server is running (start_backend.bat or start_all.bat) and try again.';
      }
      setError(displayError);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSwitchToFreeAi = () => {
    setSelectedEngine('free');
    handleGenerate('free');
  };

  const handleScrollToWorkspace = () => {
    document.getElementById('studio-workspace')?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleTryAnother = () => {
    setResult(null);
    document.getElementById('studio-workspace')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#faf8f5] text-[#181c1a] flex flex-col font-sans">
      {/* Sticky Top Header */}
      <Header
        health={health}
        onReset={handleReset}
        onOpenKeyModal={() => setIsKeyModalOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 pb-16">
        {/* Hero Section */}
        <Hero onScrollToWorkspace={handleScrollToWorkspace} />

        {/* Main Redesign Workspace (Two-column layout) */}
        <section id="studio-workspace" className="scroll-mt-24 pt-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            {/* Left Column: Garment Image Upload (5 columns on large screen) */}
            <div className="lg:col-span-5 flex flex-col">
              <UploadZone
                imageFile={imageFile}
                imagePreviewUrl={imagePreviewUrl}
                onImageSelected={handleImageSelected}
                onImageRemoved={handleImageRemoved}
                damageLocation={damageLocation}
                onDamageLocationChange={setDamageLocation}
                damageFocus={damageFocus}
                onDamageFocusChange={setDamageFocus}
                disabled={isGenerating}
              />
            </div>

            {/* Right Column: Style Presets & Parameters (7 columns on large screen) */}
            <div className="lg:col-span-7 flex flex-col">
              <StyleSelector
                selectedStyle={selectedStyle}
                onSelectStyle={setSelectedStyle}
                selectedEngine={selectedEngine}
                onSelectEngine={setSelectedEngine}
                customPrompt={customPrompt}
                onCustomPromptChange={setCustomPrompt}
                strength={strength}
                onStrengthChange={setStrength}
                onGenerate={() => handleGenerate()}
                isGenerating={isGenerating}
                hasImage={!!imageFile}
              />
            </div>
          </div>
        </section>

        {/* Redesign Results Section (Side-by-side comparison, Download, Feedback, Repair Guide) */}
        <RedesignViewer
          originalImageUrl={imagePreviewUrl}
          result={result}
          isGenerating={isGenerating}
          error={error}
          onRetry={() => handleGenerate()}
          onTryAnother={handleTryAnother}
          onOpenKeyModal={() => setIsKeyModalOpen(true)}
          onSwitchToFreeAi={handleSwitchToFreeAi}
          fashionIntelligence={fashionIntelligence}
        />
      </main>

      {/* Elegant Footer */}
      <footer className="border-t border-[#e8e3dc] bg-white py-8 text-xs text-[#6e7672]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <span className="font-serif-heading font-bold text-sm text-[#181c1a]">
              ReThread AI
            </span>
            <span>•</span>
            <span>Generative Clothing Redesign Studio</span>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={() => setIsKeyModalOpen(true)}
              className="hover:text-[#181c1a] transition-colors"
            >
              Engine & API Setup
            </button>
            <span>•</span>
            <span>Hackathon MVP Edition</span>
          </div>
        </div>
      </footer>

      {/* API Key Instructions Modal */}
      <ApiKeyModal
        isOpen={isKeyModalOpen}
        onClose={() => setIsKeyModalOpen(false)}
        health={health}
        onRefreshHealth={checkHealth}
      />
    </div>
  );
};

export default App;
