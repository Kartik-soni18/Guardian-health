import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, ChevronDown, ExternalLink, FileText } from 'lucide-react';

interface Article {
  title: string;
  journal: string;
  year: number;
  pmid: string;
  abstract: string;
}

interface ResearchOverviewProps {
  summary: string;
  articleCount: number;
  articles?: Article[];
}

const ResearchOverview: React.FC<ResearchOverviewProps> = ({
  summary,
  articleCount,
  articles = [],
}) => {
  const [expanded, setExpanded] = useState(false);
  const [openArticle, setOpenArticle] = useState<string | null>(null);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full rounded-2xl glass-card border border-white/60 overflow-hidden"
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-white/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20">
            <BookOpen className="w-4 h-4 text-primary" />
          </div>
          <div className="text-left">
            <h4 className="text-sm font-medium">Research Overview</h4>
            <p className="text-xs text-muted-foreground">
              {articleCount} PubMed articles analyzed
            </p>
          </div>
        </div>
        <motion.div
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        </motion.div>
      </button>

      {/* Expanded Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3">
              {/* Summary */}
              <div className="p-4 rounded-xl bg-white/40 border border-white/50">
                <p className="text-sm text-muted-foreground leading-relaxed">{summary}</p>
              </div>

              {/* Articles */}
              {articles.length > 0 && (
                <div className="space-y-2">
                  {articles.map((article) => (
                    <div
                      key={article.pmid}
                      className="rounded-xl bg-white/30 border border-white/40 overflow-hidden"
                    >
                      <button
                        onClick={() =>
                          setOpenArticle(openArticle === article.pmid ? null : article.pmid)
                        }
                        className="w-full flex items-center justify-between p-3 hover:bg-white/40 transition-colors"
                      >
                        <div className="flex items-center gap-2 text-left">
                          <FileText className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                          <span className="text-sm font-medium truncate">{article.title}</span>
                        </div>
                        <motion.div
                          animate={{ rotate: openArticle === article.pmid ? 180 : 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <ChevronDown className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                        </motion.div>
                      </button>

                      <AnimatePresence>
                        {openArticle === article.pmid && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                          >
                            <div className="px-3 pb-3 space-y-2">
                              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                <span className="font-medium">{article.journal}</span>
                                <span>{article.year}</span>
                                <a
                                  href={`https://pubmed.ncbi.nlm.nih.gov/${article.pmid}/`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-primary hover:text-primary/80 transition-colors"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <span>PMID: {article.pmid}</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              </div>
                              <p className="text-xs text-muted-foreground/80 leading-relaxed">
                                {article.abstract}
                              </p>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              )}

              {/* Disclaimer */}
              <div className="p-2.5 rounded-lg bg-amber-50/50 border border-amber-200/40">
                <p className="text-[10px] text-muted-foreground/60 leading-relaxed">
                  This research summary is AI-generated for informational purposes only.
                  Always consult with a healthcare professional for medical advice.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default ResearchOverview;
