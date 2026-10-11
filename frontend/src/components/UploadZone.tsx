import React, { useRef, useState, useCallback } from 'react';
import {
  UploadCloud,
  Trash2,
  RefreshCw,
  AlertCircle,
  FileCheck,
  Target,
  Crosshair,
  MapPin,
  X,
  Sliders,
  CheckCircle2,
} from 'lucide-react';
import type { DamageFocusPoint } from '../types';

interface UploadZoneProps {
  imageFile: File | null;
  imagePreviewUrl: string | null;
  onImageSelected: (file: File) => void;
  onImageRemoved: () => void;
  damageLocation: string;
  onDamageLocationChange: (loc: string) => void;
  damageFocus?: DamageFocusPoint | null;
  onDamageFocusChange?: (focus: DamageFocusPoint | null) => void;
  disabled?: boolean;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

// Curated sample clothing SVG images so the user can test with 1-click
const SAMPLE_GARMENTS = [
  {
    name: 'Denim Jacket',
    type: 'image/png',
    svgData: `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
      <rect width="600" height="600" fill="#f0ebe1"/>
      <!-- Denim jacket silhouette -->
      <path d="M 230 110 L 300 150 L 370 110 L 490 200 L 450 320 L 400 290 L 400 490 L 200 490 L 200 290 L 150 320 L 110 200 Z" fill="#3b5d7a" stroke="#253e54" stroke-width="6"/>
      <!-- Collar -->
      <path d="M 230 110 L 300 170 L 370 110 L 300 130 Z" fill="#2c4760"/>
      <!-- Chest pockets -->
      <rect x="220" y="220" width="60" height="60" rx="6" fill="#345470" stroke="#253e54" stroke-width="4"/>
      <rect x="320" y="220" width="60" height="60" rx="6" fill="#345470" stroke="#253e54" stroke-width="4"/>
      <!-- Center button placket -->
      <line x1="300" y1="170" x2="300" y2="490" stroke="#253e54" stroke-width="4" stroke-dasharray="16,8"/>
    </svg>`,
  },
  {
    name: 'Cotton White T-Shirt',
    type: 'image/png',
    svgData: `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
      <rect width="600" height="600" fill="#f0ebe1"/>
      <!-- T-shirt silhouette -->
      <path d="M 230 120 C 270 150, 330 150, 370 120 L 480 180 L 430 270 L 380 230 L 380 500 L 220 500 L 220 230 L 170 270 L 120 180 Z" fill="#fdfbf7" stroke="#cbd5e1" stroke-width="6"/>
      <!-- Crew neckline -->
      <path d="M 230 120 C 270 150, 330 150, 370 120 C 330 170, 270 170, 230 120 Z" fill="#e2e8f0"/>
      <line x1="220" y1="480" x2="380" y2="480" stroke="#e2e8f0" stroke-width="3"/>
    </svg>`,
  },
  {
    name: 'Vintage Hoodie',
    type: 'image/png',
    svgData: `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
      <rect width="600" height="600" fill="#f0ebe1"/>
      <!-- Hoodie silhouette -->
      <path d="M 240 100 Q 300 70 360 100 L 490 190 L 440 310 L 390 270 L 390 500 L 210 500 L 210 270 L 160 310 L 110 190 Z" fill="#52575d" stroke="#36393e" stroke-width="6"/>
      <!-- Hood curve -->
      <path d="M 240 100 Q 300 160 360 100 Q 300 70 240 100 Z" fill="#3f4348"/>
      <!-- Kangaroo pocket -->
      <path d="M 240 370 L 360 370 L 375 440 L 225 440 Z" fill="#464a50" stroke="#36393e" stroke-width="4"/>
    </svg>`,
  },
];

// Helper to determine anatomical garment zone based on normalized click coordinates
export const getGarmentZoneName = (x: number, y: number): string => {
  if (y < 0.24) {
    if (x < 0.35) return 'Collar / Left Neckline';
    if (x > 0.65) return 'Collar / Right Shoulder';
    return 'Collar / Center Neckline Wear';
  }
  if (y > 0.75) {
    if (x < 0.38) return 'Lower Hem (Left)';
    if (x > 0.62) return 'Lower Hem (Right)';
    return 'Lower Hem / Bottom Seam Split';
  }
  if (x < 0.30 && y >= 0.24 && y <= 0.75) {
    return y < 0.5 ? 'Left Shoulder / Sleeve Seam' : 'Left Sleeve / Elbow Fray';
  }
  if (x > 0.70 && y >= 0.24 && y <= 0.75) {
    return y < 0.5 ? 'Right Shoulder / Sleeve Seam' : 'Right Sleeve / Elbow Fray';
  }
  if (y >= 0.24 && y < 0.52) {
    if (x > 0.52) return 'Chest Pocket / Front Right Panel';
    if (x < 0.48) return 'Upper Chest / Front Left Panel';
    return 'Center Chest Placket / Seam';
  }
  if (x < 0.50) return 'Left Knee / Thigh Tear';
  return 'Right Knee / Thigh Tear';
};

// Preset anatomical coordinates for when user selects from dropdown
const PRESET_COORDINATES: Record<string, { x: number; y: number }> = {
  'Chest Pocket / Front Panel': { x: 0.62, y: 0.36 },
  'Knee / Lower Leg Tear': { x: 0.42, y: 0.68 },
  'Elbow / Sleeve Fray': { x: 0.76, y: 0.45 },
  'Lower Hem / Seam Split': { x: 0.50, y: 0.82 },
  'Collar / Neckline Wear': { x: 0.50, y: 0.18 },
  'Surface Pinhole / Custom Area': { x: 0.50, y: 0.45 },
};

export const UploadZone: React.FC<UploadZoneProps> = ({
  imageFile,
  imagePreviewUrl,
  onImageSelected,
  onImageRemoved,
  damageLocation,
  onDamageLocationChange,
  damageFocus,
  onDamageFocusChange,
  disabled = false,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const validateAndProcessFile = useCallback(
    (file: File) => {
      setErrorMsg(null);

      if (!ALLOWED_TYPES.includes(file.type)) {
        setErrorMsg('Invalid file format. Please upload a JPEG, PNG, or WebP garment photo.');
        return;
      }

      if (file.size > MAX_FILE_SIZE) {
        setErrorMsg(`File is too large (${formatFileSize(file.size)}). Max allowed size is 10 MB.`);
        return;
      }

      onImageSelected(file);
    },
    [onImageSelected]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProcessFile(e.target.files[0]);
    }
  };

  const loadSampleGarment = (sample: (typeof SAMPLE_GARMENTS)[0]) => {
    const blob = new Blob([sample.svgData], { type: 'image/svg+xml' });
    const img = new Image();
    const url = URL.createObjectURL(blob);
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = 600;
      canvas.height = 600;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(img, 0, 0);
        canvas.toBlob((pngBlob) => {
          if (pngBlob) {
            const pngFile = new File(
              [pngBlob],
              `${sample.name.toLowerCase().replace(/\s+/g, '-')}.png`,
              {
                type: 'image/png',
              }
            );
            onImageSelected(pngFile);
          }
          URL.revokeObjectURL(url);
        }, 'image/png');
      }
    };
    img.src = url;
  };

  // Interactive Tear Focus Placement Handler
  const handleImageClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (disabled || !imageRef.current) return;

    const rect = imageRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Check if clicked within image element bounds
    if (clickX < 0 || clickX > rect.width || clickY < 0 || clickY > rect.height) {
      return;
    }

    const normX = Math.max(0.06, Math.min(0.94, clickX / rect.width));
    const normY = Math.max(0.06, Math.min(0.94, clickY / rect.height));

    const zoneName = getGarmentZoneName(normX, normY);
    const currentRadius = damageFocus?.radius || 0.18;
    const currentSize = damageFocus?.sizeLabel || 'medium';

    if (onDamageFocusChange) {
      onDamageFocusChange({
        x: Number(normX.toFixed(3)),
        y: Number(normY.toFixed(3)),
        radius: currentRadius,
        sizeLabel: currentSize,
        locationName: zoneName,
      });
    }

    onDamageLocationChange(zoneName);
  };

  // Handle dropdown change and keep focus pin in sync
  const handleDropdownChange = (val: string) => {
    onDamageLocationChange(val);

    if (val === 'Auto-Detect') {
      if (onDamageFocusChange) onDamageFocusChange(null);
      return;
    }

    const coords = PRESET_COORDINATES[val];
    if (coords && onDamageFocusChange) {
      onDamageFocusChange({
        x: coords.x,
        y: coords.y,
        radius: damageFocus?.radius || 0.18,
        sizeLabel: damageFocus?.sizeLabel || 'medium',
        locationName: val,
      });
    }
  };

  // Handle tear size change (Small, Medium, Large)
  const handleTearSizeChange = (size: 'small' | 'medium' | 'large') => {
    if (!damageFocus || !onDamageFocusChange) return;

    const radiusMap: Record<'small' | 'medium' | 'large', number> = {
      small: 0.12,
      medium: 0.18,
      large: 0.28,
    };

    onDamageFocusChange({
      ...damageFocus,
      sizeLabel: size,
      radius: radiusMap[size],
    });
  };

  const handleClearMarker = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (onDamageFocusChange) onDamageFocusChange(null);
    onDamageLocationChange('Auto-Detect');
  };

  return (
    <div className="bg-white rounded-2xl border border-[#e8e3dc] p-5 sm:p-6 shadow-sm flex flex-col h-full">
      {/* Header Label */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base sm:text-lg font-semibold text-[#181c1a] flex items-center space-x-2">
            <span>Original Garment</span>
            <span className="text-xs font-medium text-[#6e7672] bg-stone-100 px-2 py-0.5 rounded-full">
              Source Image
            </span>
          </h2>
          <p className="text-xs text-[#6e7672] mt-0.5">
            Upload garment photo and mark the torn or damaged area for precision AI repair.
          </p>
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={handleFileInput}
        disabled={disabled}
      />

      {/* Main Upload / Preview Area */}
      {!imageFile || !imagePreviewUrl ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !disabled && fileInputRef.current?.click()}
          className={`flex-1 min-h-[320px] rounded-xl border-2 border-dashed flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-all ${
            isDragging
              ? 'border-[#1d4a38] bg-[#1d4a38]/5 scale-[0.99]'
              : 'border-[#d9d3c7] hover:border-[#1d4a38]/60 hover:bg-stone-50/70 bg-stone-50/40'
          } ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
        >
          <div className="w-14 h-14 rounded-2xl bg-[#faf8f5] border border-[#e8e3dc] flex items-center justify-center text-[#1d4a38] mb-4 shadow-sm group-hover:scale-105 transition-transform">
            <UploadCloud className="w-7 h-7" />
          </div>

          <p className="text-sm font-semibold text-[#181c1a] mb-1">
            Click to upload or drag & drop garment
          </p>
          <p className="text-xs text-[#6e7672] max-w-xs mb-4">
            Supports JPEG, PNG, or WebP (max 10 MB). For best results, use good lighting and flat-lay or hanger view.
          </p>

          <button
            type="button"
            className="px-4 py-2 rounded-lg bg-stone-100 hover:bg-stone-200 text-[#181c1a] text-xs font-medium border border-stone-300 transition-colors pointer-events-none"
          >
            Select Garment Photo
          </button>
        </div>
      ) : (
        /* Image Preview State with Interactive Tear Focus Marker */
        <div className="flex-1 flex flex-col">
          {/* Tear Focus Interactive Guidance Bar */}
          <div className="mb-2.5 flex items-center justify-between text-xs px-3 py-2 rounded-xl bg-[#1d4a38]/5 border border-[#1d4a38]/15">
            <div className="flex items-center space-x-2 truncate">
              {damageFocus ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span className="font-semibold text-[#1d4a38] truncate">
                    Tear Marked: {damageFocus.locationName}
                  </span>
                </>
              ) : (
                <>
                  <Crosshair className="w-4 h-4 text-[#1d4a38] shrink-0 animate-pulse" />
                  <span className="text-[#2d3a33]">
                    <strong>Click anywhere on your photo</strong> to focus or mark the torn area
                  </span>
                </>
              )}
            </div>

            {damageFocus && (
              <button
                type="button"
                onClick={handleClearMarker}
                className="inline-flex items-center space-x-1 text-[11px] font-medium text-[#6e7672] hover:text-rose-600 bg-white px-2 py-0.5 rounded border border-stone-200 transition-colors shrink-0 ml-2 shadow-2xs"
                title="Reset to Auto-Detect"
              >
                <X className="w-3 h-3" />
                <span>Reset</span>
              </button>
            )}
          </div>

          {/* Interactive Garment Viewport */}
          <div
            onClick={handleImageClick}
            className={`relative flex-1 min-h-[340px] max-h-[440px] bg-stone-900/5 rounded-xl border border-stone-200 flex items-center justify-center overflow-hidden select-none ${
              disabled ? 'cursor-not-allowed opacity-80' : 'cursor-crosshair'
            }`}
            title={disabled ? undefined : 'Click anywhere on the garment to mark or adjust the torn area'}
          >
            {/* The Image Wrapper (Sized to match the image dimensions exactly) */}
            <div className="relative inline-block max-h-[390px] max-w-full">
              <img
                ref={imageRef}
                src={imagePreviewUrl}
                alt="Uploaded garment preview"
                className="max-h-[380px] w-auto max-w-full object-contain block mx-auto rounded-lg shadow-2xs pointer-events-none"
              />

              {/* The Interactive Marked Tear Reticle */}
              {damageFocus && (
                <div
                  className="absolute pointer-events-none transform -translate-x-1/2 -translate-y-1/2 transition-all duration-100 ease-out z-20"
                  style={{
                    left: `${damageFocus.x * 100}%`,
                    top: `${damageFocus.y * 100}%`,
                  }}
                >
                  {/* Outer Pulsing Aura Ring */}
                  <div
                    className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-emerald-400 bg-emerald-500/15 animate-ping"
                    style={{
                      width: damageFocus.sizeLabel === 'large' ? '88px' : damageFocus.sizeLabel === 'small' ? '44px' : '64px',
                      height: damageFocus.sizeLabel === 'large' ? '88px' : damageFocus.sizeLabel === 'small' ? '44px' : '64px',
                    }}
                  />

                  {/* Target Focus Boundary Circle */}
                  <div
                    className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-dashed border-emerald-400/90 bg-emerald-500/20 backdrop-blur-[1px] shadow-lg flex items-center justify-center"
                    style={{
                      width: damageFocus.sizeLabel === 'large' ? '88px' : damageFocus.sizeLabel === 'small' ? '44px' : '64px',
                      height: damageFocus.sizeLabel === 'large' ? '88px' : damageFocus.sizeLabel === 'small' ? '44px' : '64px',
                    }}
                  >
                    {/* Crosshair Center Point */}
                    <div className="w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-white shadow-md flex items-center justify-center">
                      <div className="w-1 h-1 rounded-full bg-white" />
                    </div>
                  </div>

                  {/* Pinpoint Reticle Icon */}
                  <div className="relative -top-7 -left-3.5 filter drop-shadow">
                    <div className="inline-flex items-center space-x-1 bg-[#181c1a]/90 text-white text-[10px] font-medium px-2 py-0.5 rounded-md shadow backdrop-blur-sm whitespace-nowrap">
                      <Target className="w-3 h-3 text-emerald-400" />
                      <span>{damageFocus.locationName}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Top Badge: Garment Loaded */}
            <div className="absolute top-3 left-3 bg-black/70 backdrop-blur-sm text-white px-2.5 py-1 rounded-md text-[11px] font-medium flex items-center space-x-1.5 shadow pointer-events-none">
              <FileCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Garment Loaded</span>
            </div>

            {/* Bottom Floating Hint Overlay */}
            <div className="absolute bottom-2.5 right-2.5 bg-black/60 backdrop-blur-sm text-white px-2 py-1 rounded text-[10px] font-medium flex items-center space-x-1 shadow pointer-events-none">
              <Crosshair className="w-3 h-3 text-emerald-400" />
              <span>{damageFocus ? 'Click to move tear marker' : 'Click garment to mark tear'}</span>
            </div>
          </div>

          {/* Interactive Tear Size Controls (Visible when marker is placed) */}
          {damageFocus && (
            <div className="mt-2.5 p-2.5 bg-emerald-50/50 rounded-xl border border-emerald-200/60 flex items-center justify-between text-xs animate-in fade-in">
              <div className="flex items-center space-x-1.5 text-emerald-900 font-medium">
                <Sliders className="w-3.5 h-3.5 text-emerald-700" />
                <span className="text-[11px]">Tear / Repair Size:</span>
              </div>
              <div className="flex items-center space-x-1">
                {(['small', 'medium', 'large'] as const).map((size) => (
                  <button
                    key={size}
                    type="button"
                    onClick={() => handleTearSizeChange(size)}
                    disabled={disabled}
                    className={`px-2 py-1 rounded-lg text-[11px] font-semibold transition-all capitalize ${
                      damageFocus.sizeLabel === size
                        ? 'bg-[#1d4a38] text-white shadow-2xs'
                        : 'bg-white text-[#4a554f] border border-stone-200 hover:bg-stone-100'
                    }`}
                  >
                    {size === 'small' ? 'Pin (Small)' : size === 'medium' ? 'Standard (Med)' : 'Patch (Large)'}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Image Details Bar */}
          <div className="mt-3 p-3 bg-stone-50 rounded-xl border border-stone-200 flex items-center justify-between text-xs">
            <div className="min-w-0 pr-2">
              <p className="font-medium text-[#181c1a] truncate" title={imageFile.name}>
                {imageFile.name}
              </p>
              <p className="text-[#6e7672] text-[11px] mt-0.5">
                {formatFileSize(imageFile.size)} • {imageFile.type.replace('image/', '').toUpperCase()}
              </p>
            </div>

            {/* Actions: Replace / Remove */}
            <div className="flex items-center space-x-2 shrink-0">
              <button
                type="button"
                onClick={() => !disabled && fileInputRef.current?.click()}
                disabled={disabled}
                className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-white text-[#181c1a] border border-stone-300 hover:bg-stone-100 transition-colors disabled:opacity-50"
                title="Choose a different image"
              >
                <RefreshCw className="w-3 h-3 text-[#5e6662]" />
                <span>Replace</span>
              </button>
              <button
                type="button"
                onClick={onImageRemoved}
                disabled={disabled}
                className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100 transition-colors disabled:opacity-50"
                title="Remove this image"
              >
                <Trash2 className="w-3 h-3" />
                <span>Remove</span>
              </button>
            </div>
          </div>

          {/* Damaged Area Focus & Clarification Control */}
          <div className="mt-3 p-3 bg-stone-50/90 rounded-xl border border-stone-200 text-xs">
            <div className="flex items-center justify-between mb-1.5">
              <label htmlFor="damage-zone-select" className="font-semibold text-[#181c1a] flex items-center space-x-1.5">
                <MapPin className="w-3.5 h-3.5 text-[#1d4a38]" />
                <span>Target Damaged Area</span>
              </label>
              <span className="text-[10px] text-[#6e7672] bg-white px-2 py-0.5 rounded border border-stone-200">
                {damageFocus ? 'Custom Marked Pin' : 'Repair Focus'}
              </span>
            </div>
            <select
              id="damage-zone-select"
              value={damageLocation}
              onChange={(e) => handleDropdownChange(e.target.value)}
              disabled={disabled}
              className="w-full text-xs text-[#181c1a] bg-white border border-[#d9d3c7] rounded-lg p-2 focus:border-[#1d4a38] outline-hidden transition-colors"
            >
              <option value="Auto-Detect">⚡ Auto-Detect (AI Garment Scan)</option>
              <option value="Chest Pocket / Front Panel">Chest Pocket / Front Panel</option>
              <option value="Knee / Lower Leg Tear">Knee / Lower Leg Tear</option>
              <option value="Elbow / Sleeve Fray">Elbow / Sleeve Fray</option>
              <option value="Lower Hem / Seam Split">Lower Hem / Seam Split</option>
              <option value="Collar / Neckline Wear">Collar / Neckline Wear</option>
              <option value="Surface Pinhole / Custom Area">Surface Pinhole / Custom Area</option>
              {damageFocus &&
                !['Chest Pocket / Front Panel', 'Knee / Lower Leg Tear', 'Elbow / Sleeve Fray', 'Lower Hem / Seam Split', 'Collar / Neckline Wear', 'Surface Pinhole / Custom Area'].includes(damageLocation) && (
                  <option value={damageLocation}>🎯 Marked: {damageLocation}</option>
                )}
            </select>
            <p className="text-[10px] text-[#6e7672] mt-1">
              Click anywhere on the photo above to mark the exact tear spot, or select a preset repair area.
            </p>
          </div>
        </div>
      )}

      {/* Validation Error Banner */}
      {errorMsg && (
        <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-2.5 text-xs text-rose-800">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <p>{errorMsg}</p>
        </div>
      )}

      {/* Quick Sample Presets (Great for immediate testing without personal photo) */}
      {!imageFile && (
        <div className="mt-4 pt-4 border-t border-[#e8e3dc]">
          <p className="text-xs font-medium text-[#525a56] mb-2 flex items-center justify-between">
            <span>Or test with a sample garment:</span>
            <span className="text-[10px] text-[#78817d]">1-click test</span>
          </p>
          <div className="grid grid-cols-3 gap-2">
            {SAMPLE_GARMENTS.map((sample) => (
              <button
                key={sample.name}
                type="button"
                onClick={() => loadSampleGarment(sample)}
                disabled={disabled}
                className="px-2.5 py-2 text-center rounded-lg bg-stone-100 hover:bg-stone-200/80 border border-stone-200 text-xs font-medium text-[#2d322f] hover:text-[#181c1a] transition-all hover:border-[#1d4a38]/40 truncate"
              >
                {sample.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
