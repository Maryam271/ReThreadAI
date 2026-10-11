import React from 'react';
import { ArrowDown, Sparkles } from 'lucide-react';

interface HeroProps {
  onScrollToWorkspace: () => void;
}

export const Hero: React.FC<HeroProps> = ({ onScrollToWorkspace }) => {
  return (
    <section className="relative pt-8 pb-10 sm:pt-12 sm:pb-12 text-center max-w-4xl mx-auto px-4 sm:px-6">
      {/* Subtle pill tag */}
      <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-[#1d4a38]/8 border border-[#1d4a38]/15 text-[#1d4a38] text-xs font-semibold tracking-wide uppercase mb-4">
        <Sparkles className="w-3.5 h-3.5 text-[#1d4a38]" />
        <span>Sustainable Generative Fashion</span>
      </div>

      {/* Main Headline */}
      <h1 className="font-serif-heading text-3xl sm:text-4xl md:text-5xl font-bold text-[#181c1a] tracking-tight leading-tight sm:leading-tight mb-4">
        Give Your Clothes a Second Life.
      </h1>

      {/* Supporting Text */}
      <p className="text-base sm:text-lg text-[#525a56] max-w-2xl mx-auto font-normal leading-relaxed mb-6">
        Upload a garment. Reimagine its style. Discover a new look with AI.
      </p>

      {/* Compact CTAs and Steps */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
        <button
          onClick={onScrollToWorkspace}
          className="inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-xl bg-[#1d4a38] text-white font-medium text-sm hover:bg-[#15382a] shadow-sm hover:shadow transition-all duration-150 active:scale-[0.98]"
        >
          <span>Start Redesign Studio</span>
          <ArrowDown className="w-4 h-4 animate-bounce" />
        </button>
      </div>

      {/* 4-Step Visual Journey Flow */}
      <div className="mt-8 pt-6 border-t border-[#e8e3dc]/80 grid grid-cols-2 md:grid-cols-4 gap-3 text-left">
        <div className="p-2.5 rounded-lg bg-white/60 border border-stone-200/60">
          <span className="text-[11px] font-semibold text-[#1d4a38] block uppercase tracking-wider">Step 1</span>
          <p className="text-xs text-[#2b302d] font-medium mt-0.5">Upload Garment</p>
          <p className="text-[11px] text-[#6e7672]">JPEG, PNG, WebP photo</p>
        </div>
        <div className="p-2.5 rounded-lg bg-white/60 border border-stone-200/60">
          <span className="text-[11px] font-semibold text-[#1d4a38] block uppercase tracking-wider">Step 2</span>
          <p className="text-xs text-[#2b302d] font-medium mt-0.5">Select Style</p>
          <p className="text-[11px] text-[#6e7672]">Streetwear, Vintage & more</p>
        </div>
        <div className="p-2.5 rounded-lg bg-white/60 border border-stone-200/60">
          <span className="text-[11px] font-semibold text-[#1d4a38] block uppercase tracking-wider">Step 3</span>
          <p className="text-xs text-[#2b302d] font-medium mt-0.5">Generate Redesign</p>
          <p className="text-[11px] text-[#6e7672]">Conditioned image synthesis</p>
        </div>
        <div className="p-2.5 rounded-lg bg-white/60 border border-stone-200/60">
          <span className="text-[11px] font-semibold text-[#1d4a38] block uppercase tracking-wider">Step 4</span>
          <p className="text-xs text-[#2b302d] font-medium mt-0.5">Compare & Download</p>
          <p className="text-[11px] text-[#6e7672]">High-res result export</p>
        </div>
      </div>
    </section>
  );
};
