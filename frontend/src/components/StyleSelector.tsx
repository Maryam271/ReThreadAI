import React from 'react';
import {
  Sparkles,
  Scissors,
  Flower2,
  Minus,
  Clock,
  Palette,
  Edit3,
  Sliders,
  Flame,
  ArrowRight,
  Loader2,
  Zap,
} from 'lucide-react';
import type { StylePreset, StyleOption, EngineMode } from '../types';

interface StyleSelectorProps {
  selectedStyle: StylePreset;
  onSelectStyle: (style: StylePreset) => void;
  selectedEngine: EngineMode;
  onSelectEngine: (engine: EngineMode) => void;
  customPrompt: string;
  onCustomPromptChange: (val: string) => void;
  strength: number;
  onStrengthChange: (val: number) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  hasImage: boolean;
}

const STYLE_OPTIONS: StyleOption[] = [
  {
    id: 'Streetwear',
    title: 'Streetwear',
    tagline: 'Urban Utility & Graphic',
    iconName: 'Flame',
    description: 'Bold urban textures, elevated streetwear graphics, tasteful distressing.',
  },
  {
    id: 'Floral Embroidery',
    title: 'Floral Embroidery',
    tagline: 'Artisanal Botanical Needlework',
    iconName: 'Flower2',
    description: 'Intricate botanical wildflower embroidery stitched into the fabric.',
  },
  {
    id: 'Minimalist',
    title: 'Minimalist',
    tagline: 'Quiet Luxury & Clean Lines',
    iconName: 'Minus',
    description: 'Understated elegance, streamlined silhouette, and tone-on-tone textures.',
  },
  {
    id: 'Vintage',
    title: 'Vintage',
    tagline: 'Retro Fade & Heritage Stitch',
    iconName: 'Clock',
    description: 'Classic heritage styling, gentle sun-fade wash, and nostalgic patina.',
  },
  {
    id: 'Patchwork',
    title: 'Patchwork',
    tagline: 'Upcycled Sashiko Textile',
    iconName: 'Scissors',
    description: 'Artfully placed contrasting fabric swatches and visible repair stitches.',
  },
  {
    id: 'Artistic',
    title: 'Artistic',
    tagline: 'Painterly Wearable Art',
    iconName: 'Palette',
    description: 'Expressive brushstroke dye motifs and avant-garde textile accents.',
  },
  {
    id: 'Custom',
    title: 'Custom',
    tagline: 'Bespoke Prompt Vision',
    iconName: 'Edit3',
    description: 'Create your own unique transformation with a tailored text instruction.',
  },
];

export const StyleSelector: React.FC<StyleSelectorProps> = ({
  selectedStyle,
  onSelectStyle,
  selectedEngine,
  onSelectEngine,
  customPrompt,
  onCustomPromptChange,
  strength,
  onStrengthChange,
  onGenerate,
  isGenerating,
  hasImage,
}) => {
  const renderIcon = (name: string, isSelected: boolean) => {
    const className = `w-4 h-4 ${isSelected ? 'text-[#1d4a38]' : 'text-[#6e7672]'}`;
    switch (name) {
      case 'Flame':
        return <Flame className={className} />;
      case 'Flower2':
        return <Flower2 className={className} />;
      case 'Minus':
        return <Minus className={className} />;
      case 'Clock':
        return <Clock className={className} />;
      case 'Scissors':
        return <Scissors className={className} />;
      case 'Palette':
        return <Palette className={className} />;
      case 'Edit3':
        return <Edit3 className={className} />;
      default:
        return <Sparkles className={className} />;
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-[#e8e3dc] p-5 sm:p-6 shadow-sm flex flex-col h-full">
      {/* Header */}
      <div className="mb-4">
        <h2 className="text-base sm:text-lg font-semibold text-[#181c1a] flex items-center space-x-2">
          <span>Design Controls</span>
          <span className="text-xs font-medium text-[#1d4a38] bg-[#1d4a38]/8 px-2 py-0.5 rounded-full">
            AI Parameters
          </span>
        </h2>
        <p className="text-xs text-[#6e7672] mt-0.5">
          Choose a style direction and refine your custom vision below.
        </p>
      </div>

      {/* Engine Mode Selection */}
      <div className="mb-5 p-3 bg-stone-50 rounded-xl border border-stone-200/80">
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs font-semibold text-[#282d2a] uppercase tracking-wider flex items-center space-x-1.5">
            <Zap className="w-3.5 h-3.5 text-[#1d4a38]" />
            <span>AI Engine</span>
          </label>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium">
            Zero Credit Burn
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-xs">
          <button
            type="button"
            onClick={() => onSelectEngine('auto')}
            disabled={isGenerating}
            className={`p-2 rounded-lg border text-left transition-all ${
              selectedEngine === 'auto'
                ? 'bg-[#1d4a38] text-white border-[#1d4a38] shadow-xs'
                : 'bg-white text-stone-700 border-stone-200 hover:bg-stone-100'
            }`}
          >
            <div className="font-semibold text-[11px] leading-tight">⚡ Auto</div>
            <div className="text-[9px] opacity-80 mt-0.5">Smart Fallback</div>
          </button>

          <button
            type="button"
            onClick={() => onSelectEngine('free')}
            disabled={isGenerating}
            className={`p-2 rounded-lg border text-left transition-all ${
              selectedEngine === 'free'
                ? 'bg-[#1d4a38] text-white border-[#1d4a38] shadow-xs'
                : 'bg-white text-stone-700 border-stone-200 hover:bg-stone-100'
            }`}
          >
            <div className="font-semibold text-[11px] leading-tight">🆓 Free AI</div>
            <div className="text-[9px] opacity-80 mt-0.5">100% Free / Fast</div>
          </button>

          <button
            type="button"
            onClick={() => onSelectEngine('demo')}
            disabled={isGenerating}
            className={`p-2 rounded-lg border text-left transition-all ${
              selectedEngine === 'demo'
                ? 'bg-[#1d4a38] text-white border-[#1d4a38] shadow-xs'
                : 'bg-white text-stone-700 border-stone-200 hover:bg-stone-100'
            }`}
          >
            <div className="font-semibold text-[11px] leading-tight">🎨 Demo Mode</div>
            <div className="text-[9px] opacity-80 mt-0.5">Instant Offline</div>
          </button>

          <button
            type="button"
            onClick={() => onSelectEngine('stability')}
            disabled={isGenerating}
            className={`p-2 rounded-lg border text-left transition-all ${
              selectedEngine === 'stability'
                ? 'bg-[#1d4a38] text-white border-[#1d4a38] shadow-xs'
                : 'bg-white text-stone-700 border-stone-200 hover:bg-stone-100'
            }`}
          >
            <div className="font-semibold text-[11px] leading-tight">🔑 Stability</div>
            <div className="text-[9px] opacity-80 mt-0.5">Paid SD3.5</div>
          </button>
        </div>
      </div>

      {/* Style Presets Grid */}
      <div className="mb-5">
        <label className="block text-xs font-semibold text-[#282d2a] mb-2 uppercase tracking-wider">
          1. Select Redesign Style
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {STYLE_OPTIONS.map((style) => {
            const isSelected = selectedStyle === style.id;
            return (
              <button
                key={style.id}
                type="button"
                onClick={() => onSelectStyle(style.id)}
                disabled={isGenerating}
                className={`p-3 rounded-xl text-left border transition-all relative ${
                  isSelected
                    ? 'border-[#1d4a38] bg-[#1d4a38]/5 ring-1 ring-[#1d4a38]/20 shadow-xs'
                    : 'border-[#e8e3dc] hover:border-stone-300 bg-white hover:bg-stone-50/60'
                } ${isGenerating ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                <div className="flex items-center space-x-2.5 mb-1">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                      isSelected ? 'bg-white shadow-xs' : 'bg-stone-100'
                    }`}
                  >
                    {renderIcon(style.iconName, isSelected)}
                  </div>
                  <span
                    className={`text-xs font-semibold ${
                      isSelected ? 'text-[#1d4a38]' : 'text-[#181c1a]'
                    }`}
                  >
                    {style.title}
                  </span>
                </div>
                <p className="text-[11px] text-[#6e7672] line-clamp-1 leading-snug">
                  {style.tagline}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Custom Vision Text Area */}
      <div className="mb-5 flex-1">
        <label
          htmlFor="custom-vision-prompt"
          className="block text-xs font-semibold text-[#282d2a] mb-1.5 uppercase tracking-wider flex items-center justify-between"
        >
          <span>2. Describe your vision (Optional)</span>
          <span className="text-[11px] font-normal text-[#6e7672]">
            {customPrompt.length}/250
          </span>
        </label>
        <textarea
          id="custom-vision-prompt"
          rows={3}
          maxLength={250}
          value={customPrompt}
          onChange={(e) => onCustomPromptChange(e.target.value)}
          disabled={isGenerating}
          placeholder="Example: Add subtle floral embroidery to the torn knee area while keeping the original denim color."
          className="w-full text-xs text-[#181c1a] placeholder:text-[#9aa09d] p-3 rounded-xl border border-[#e8e3dc] focus:border-[#1d4a38] focus:ring-1 focus:ring-[#1d4a38] outline-hidden bg-stone-50/50 resize-none transition-colors"
        />
        <p className="text-[11px] text-[#6e7672] mt-1">
          Specify exact embroidery motifs, distressing locations, or accent shades.
        </p>
      </div>

      {/* Redesign Intensity Slider (Advanced Control) */}
      <div className="mb-6 p-3 bg-stone-50/80 rounded-xl border border-stone-200/80">
        <div className="flex items-center justify-between text-xs mb-1.5">
          <span className="font-medium text-[#2d322f] flex items-center space-x-1.5">
            <Sliders className="w-3.5 h-3.5 text-[#5e6662]" />
            <span>Redesign Transformation Strength</span>
          </span>
          <span className="font-mono text-xs text-[#1d4a38] font-semibold">
            {Math.round(strength * 100)}%
          </span>
        </div>
        <input
          type="range"
          min="0.4"
          max="0.85"
          step="0.05"
          value={strength}
          onChange={(e) => onStrengthChange(parseFloat(e.target.value))}
          disabled={isGenerating}
          className="w-full h-1.5 bg-stone-200 rounded-lg appearance-none cursor-pointer accent-[#1d4a38]"
        />
        <div className="flex justify-between text-[10px] text-[#78817d] mt-1">
          <span>Subtle Accent (Preserve 100% form)</span>
          <span>Bold Redesign</span>
        </div>
      </div>

      {/* Generate Action Button */}
      <div>
        <button
          type="button"
          onClick={onGenerate}
          disabled={!hasImage || isGenerating}
          className={`w-full py-3.5 px-5 rounded-xl font-medium text-sm flex items-center justify-center space-x-2 transition-all duration-150 ${
            !hasImage
              ? 'bg-stone-200 text-stone-500 cursor-not-allowed border border-stone-300'
              : isGenerating
              ? 'bg-[#15382a] text-white cursor-wait opacity-90'
              : 'bg-[#1d4a38] hover:bg-[#15382a] text-white shadow-sm hover:shadow active:scale-[0.99]'
          }`}
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Reimagining your garment...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Generate Redesign</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>

        {!hasImage && (
          <p className="text-[11px] text-center text-[#6e7672] mt-2">
            Please upload a garment image on the left to enable generation.
          </p>
        )}
      </div>
    </div>
  );
};
