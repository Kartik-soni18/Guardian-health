import React from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  Thermometer,
  Pill,
  Stethoscope,
  Sparkles,
  ExternalLink,
  Heart,
  Brain,
  Flame,
  Droplets,
  Wind,
  CheckCircle2,
} from 'lucide-react';
import PrivacyBadge from './PrivacyBadge';
import ResearchOverview from './ResearchOverview';

export interface TriageData {
  triage_level?: 'emergency' | 'urgent' | 'moderate' | 'mild' | 'self_care';
  reasoning?: string;
  red_flags?: string[];
  remedies?: string[];
  disease?: string;
  confidence?: number;
  symptoms?: string[];
  all_predictions?: Array<{ disease: string; confidence: number }>;
  care_advice?: string;
  otc_products?: string[];
  research?: {
    summary: string;
    article_count: number;
    articles?: Array<{
      title: string;
      journal: string;
      year: number;
      pmid: string;
      abstract: string;
    }>;
  };
  pii_detected?: boolean;
}

interface TriageResultProps {
  data: TriageData;
  type?: string;
  privacy?: { pii_detected: boolean };
}

const TriageResult: React.FC<TriageResultProps> = ({ data, type: _type = 'triage', privacy }) => {
  const getTriageConfig = (level?: string) => {
    switch (level) {
      case 'emergency':
        return {
          color: 'text-rose-500',
          bg: 'bg-rose-50/80',
          border: 'border-rose-200/60',
          icon: <AlertTriangle className="w-5 h-5 text-rose-500" />,
          label: 'Emergency',
          description: 'Seek immediate medical attention',
        };
      case 'urgent':
        return {
          color: 'text-orange-500',
          bg: 'bg-orange-50/80',
          border: 'border-orange-200/60',
          icon: <Thermometer className="w-5 h-5 text-orange-500" />,
          label: 'Urgent',
          description: 'See a doctor within 24 hours',
        };
      case 'moderate':
        return {
          color: 'text-amber-500',
          bg: 'bg-amber-50/80',
          border: 'border-amber-200/60',
          icon: <Activity className="w-5 h-5 text-amber-500" />,
          label: 'Moderate',
          description: 'Schedule a medical appointment',
        };
      case 'mild':
        return {
          color: 'text-emerald-500',
          bg: 'bg-emerald-50/80',
          border: 'border-emerald-200/60',
          icon: <Heart className="w-5 h-5 text-emerald-500" />,
          label: 'Mild',
          description: 'Self-care with monitoring',
        };
      default:
        return {
          color: 'text-sky-500',
          bg: 'bg-sky-50/80',
          border: 'border-sky-200/60',
          icon: <CheckCircle2 className="w-5 h-5 text-sky-500" />,
          label: 'Self-Care',
          description: 'Home treatment recommended',
        };
    }
  };

  const getSymptomIcon = (symptom: string) => {
    const s = symptom.toLowerCase();
    if (s.includes('fever') || s.includes('temp')) return <Thermometer className="w-3 h-3" />;
    if (s.includes('pain') || s.includes('ache')) return <Activity className="w-3 h-3" />;
    if (s.includes('cough') || s.includes('breath')) return <Wind className="w-3 h-3" />;
    if (s.includes('nausea') || s.includes('vomit')) return <Droplets className="w-3 h-3" />;
    if (s.includes('head')) return <Brain className="w-3 h-3" />;
    if (s.includes('burn') || s.includes('rash')) return <Flame className="w-3 h-3" />;
    return <Stethoscope className="w-3 h-3" />;
  };

  const triageConfig = getTriageConfig(data.triage_level);

  const handleOtcClick = (product: string) => {
    window.open(`https://blinkit.com/s/?q=${encodeURIComponent(product)}`, '_blank');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="w-full space-y-3"
    >
      {/* Privacy Badge */}
      {privacy && <PrivacyBadge piiDetected={privacy.pii_detected} />}

      {/* Triage Level Card */}
      {data.triage_level && (
        <div className={`rounded-2xl ${triageConfig.bg} border ${triageConfig.border} p-4 glass-shimmer`}>
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/60 flex items-center justify-center flex-shrink-0 border border-white/60">
              {triageConfig.icon}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-sm font-semibold ${triageConfig.color}`}>
                  {triageConfig.label}
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-white/60 text-muted-foreground border border-white/50">
                  {data.triage_level.toUpperCase()}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">{triageConfig.description}</p>
            </div>
          </div>
        </div>
      )}

      {/* Disease Diagnosis Card */}
      {data.disease && (
        <div className="rounded-2xl glass-card border border-white/60 p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20">
              <Stethoscope className="w-3.5 h-3.5 text-primary" />
            </div>
            <h4 className="text-sm font-semibold">Probable Condition</h4>
          </div>

          <div className="flex items-center gap-3 mb-4">
            <span className="text-lg font-bold text-foreground">{data.disease}</span>
            {data.confidence !== undefined && (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-medium border border-primary/20">
                {(data.confidence * 100).toFixed(0)}% confidence
              </span>
            )}
          </div>

          {/* Confidence Bar */}
          {data.confidence !== undefined && (
            <div className="mb-5">
              <div className="w-full h-2.5 rounded-full bg-muted/60 overflow-hidden border border-white/40">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${data.confidence * 100}%` }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                  className={`h-full rounded-full ${
                    data.confidence > 0.8
                      ? 'bg-emerald-400'
                      : data.confidence > 0.5
                      ? 'bg-amber-400'
                      : 'bg-orange-400'
                  }`}
                />
              </div>
            </div>
          )}

          {/* Alternative Diagnoses */}
          {data.all_predictions && data.all_predictions.length > 1 && (
            <div className="mb-5">
              <p className="text-xs text-muted-foreground mb-2.5">Alternative possibilities:</p>
              <div className="space-y-2">
                {data.all_predictions.slice(1, 4).map((pred, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="flex-1 h-2 rounded-full bg-muted/50 overflow-hidden border border-white/30">
                      <div
                        className="h-full rounded-full bg-muted-foreground/30"
                        style={{ width: `${pred.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground w-24 text-right truncate">
                      {pred.disease}
                    </span>
                    <span className="text-[10px] text-muted-foreground/50 w-10 text-right">
                      {(pred.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Symptoms */}
          {data.symptoms && data.symptoms.length > 0 && (
            <div className="mb-5">
              <p className="text-xs text-muted-foreground mb-2.5">Key symptoms:</p>
              <div className="flex flex-wrap gap-1.5">
                {data.symptoms.map((symptom, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white/60 border border-white/50 text-xs text-muted-foreground"
                  >
                    {getSymptomIcon(symptom)}
                    {symptom}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Care Advice */}
          {data.care_advice && (
            <div className="p-4 rounded-xl bg-primary/5 border border-primary/15 mb-4">
              <div className="flex items-start gap-2.5">
                <Sparkles className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                <p className="text-sm text-muted-foreground leading-relaxed">{data.care_advice}</p>
              </div>
            </div>
          )}

          {/* OTC Products */}
          {data.otc_products && data.otc_products.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2.5">
                <Pill className="w-3.5 h-3.5 text-muted-foreground" />
                <p className="text-xs text-muted-foreground">Recommended OTC products:</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {data.otc_products.map((product, idx) => (
                  <motion.button
                    key={idx}
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={() => handleOtcClick(product)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/60 hover:bg-primary/10 border border-white/60 hover:border-primary/30 text-xs text-muted-foreground hover:text-primary transition-all"
                  >
                    <Pill className="w-3 h-3" />
                    <span>{product}</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </motion.button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Reasoning */}
      {data.reasoning && (
        <div className="rounded-2xl glass-card border border-white/60 p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-7 h-7 rounded-lg bg-secondary flex items-center justify-center border border-white/50">
              <Brain className="w-3.5 h-3.5 text-primary" />
            </div>
            <h4 className="text-sm font-medium">Clinical Reasoning</h4>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">{data.reasoning}</p>
        </div>
      )}

      {/* Red Flags */}
      {data.red_flags && data.red_flags.length > 0 && (
        <div className="rounded-2xl bg-rose-50/70 border border-rose-200/50 p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-7 h-7 rounded-lg bg-rose-100 flex items-center justify-center border border-rose-200/50">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
            </div>
            <h4 className="text-sm font-medium text-rose-500">Warning Signs</h4>
          </div>
          <ul className="space-y-2">
            {data.red_flags.map((flag, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-2 flex-shrink-0" />
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Remedies */}
      {data.remedies && data.remedies.length > 0 && (
        <div className="rounded-2xl bg-emerald-50/70 border border-emerald-200/50 p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-7 h-7 rounded-lg bg-emerald-100 flex items-center justify-center border border-emerald-200/50">
              <Heart className="w-3.5 h-3.5 text-emerald-500" />
            </div>
            <h4 className="text-sm font-medium text-emerald-600">Home Remedies</h4>
          </div>
          <ul className="space-y-2">
            {data.remedies.map((remedy, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-2 flex-shrink-0" />
                {remedy}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Research */}
      {data.research && (
        <ResearchOverview
          summary={data.research.summary}
          articleCount={data.research.article_count}
          articles={data.research.articles}
        />
      )}

      {/* Disclaimer Footer */}
      <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200/40">
        <p className="text-[11px] text-muted-foreground/60 leading-relaxed">
          <span className="font-medium text-amber-500/80">Disclaimer:</span> This analysis is
          AI-generated and for informational purposes only. It does not constitute medical advice,
          diagnosis, or treatment. Always consult a qualified healthcare professional for medical
          concerns. If you are experiencing a medical emergency, call your local emergency number
          immediately.
        </p>
      </div>
    </motion.div>
  );
};

export default TriageResult;
