export type StylePreset =
  | 'Streetwear'
  | 'Floral Embroidery'
  | 'Minimalist'
  | 'Vintage'
  | 'Patchwork'
  | 'Artistic'
  | 'Custom';

export type EngineMode = 'auto' | 'free' | 'demo' | 'stability';

export interface StyleOption {
  id: StylePreset;
  title: string;
  tagline: string;
  iconName: string;
  description: string;
}

export interface DamageFocusPoint {
  x: number; // 0.0 to 1.0 (relative percentage from left of image)
  y: number; // 0.0 to 1.0 (relative percentage from top of image)
  radius: number; // 0.08 to 0.25 (relative size)
  sizeLabel: 'small' | 'medium' | 'large';
  locationName: string;
}

export interface GarmentAnalysis {
  garment_type: string;
  fabric_type: string;
  color_tone: string;
  damage_location: string;
  damage_severity: string;
  confidence: 'high' | 'medium' | 'low';
  user_specified: boolean;
  clarification_needed: boolean;
  clarification_message?: string;
  recommended_technique: string;
  repair_plan?: RepairPlan;
}

export interface RepairPlan {
  technique_name: string;
  technique_rationale: string;
  difficulty: 'Beginner Friendly' | 'Intermediate' | 'Advanced';
  estimated_time: string;
  tools_and_materials: string[];
  steps: string[];
  when_to_seek_tailor: string;
}

export interface FashionIntelligenceItem {
  id: string;
  title: string;
  source: string;
  category: string;
  type: 'verified_external' | 'general_atelier' | 'ai_concept';
  url: string;
  publication_date: string;
  summary: string;
  key_technique: string;
  relevance: string;
}

export interface RedesignResult {
  id: string;
  imageData: string;
  style: StylePreset;
  provider: string;
  promptUsed: string;
  durationSeconds: number;
  downloadUrl: string;
  fallbackUsed?: boolean;
  fallbackReason?: string;
  isDemo?: boolean;
  isCached?: boolean;
  garmentAnalysis?: GarmentAnalysis;
  repairPlan?: RepairPlan;
}

export interface HealthStatus {
  status: string;
  ai_configured: boolean;
  active_provider: string;
  available_providers?: string[];
  has_stability_key?: boolean;
  has_replicate_token?: boolean;
  max_upload_size_mb: number;
  allowed_formats: string[];
  supported_styles: string[];
  fashion_intelligence_available?: boolean;
}

