import React from 'react';
import { X, ExternalLink, CheckCircle, Shield, AlertCircle, Zap, Sparkles } from 'lucide-react';
import type { HealthStatus } from '../types';

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  health: HealthStatus | null;
  onRefreshHealth: () => void;
}

export const ApiKeyModal: React.FC<ApiKeyModalProps> = ({
  isOpen,
  onClose,
  health,
  onRefreshHealth,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl max-w-lg w-full border border-[#e8e3dc] shadow-xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-stone-50 border-b border-[#e8e3dc] flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#1d4a38]/10 text-[#1d4a38] flex items-center justify-center">
              <Zap className="w-4 h-4 text-[#1d4a38]" />
            </div>
            <h3 className="font-semibold text-sm sm:text-base text-[#181c1a]">
              AI Engine & API Setup Guide
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-stone-200/60 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 text-xs sm:text-sm text-[#2d322f] space-y-4 max-h-[80vh] overflow-y-auto">
          {/* Current Connection Status */}
          <div className="p-3.5 rounded-xl border bg-emerald-50 border-emerald-200 text-emerald-900 flex items-start space-x-3">
            <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">
                Multi-Engine AI Ready For Submission
              </p>
              <p className="text-xs mt-0.5 opacity-90">
                Active Default Mode:{' '}
                <strong className="uppercase">
                  {health?.active_provider || 'AUTO'}
                </strong>
                . Includes built-in Free Cloud Fashion AI and instant Demo Showcase Mode.
              </p>
            </div>
          </div>

          {/* Explanation: Why did new Stability API key fail? */}
          <div className="p-3.5 bg-amber-50/80 border border-amber-200 rounded-xl space-y-1.5 text-xs text-amber-950">
            <div className="flex items-center space-x-1.5 font-bold text-amber-900">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Why Stability AI gave "Insufficient Credits":</span>
            </div>
            <p className="text-[#3b3a36] leading-relaxed">
              Stability AI keys are bound to your account credit balance. Stability AI no longer gives free generation credits on new accounts. Generating a new API key on an account with 0 credits still returns <strong>402 Payment Required</strong> until credits are purchased.
            </p>
          </div>

          {/* Solution 1: Built-in Free AI Engine */}
          <div className="p-3.5 bg-emerald-50/50 border border-emerald-200/80 rounded-xl space-y-1.5 text-xs text-emerald-950">
            <div className="flex items-center space-x-1.5 font-bold text-emerald-900">
              <Zap className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Recommended: Use Built-in Free Fashion AI (No Credits Needed)</span>
            </div>
            <p className="text-[#2b3831] leading-relaxed">
              ReThread AI includes a high-speed generative fashion AI engine that requires <strong>0 API credits, 0 credit cards, and no paid setup</strong>. Simply select <strong>Free AI</strong> or <strong>Auto</strong> in the Design Controls engine picker.
            </p>
          </div>

          {/* Solution 2: Demo Mode for Hackathon Judging */}
          <div className="p-3.5 bg-purple-50/50 border border-purple-200/80 rounded-xl space-y-1.5 text-xs text-purple-950">
            <div className="flex items-center space-x-1.5 font-bold text-purple-900">
              <Sparkles className="w-4 h-4 text-purple-600 shrink-0" />
              <span>Guaranteed Presentation: Studio Demo Mode</span>
            </div>
            <p className="text-[#3b2b3a] leading-relaxed">
              If evaluating offline or during a live judge presentation where Wi-Fi might drop, select <strong>Demo Mode</strong>. It applies instant artisanal garment styling filters and never fails.
            </p>
          </div>

          {/* Optional: Paid Stability Setup */}
          <div className="space-y-2 pt-1 border-t border-stone-200">
            <h4 className="text-xs font-bold text-[#181c1a] uppercase tracking-wider">
              Optional: Using Paid Stability AI SD3.5
            </h4>
            <div className="p-3 bg-stone-50 rounded-xl border border-stone-200 space-y-1.5 text-xs">
              <p className="text-[#5e6662]">
                1. Top up credits ($10 minimum) at:
              </p>
              <a
                href="https://platform.stability.ai/account/credits"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-1 text-[#1d4a38] hover:underline font-semibold"
              >
                <span>platform.stability.ai/account/credits</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              <p className="text-[#5e6662] pt-1">
                2. Paste your funded key into <code className="bg-stone-200 px-1 py-0.5 rounded font-mono text-[11px]">backend/.env</code>:
              </p>
              <div className="bg-[#181c1a] text-stone-200 p-2 rounded-lg font-mono text-[11px] overflow-x-auto">
                STABILITY_API_KEY=sk-your_funded_key_here
              </div>
            </div>
          </div>

          {/* Security note */}
          <div className="p-3 bg-blue-50/60 border border-blue-200/80 rounded-xl text-xs text-blue-900 flex items-start space-x-2">
            <Shield className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <p>
              <strong>Security Guarantee:</strong> All keys are strictly stored on your local backend server in <code className="bg-blue-100 px-1 rounded">.env</code> and are never leaked to frontend bundles.
            </p>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-stone-50 border-t border-[#e8e3dc] flex items-center justify-between">
          <button
            type="button"
            onClick={onRefreshHealth}
            className="text-xs font-semibold text-[#1d4a38] hover:underline"
          >
            Check Status Now
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#1d4a38] hover:bg-[#15382a] text-white text-xs font-medium transition-colors shadow-xs"
          >
            Got It
          </button>
        </div>
      </div>
    </div>
  );
};
