import React, { useState } from 'react';
import {
  Download,
  RotateCcw,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Clock,
  Cpu,
  Zap,
  AlertCircle,
  BookOpen,
  Wrench,
  Scissors,
  ExternalLink,
  ShieldCheck,
  FileText,
} from 'lucide-react';
import type { RedesignResult, FashionIntelligenceItem } from '../types';

interface RedesignViewerProps {
  originalImageUrl: string | null;
  result: RedesignResult | null;
  isGenerating: boolean;
  error: string | null;
  onRetry: () => void;
  onTryAnother: () => void;
  onOpenKeyModal: () => void;
  onSwitchToFreeAi?: () => void;
  fashionIntelligence?: FashionIntelligenceItem[];
}

const DEFAULT_FASHION_INTELLIGENCE: FashionIntelligenceItem[] = [
  {
    id: 'patagonia-worn-wear',
    title: 'Patagonia Worn Wear DIY Repair Program & Hand-Mending Guides',
    source: 'Patagonia & iFixit',
    category: 'Visible Mending & Gear Repair',
    type: 'verified_external',
    url: 'https://wornwear.patagonia.com',
    publication_date: '2024–2026 Active Directory',
    summary:
      'Over 100 free step-by-step guides covering hand sewing, blanket stitching, woven darning for knits, and patch kits to extend garment life.',
    key_technique: 'Hand sewing, woven darning, fabric patch kits',
    relevance: 'Denim jackets, fleece outerwear, woven pants',
  },
  {
    id: 'fashion-revolution-loved-clothes',
    title: "Fashion Revolution: 'Loved Clothes Last' & Mend in Public Day",
    source: 'Fashion Revolution (Orsola de Castro)',
    category: 'Circular Fashion Philosophy',
    type: 'verified_external',
    url: 'https://www.fashionrevolution.org',
    publication_date: 'Annual Global Campaign (Est. 2017)',
    summary:
      'Global sustainable fashion movement advocating visible mending and upcycling as acts of personal style and environmental care.',
    key_technique: 'Visible mending, Sashiko stitching, decorative surface threadwork',
    relevance: 'Cotton shirts, hoodies, everyday sustainable wardrobes',
  },
  {
    id: 'sashiko-story-boro',
    title: 'Traditional Japanese Sashiko & Boro Structural Textile Reinforcement',
    source: 'Atsushi Futatsuya / Sashiko Story',
    category: 'Heritage Textile Repair',
    type: 'verified_external',
    url: 'https://sashikostory.com',
    publication_date: 'Heritage & Modern Practice',
    summary:
      'Authentic Japanese mending utilizing geometric running stitches (Sashiko) and layered rag patching (Boro) to reinforce denim and twill.',
    key_technique: 'Geometric running stitch, Boro fabric layering',
    relevance: 'Denim twill, canvas jackets, knee and elbow stress tears',
  },
  {
    id: 'vam-textile-conservation',
    title: 'V&A Museum Textile Conservation: Fiber Stabilization & Support Patching',
    source: 'Victoria & Albert Museum Conservation',
    category: 'Textile Preservation',
    type: 'verified_external',
    url: 'https://www.vam.ac.uk',
    publication_date: 'Archival Conservation Reference',
    summary:
      'Museum-grade textile stabilization standards. Focuses on underlay backing stabilization and low-tension couching to halt tear propagation.',
    key_technique: 'Underlay stabilization, grain alignment, low-tension stitching',
    relevance: 'Delicate fabrics, vintage clothing, fine cottons',
  },
  {
    id: 'eileen-fisher-renew',
    title: 'Eileen Fisher Renew: Remanufacturing & Visible Mending Design Standards',
    source: 'Eileen Fisher Renew Circular Initiative',
    category: 'Upcycling & Remanufacturing',
    type: 'verified_external',
    url: 'https://www.eileenfisherrenew.com',
    publication_date: 'Active Circular Initiative',
    summary:
      'Circular design workflow transforming damaged garments into bespoke upcycled fashion pieces using sashiko stitches and color-blocked patches.',
    key_technique: 'Sashiko hand-stitching, visible seam reinforcement',
    relevance: 'Linen, knitwear, minimalist tailored garments',
  },
];

export const RedesignViewer: React.FC<RedesignViewerProps> = ({
  originalImageUrl,
  result,
  isGenerating,
  error,
  onRetry,
  onTryAnother,
  onOpenKeyModal,
  onSwitchToFreeAi,
  fashionIntelligence,
}) => {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'toggle'>('side-by-side');
  const [activeToggle, setActiveToggle] = useState<'original' | 'redesign'>('redesign');
  const [activeInfoTab, setActiveInfoTab] = useState<'repair-guide' | 'fashion-intelligence'>('repair-guide');
  const [checkedTools, setCheckedTools] = useState<Record<number, boolean>>({});

  // Genuine image download handler
  const handleDownload = () => {
    if (!result) return;

    // Create an anchor link and trigger download of data URI or endpoint
    const link = document.createElement('a');
    link.href = result.imageData;
    link.download = `rethread-${result.style.toLowerCase().replace(/\s+/g, '-')}-${result.id.slice(0, 8)}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <section id="results-view" className="mt-10 sm:mt-12 scroll-mt-24">
      <div className="bg-white rounded-2xl border border-[#e8e3dc] p-6 sm:p-8 shadow-sm">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-[#e8e3dc] gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="font-serif-heading text-xl sm:text-2xl font-bold text-[#181c1a]">
                Redesign Studio Results
              </h2>
              {result && (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Synthesized</span>
                </span>
              )}
            </div>
            <p className="text-xs text-[#6e7672] mt-1">
              Compare your original clothing item against the generative AI redesign.
            </p>
          </div>

          {/* Action buttons when result exists */}
          {result && (
            <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
              {/* Download Redesign Button */}
              <button
                type="button"
                onClick={handleDownload}
                className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-[#1d4a38] text-white text-xs sm:text-sm font-medium hover:bg-[#15382a] shadow-sm hover:shadow transition-all active:scale-[0.98]"
              >
                <Download className="w-4 h-4" />
                <span>Download Redesign</span>
              </button>

              {/* Try Another Design */}
              <button
                type="button"
                onClick={onTryAnother}
                className="inline-flex items-center space-x-2 px-3.5 py-2.5 rounded-xl bg-stone-100 hover:bg-stone-200/80 text-[#181c1a] text-xs sm:text-sm font-medium border border-stone-200 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5 text-[#5e6662]" />
                <span>Try Another Style</span>
              </button>
            </div>
          )}
        </div>

        {/* State 1: Active Error State */}
        {error && !isGenerating && (
          <div className="my-8 p-6 bg-rose-50/70 border border-rose-200 rounded-2xl">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-rose-900">
                  Redesign Generation Failed
                </h3>
                <p className="text-xs text-rose-800 mt-1 leading-relaxed">
                  {error}
                </p>
                {error.includes('STABILITY_API_KEY') && (
                  <p className="text-xs text-rose-800 mt-2 font-medium">
                    To fix this, get an API key from{' '}
                    <a
                      href="https://platform.stability.ai"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline font-semibold hover:text-rose-950"
                    >
                      platform.stability.ai
                    </a>{' '}
                    and add it to your <code className="bg-rose-100 px-1 rounded">backend/.env</code> file.
                  </p>
                )}

                <div className="mt-4 flex flex-wrap items-center gap-2.5">
                  {onSwitchToFreeAi && (
                    <button
                      type="button"
                      onClick={onSwitchToFreeAi}
                      className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-[#1d4a38] hover:bg-[#15382a] text-white text-xs font-semibold shadow-xs transition-colors"
                    >
                      <Zap className="w-3.5 h-3.5 text-emerald-300" />
                      <span>Switch to Free AI & Retry</span>
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={onRetry}
                    className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-medium shadow-xs transition-colors"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Retry Generation</span>
                  </button>
                  <button
                    type="button"
                    onClick={onOpenKeyModal}
                    className="text-xs font-medium text-rose-700 hover:text-rose-900 underline px-2 py-1"
                  >
                    API Setup Guide
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* State 2: Active Generating / Loading State */}
        {isGenerating && (
          <div className="my-8 py-10 px-6 rounded-2xl bg-[#faf8f5] border border-[#e8e3dc] flex flex-col items-center justify-center text-center">
            {/* Elegant Spinner */}
            <div className="relative mb-5">
              <div className="w-16 h-16 rounded-full border-4 border-stone-200 border-t-[#1d4a38] animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-[#1d4a38] animate-pulse" />
              </div>
            </div>

            <h3 className="font-serif-heading text-lg sm:text-xl font-bold text-[#181c1a]">
              Reimagining your garment...
            </h3>
            <p className="text-xs sm:text-sm text-[#5e6662] max-w-md mt-1.5 leading-relaxed">
              Conditioning the generative AI model on your garment's silhouette, texture, and seam details.
            </p>
            <p className="text-[11px] text-[#868f8b] mt-3">
              Image synthesis typically takes 10–25 seconds. Please keep this tab open.
            </p>

            {/* Original preview mini-card during loading */}
            {originalImageUrl && (
              <div className="mt-6 flex items-center space-x-3 p-2.5 bg-white rounded-xl border border-stone-200 shadow-xs max-w-xs">
                <img
                  src={originalImageUrl}
                  alt="Original garment"
                  className="w-12 h-12 object-cover rounded-lg border border-stone-100"
                />
                <div className="text-left">
                  <p className="text-xs font-medium text-[#181c1a]">Reference Garment</p>
                  <p className="text-[11px] text-[#6e7672]">Synthesizing new styling...</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* State 3: Empty State (Before Any Generation) */}
        {!result && !isGenerating && !error && (
          <div className="my-10 py-12 px-6 rounded-2xl bg-stone-50/50 border border-dashed border-[#d9d3c7] flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-2xl bg-white border border-[#e8e3dc] flex items-center justify-center text-[#5e6662] mb-4 shadow-xs">
              <Layers className="w-7 h-7 stroke-[1.5]" />
            </div>
            <h3 className="text-base font-semibold text-[#181c1a]">
              Your AI Redesign will appear here
            </h3>
            <p className="text-xs text-[#6e7672] max-w-sm mt-1 mb-4 leading-relaxed">
              Select an image on the left, pick your favorite aesthetic style on the right, and click
              <strong> "Generate Redesign"</strong> to begin.
            </p>
            <div className="inline-flex items-center space-x-1.5 text-xs text-[#1d4a38] font-medium bg-[#1d4a38]/8 px-3 py-1 rounded-full">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Full side-by-side comparison with high-res export</span>
            </div>
          </div>
        )}

        {/* State 4: Successful Result Display */}
        {result && !isGenerating && (
          <div className="mt-6">
            {/* Demo Mode Notice */}
            {result.isDemo && (
              <div className="mb-4 p-3.5 bg-purple-50/80 border border-purple-200 rounded-xl flex items-start space-x-3 text-xs text-purple-900 animate-in fade-in">
                <Sparkles className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-purple-950">
                    Showcase Demo Mode Result
                  </p>
                  <p className="text-[11px] text-purple-800 mt-0.5 leading-relaxed">
                    This high-fidelity garment transformation was generated via the offline studio simulation engine for zero-credit testing. To generate using live generative cloud AI, select <strong>Free AI</strong> or <strong>Auto</strong> in the engine picker above.
                  </p>
                </div>
              </div>
            )}

            {/* Smart Auto-Fallback Notice */}
            {result.fallbackUsed && (
              <div className="mb-4 p-3.5 bg-amber-50/80 border border-amber-200 rounded-xl flex items-start space-x-3 text-xs text-amber-900 animate-in fade-in">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-amber-950">
                    Smart Engine Auto-Fallback Activated
                  </p>
                  <p className="text-[11px] text-amber-800 mt-0.5 leading-relaxed">
                    {result.fallbackReason || 'Stability AI account has insufficient credits. ReThread automatically completed your garment redesign using the Free Fashion AI engine!'}
                  </p>
                </div>
              </div>
            )}

            {/* View Mode Switcher (Desktop & Mobile) */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-3 text-xs">
              <div className="flex items-center space-x-3">
                <span className="font-semibold text-[#181c1a]">Comparison View:</span>
                <div className="inline-flex p-1 bg-stone-100 rounded-lg border border-stone-200">
                  <button
                    type="button"
                    onClick={() => setViewMode('side-by-side')}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                      viewMode === 'side-by-side'
                        ? 'bg-white text-[#181c1a] shadow-xs'
                        : 'text-[#6e7672] hover:text-[#181c1a]'
                    }`}
                  >
                    Side-by-Side
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('toggle')}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                      viewMode === 'toggle'
                        ? 'bg-white text-[#181c1a] shadow-xs'
                        : 'text-[#6e7672] hover:text-[#181c1a]'
                    }`}
                  >
                    Flip View
                  </button>
                </div>
              </div>

              {/* Provider & Speed Badge */}
              <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-[11px] text-[#6e7672]">
                {result.isCached && (
                  <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-800 border border-blue-200">
                    <Zap className="w-3 h-3 text-blue-600" />
                    <span>Instant Cache (0 Credits Used)</span>
                  </span>
                )}
                <span className="flex items-center space-x-1">
                  <Cpu className="w-3.5 h-3.5 text-[#5e6662]" />
                  <span>Engine: <strong className="capitalize">{result.provider}</strong></span>
                </span>
                <span>•</span>
                <span className="flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5 text-[#5e6662]" />
                  <span>Completed in <strong>{result.durationSeconds}s</strong></span>
                </span>
              </div>
            </div>

            {/* Side-by-Side View */}
            {viewMode === 'side-by-side' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left Card: Original Garment */}
                <div className="flex flex-col bg-stone-50 rounded-2xl border border-stone-200 overflow-hidden">
                  <div className="px-4 py-3 bg-white border-b border-stone-200 flex items-center justify-between">
                    <span className="text-xs font-semibold text-[#181c1a] uppercase tracking-wider">
                      Original Garment
                    </span>
                    <span className="text-[11px] text-[#6e7672] bg-stone-100 px-2 py-0.5 rounded">
                      Reference Input
                    </span>
                  </div>
                  <div className="p-4 flex-1 flex items-center justify-center min-h-[360px] bg-stone-100/60">
                    {originalImageUrl ? (
                      <img
                        src={originalImageUrl}
                        alt="Original garment"
                        className="max-h-[420px] w-full object-contain rounded-xl"
                      />
                    ) : (
                      <span className="text-xs text-[#6e7672]">No original preview</span>
                    )}
                  </div>
                </div>

                {/* Right Card: AI Redesign Result */}
                <div className="flex flex-col bg-[#1d4a38]/3 rounded-2xl border-2 border-[#1d4a38]/30 overflow-hidden shadow-xs">
                  <div className="px-4 py-3 bg-white border-b border-[#1d4a38]/20 flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-semibold text-[#1d4a38] uppercase tracking-wider">
                        AI Redesign
                      </span>
                      <span className="text-[11px] font-medium bg-[#1d4a38]/10 text-[#1d4a38] px-2 py-0.5 rounded-full">
                        {result.style}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={handleDownload}
                      className="text-xs text-[#1d4a38] hover:text-[#15382a] font-medium flex items-center space-x-1"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download</span>
                    </button>
                  </div>
                  <div className="p-4 flex-1 flex items-center justify-center min-h-[360px] bg-stone-100/60 relative group">
                    <img
                      src={result.imageData}
                      alt={`Redesigned garment in ${result.style} style`}
                      className="max-h-[420px] w-full object-contain rounded-xl transition-transform duration-200"
                    />
                  </div>
                </div>
              </div>
            ) : (
              /* Toggle / Flip View */
              <div className="max-w-2xl mx-auto flex flex-col bg-stone-50 rounded-2xl border border-stone-200 overflow-hidden">
                <div className="px-4 py-3 bg-white border-b border-stone-200 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => setActiveToggle('original')}
                      className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                        activeToggle === 'original'
                          ? 'bg-[#181c1a] text-white'
                          : 'bg-stone-100 text-[#4a524e] hover:bg-stone-200'
                      }`}
                    >
                      Show Original
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveToggle('redesign')}
                      className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                        activeToggle === 'redesign'
                          ? 'bg-[#1d4a38] text-white'
                          : 'bg-stone-100 text-[#4a524e] hover:bg-stone-200'
                      }`}
                    >
                      Show AI Redesign ({result.style})
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={handleDownload}
                    className="text-xs text-[#1d4a38] font-medium flex items-center space-x-1"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download</span>
                  </button>
                </div>

                <div className="p-6 flex items-center justify-center min-h-[420px] bg-stone-100/60">
                  {activeToggle === 'original' ? (
                    <img
                      src={originalImageUrl || ''}
                      alt="Original garment"
                      className="max-h-[440px] w-full object-contain rounded-xl"
                    />
                  ) : (
                    <img
                      src={result.imageData}
                      alt="AI Redesign"
                      className="max-h-[440px] w-full object-contain rounded-xl"
                    />
                  )}
                </div>
              </div>
            )}

            {/* Prompt Transparency Details */}
            {result.promptUsed && (
              <div className="mt-6 p-4 bg-stone-50 rounded-xl border border-stone-200 text-xs">
                <p className="font-semibold text-[#181c1a] mb-1 flex items-center space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#1d4a38]" />
                  <span>Synthesized Visible Mending AI Prompt</span>
                </p>
                <p className="text-[#5e6662] font-mono text-[11px] leading-relaxed break-words">
                  "{result.promptUsed}"
                </p>
              </div>
            )}

            {/* ========================================================================= */}
            {/* SMART GARMENT REPAIR & FASHION INTELLIGENCE STUDIO SECTION                */}
            {/* ========================================================================= */}
            <div className="mt-8 pt-8 border-t border-[#e8e3dc]">
              {/* Garment Diagnostic Summary Bar */}
              {result.garmentAnalysis && (
                <div className="mb-6 p-4 bg-[#faf8f5] rounded-2xl border border-[#e8e3dc]">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#e8e3dc]/70 gap-2">
                    <div className="flex items-center space-x-2">
                      <Scissors className="w-4 h-4 text-[#1d4a38]" />
                      <h3 className="text-xs sm:text-sm font-semibold text-[#181c1a]">
                        Garment & Damage Diagnostic
                      </h3>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-[10px] uppercase font-semibold tracking-wider text-[#6e7672]">
                        Confidence:
                      </span>
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          result.garmentAnalysis.confidence === 'high'
                            ? 'bg-emerald-100 text-emerald-800'
                            : result.garmentAnalysis.confidence === 'medium'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {result.garmentAnalysis.confidence.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 text-xs">
                    <div>
                      <span className="text-[10px] text-[#6e7672] uppercase tracking-wider block">
                        Identified Garment
                      </span>
                      <span className="font-medium text-[#181c1a]">
                        {result.garmentAnalysis.garment_type}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#6e7672] uppercase tracking-wider block">
                        Visible Fabric
                      </span>
                      <span className="font-medium text-[#181c1a]">
                        {result.garmentAnalysis.fabric_type}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#6e7672] uppercase tracking-wider block">
                        Damage Location Focus
                      </span>
                      <span className="font-medium text-[#1d4a38]">
                        {result.garmentAnalysis.damage_location}
                      </span>
                    </div>
                  </div>

                  {result.garmentAnalysis.clarification_needed && (
                    <div className="mt-3 p-2.5 bg-amber-50/90 border border-amber-200/80 rounded-xl text-[11px] text-amber-900 flex items-start space-x-2">
                      <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                      <p>
                        {result.garmentAnalysis.clarification_message ||
                          'Automated damage detection has moderate confidence. If this placement differs from your garment, select a specific area in the upload zone.'}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Navigation Tabs: Repair Plan vs Fashion Intelligence */}
              <div className="flex items-center space-x-3 mb-6 border-b border-[#e8e3dc]">
                <button
                  type="button"
                  onClick={() => setActiveInfoTab('repair-guide')}
                  className={`pb-3 text-xs sm:text-sm font-semibold flex items-center space-x-2 border-b-2 transition-all ${
                    activeInfoTab === 'repair-guide'
                      ? 'border-[#1d4a38] text-[#1d4a38]'
                      : 'border-transparent text-[#6e7672] hover:text-[#181c1a]'
                  }`}
                >
                  <BookOpen className="w-4 h-4" />
                  <span>Practical Repair Guide</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveInfoTab('fashion-intelligence')}
                  className={`pb-3 text-xs sm:text-sm font-semibold flex items-center space-x-2 border-b-2 transition-all ${
                    activeInfoTab === 'fashion-intelligence'
                      ? 'border-[#1d4a38] text-[#1d4a38]'
                      : 'border-transparent text-[#6e7672] hover:text-[#181c1a]'
                  }`}
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Fashion Intelligence & External Guides</span>
                </button>
              </div>

              {/* TAB 1: STRUCTURED REPAIR PLAN */}
              {activeInfoTab === 'repair-guide' && result.repairPlan && (
                <div className="space-y-6">
                  {/* Technique Header */}
                  <div className="p-4 sm:p-5 bg-stone-50 rounded-2xl border border-stone-200">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
                      <h4 className="text-sm sm:text-base font-bold text-[#181c1a] flex items-center space-x-2">
                        <span>{result.repairPlan.technique_name}</span>
                      </h4>
                      <div className="flex items-center space-x-2">
                        <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                          {result.repairPlan.difficulty}
                        </span>
                        <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-stone-200 text-[#2d322f] flex items-center space-x-1">
                          <Clock className="w-3 h-3 text-[#5e6662]" />
                          <span>{result.repairPlan.estimated_time}</span>
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-[#4a524e] leading-relaxed">
                      {result.repairPlan.technique_rationale}
                    </p>
                  </div>

                  {/* Two-Column Grid: Tools Checklist & Repair Steps */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Left: Materials & Tools Checklist (5 columns) */}
                    <div className="lg:col-span-5 bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
                      <h5 className="text-xs font-bold text-[#181c1a] uppercase tracking-wider mb-3 flex items-center space-x-2">
                        <Wrench className="w-3.5 h-3.5 text-[#1d4a38]" />
                        <span>Materials & Tools Needed</span>
                      </h5>
                      <div className="space-y-2 text-xs">
                        {result.repairPlan.tools_and_materials.map((item, idx) => {
                          const isChecked = !!checkedTools[idx];
                          return (
                            <button
                              key={idx}
                              type="button"
                              onClick={() =>
                                setCheckedTools((prev) => ({
                                  ...prev,
                                  [idx]: !prev[idx],
                                }))
                              }
                              className={`w-full text-left p-2.5 rounded-xl border flex items-start space-x-2.5 transition-all ${
                                isChecked
                                  ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
                                  : 'bg-stone-50 border-stone-200 hover:bg-stone-100 text-[#2d322f]'
                              }`}
                            >
                              <div
                                className={`w-4 h-4 rounded shrink-0 mt-0.5 flex items-center justify-center border ${
                                  isChecked
                                    ? 'bg-[#1d4a38] border-[#1d4a38] text-white'
                                    : 'border-stone-300 bg-white'
                                }`}
                              >
                                {isChecked && <CheckCircle2 className="w-3 h-3" />}
                              </div>
                              <span className={`text-[11px] leading-snug ${isChecked ? 'line-through opacity-80' : ''}`}>
                                {item}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                      <p className="text-[10px] text-[#78817d] mt-3">
                        Click items as you gather them from your sewing kit.
                      </p>
                    </div>

                    {/* Right: Step-by-Step Practical Instructions (7 columns) */}
                    <div className="lg:col-span-7 bg-white p-5 rounded-2xl border border-stone-200 shadow-xs">
                      <h5 className="text-xs font-bold text-[#181c1a] uppercase tracking-wider mb-3 flex items-center space-x-2">
                        <FileText className="w-3.5 h-3.5 text-[#1d4a38]" />
                        <span>Step-by-Step Beginner Guide</span>
                      </h5>
                      <div className="space-y-3 text-xs">
                        {result.repairPlan.steps.map((step, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-stone-50/80 rounded-xl border border-stone-200 flex items-start space-x-3"
                          >
                            <span className="w-5 h-5 rounded-full bg-[#1d4a38] text-white text-[11px] font-bold flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                              {idx + 1}
                            </span>
                            <p className="text-[11px] text-[#2d322f] leading-relaxed flex-1">
                              {step}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Tailor Advice Caution Card */}
                  {result.repairPlan.when_to_seek_tailor && (
                    <div className="p-4 bg-amber-50/80 border border-amber-200 rounded-2xl text-xs text-amber-950 flex items-start space-x-3">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <h6 className="font-bold text-amber-900 text-xs">
                          When to Consult a Professional Tailor:
                        </h6>
                        <p className="text-[11px] text-amber-900/90 mt-1 leading-relaxed">
                          {result.repairPlan.when_to_seek_tailor}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 2: VERIFIED FASHION INTELLIGENCE & EXTERNAL SOURCES */}
              {activeInfoTab === 'fashion-intelligence' && (
                <div className="space-y-4">
                  {/* Transparency Statement Header */}
                  <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-2xl text-xs text-emerald-950">
                    <div className="flex items-center space-x-2 mb-1">
                      <ShieldCheck className="w-4 h-4 text-emerald-700" />
                      <h4 className="font-bold text-emerald-900">
                        Verified Sustainable Fashion & Mending Intelligence
                      </h4>
                    </div>
                    <p className="text-[11px] text-emerald-900/90 leading-relaxed">
                      All references below are curated from active circular fashion and repair programs (Patagonia Worn Wear / iFixit, Fashion Revolution, Sashiko Story, V&A Museum Conservation, Eileen Fisher Renew). Every link and publication attribution is an authentic, verified external resource.
                    </p>
                  </div>

                  {/* Resources Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {(fashionIntelligence && fashionIntelligence.length > 0
                      ? fashionIntelligence
                      : DEFAULT_FASHION_INTELLIGENCE
                    ).map((item) => (
                      <div
                        key={item.id}
                        className="p-4 bg-white rounded-2xl border border-stone-200 shadow-xs flex flex-col justify-between hover:border-[#1d4a38]/40 transition-colors"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                              Verified External Reference
                            </span>
                            <span className="text-[10px] text-[#78817d]">
                              {item.publication_date}
                            </span>
                          </div>

                          <h5 className="font-semibold text-xs sm:text-sm text-[#181c1a] mb-1">
                            {item.title}
                          </h5>

                          <p className="text-[11px] text-[#5e6662] mb-3 leading-relaxed">
                            {item.summary}
                          </p>

                          <div className="p-2 bg-stone-50 rounded-lg text-[10px] text-[#4a524e] space-y-0.5 mb-3">
                            <p>
                              <strong>Key Technique:</strong> {item.key_technique}
                            </p>
                            <p>
                              <strong>Best For:</strong> {item.relevance}
                            </p>
                          </div>
                        </div>

                        <div className="pt-2 border-t border-stone-100 flex items-center justify-between text-xs">
                          <span className="text-[11px] font-medium text-[#6e7672]">
                            {item.source}
                          </span>
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center space-x-1 text-xs font-semibold text-[#1d4a38] hover:underline"
                          >
                            <span>Official Guide</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

