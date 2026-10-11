import React from 'react';
import { RotateCcw, Key, ShieldCheck, AlertCircle } from 'lucide-react';
import type { HealthStatus } from '../types';

interface HeaderProps {
  health: HealthStatus | null;
  onReset: () => void;
  onOpenKeyModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, onReset, onOpenKeyModal }) => {
  const isConfigured = health?.ai_configured ?? false;

  return (
    <header className="sticky top-0 z-40 bg-[#faf8f5]/90 backdrop-blur-md border-b border-[#e8e3dc] transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand Logo & Wordmark */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-[#1d4a38] text-white flex items-center justify-center shadow-sm">
            <svg
              className="w-5 h-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              {/* Garment silhouette with stitch needle */}
              <path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-serif-heading text-xl sm:text-2xl font-bold tracking-tight text-[#181c1a]">
                ReThread AI
              </span>
              <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-[#1d4a38]/10 text-[#1d4a38] tracking-wider uppercase">
                MVP Studio
              </span>
            </div>
            <p className="text-xs text-[#6e7672] font-normal tracking-wide">
              AI Clothing Redesign Studio
            </p>
          </div>
        </div>

        {/* Header Right Actions */}
        <div className="flex items-center space-x-3">
          {/* AI Backend Status Badge */}
          <button
            onClick={onOpenKeyModal}
            className={`hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
              isConfigured
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100'
                : 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100'
            }`}
            title="Click to check or configure AI provider settings"
          >
            {isConfigured ? (
              <>
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>
                  AI Ready:{' '}
                  <strong className="capitalize">
                    {health?.active_provider === 'auto'
                      ? 'Auto (Free AI Ready)'
                      : health?.active_provider === 'free'
                      ? 'Free Fashion AI'
                      : health?.active_provider || 'Ready'}
                  </strong>
                </span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
                <span>Configure API Key</span>
              </>
            )}
          </button>

          {/* Quick API Key Setup Modal Trigger for mobile/desktop */}
          <button
            onClick={onOpenKeyModal}
            className="md:hidden p-2 rounded-lg text-[#5e6662] hover:text-[#181c1a] hover:bg-stone-200/50 transition-colors"
            title="API Setup"
            aria-label="API Settings"
          >
            <Key className="w-4 h-4" />
          </button>

          {/* Reset Workspace Action */}
          <button
            onClick={onReset}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-medium text-[#4a524e] bg-stone-100 hover:bg-stone-200/80 rounded-lg transition-colors border border-stone-200"
            title="Start fresh with a new garment"
          >
            <RotateCcw className="w-3.5 h-3.5 text-[#5e6662]" />
            <span className="hidden sm:inline">New Design</span>
            <span className="sm:hidden">Reset</span>
          </button>
        </div>
      </div>
    </header>
  );
};
