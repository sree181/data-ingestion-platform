"""
PubMed Data Collection Script
Collects diverse medical literature from PubMed and auto-labels for classification training
"""

import asyncio
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import re
from typing import List, Dict, Tuple
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from existing literature service
from services.literature_automation.services.literature_search_service import LiteratureSearchService
from services.literature_automation.models.literature_models import LiteratureSource

class AutoLabeler:
    """
    Intelligent auto-labeling using keyword patterns and heuristics
    Based on ICSR identification rules from pharmacovigilance guidelines
    """
    
    def __init__(self):
        # ICSR indicators - Individual case safety reports
        self.icsr_strong_indicators = [
            r'\bcase\s+report\b',
            r'\bcase\s+series\b',
            r'\badverse\s+event\s+report\b',
            r'\bpatient\s+(experienced|developed|presented\s+with)',
            r'\b\d+[-\s]year[-\s]old\s+(male|female|patient)',
            r'\banaphylaxis\b.*\b(following|after)\b',
            r'\bdeath\b.*\b(following|after|due\s+to)\b.*\b(drug|vaccine|medication)\b',
            r'\bhospitalization\b.*\b(due\s+to|following|after)\b',
            r'\bsevere\s+adverse\s+(reaction|event)\b',
            r'\bdrug[-\s]induced\b',
            r'\bmedication[-\s]induced\b',
            r'\bvaccine[-\s]associated\b',
        ]
        
        self.icsr_moderate_indicators = [
            r'\badverse\s+(reaction|event|effect)\b',
            r'\bside\s+effect\b',
            r'\btoxicity\b',
            r'\bhypersensitivity\b',
            r'\ballergic\s+reaction\b',
            r'\boverdose\b',
            r'\bwithdrawal\s+syndrome\b',
        ]
        
        # Safety Information indicators - Studies, trials, surveillance
        self.safety_strong_indicators = [
            r'\bclinical\s+trial\b',
            r'\bphase\s+(I{1,3}|IV|1|2|3|4)\s+(trial|study)\b',
            r'\brandomized\s+controlled\s+trial\b',
            r'\bpost[-\s]marketing\s+(surveillance|study)\b',
            r'\bpharmacovigilance\s+study\b',
            r'\bobservational\s+study\b.*\badverse\b',
            r'\bcohort\s+study\b.*\b(safety|adverse)\b',
            r'\bprospective\s+study\b.*\bsafety\b',
        ]
        
        self.safety_moderate_indicators = [
            r'\bsafety\s+(profile|analysis|assessment|data)\b',
            r'\btolerability\b',
            r'\breal[-\s]world\s+(evidence|data)\b',
            r'\bregistry\s+study\b',
            r'\bmulticenter\s+study\b',
        ]
        
        # Rejected indicators - Reviews, meta-analyses, non-clinical
        self.rejected_strong_indicators = [
            r'\bsystematic\s+review\b',
            r'\bmeta[-\s]analysis\b',
            r'\bliterature\s+review\b',
            r'\beditorial\b',
            r'\bcommentary\b',
            r'\bopinion\b',
            r'\bguideline\b',
            r'\brecommendation\b',
            r'\bconsensus\s+statement\b',
        ]
        
        self.rejected_moderate_indicators = [
            r'\bin\s+vitro\b',
            r'\banimal\s+(study|model|experiment)\b',
            r'\bpreclinical\b',
            r'\bmolecular\s+mechanism\b',
            r'\bpathophysiology\b',
            r'\bpharmacokinetic\b',
            r'\bpharmacodynamic\b',
            r'\bprotocol\b.*\bstudy\b',
        ]
        
        # Non-ICSR indicators - General medical literature
        self.non_icsr_indicators = [
            r'\bdiagnosis\b',
            r'\btreatment\s+(approach|strategy|guideline)\b',
            r'\bepidemiolog(y|ical)\b',
            r'\bprevalence\b',
            r'\bincidence\b',
            r'\brisk\s+factor\b',
            r'\bpathogenesis\b',
        ]
    
    def score_patterns(self, text: str, patterns: List[str]) -> int:
        """Count how many patterns match in the text"""
        text_lower = text.lower()
        score = 0
        for pattern in patterns:
            if re.search(pattern, text_lower):
                score += 1
        return score
    
    def auto_label(self, title: str, abstract: str) -> Tuple[str, str, float, Dict]:
        """
        Auto-label article based on content analysis
        Returns: (label, confidence_level, confidence_score, reasoning)
        """
        # Combine title and abstract for analysis
        text = f"{title} {abstract}"
        
        # Score each category
        icsr_strong = self.score_patterns(text, self.icsr_strong_indicators)
        icsr_moderate = self.score_patterns(text, self.icsr_moderate_indicators)
        icsr_total = icsr_strong * 3 + icsr_moderate
        
        safety_strong = self.score_patterns(text, self.safety_strong_indicators)
        safety_moderate = self.score_patterns(text, self.safety_moderate_indicators)
        safety_total = safety_strong * 3 + safety_moderate
        
        rejected_strong = self.score_patterns(text, self.rejected_strong_indicators)
        rejected_moderate = self.score_patterns(text, self.rejected_moderate_indicators)
        rejected_total = rejected_strong * 3 + rejected_moderate
        
        non_icsr_score = self.score_patterns(text, self.non_icsr_indicators)
        
        # Decision logic
        scores = {
            'ICSR': icsr_total,
            'Safety_Information': safety_total,
            'Rejected': rejected_total,
            'Non-ICSR': non_icsr_score
        }
        
        # Determine label based on scores
        if rejected_strong >= 1:
            label = 'Rejected'
            confidence = 'high' if rejected_strong >= 2 else 'medium'
            confidence_score = 0.9 if rejected_strong >= 2 else 0.7
            
        elif icsr_strong >= 2:
            label = 'ICSR'
            confidence = 'high'
            confidence_score = 0.9
            
        elif icsr_strong == 1 or icsr_total >= 4:
            label = 'ICSR'
            confidence = 'medium'
            confidence_score = 0.7
            
        elif safety_strong >= 1:
            label = 'Safety_Information'
            confidence = 'high' if safety_strong >= 2 else 'medium'
            confidence_score = 0.85 if safety_strong >= 2 else 0.7
            
        elif safety_moderate >= 2:
            label = 'Safety_Information'
            confidence = 'medium'
            confidence_score = 0.65
            
        elif non_icsr_score >= 2:
            label = 'Non-ICSR'
            confidence = 'medium'
            confidence_score = 0.65
            
        else:
            # Default to Non-ICSR if unclear
            label = 'Non-ICSR'
            confidence = 'low'
            confidence_score = 0.5
        
        reasoning = {
            'scores': scores,
            'matched_patterns': self._get_matched_patterns(text)
        }
        
        return label, confidence, confidence_score, reasoning
    
    def _get_matched_patterns(self, text: str) -> Dict[str, List[str]]:
        """Get which patterns matched (for debugging)"""
        matched = {}
        text_lower = text.lower()
        
        for category, patterns in [
            ('ICSR_strong', self.icsr_strong_indicators),
            ('ICSR_moderate', self.icsr_moderate_indicators),
            ('Safety_strong', self.safety_strong_indicators),
            ('Rejected_strong', self.rejected_strong_indicators)
        ]:
            matched[category] = [
                pattern for pattern in patterns 
                if re.search(pattern, text_lower)
            ][:3]  # Limit to first 3 matches
        
        return matched


class PubMedDataCollector:
    """
    Collects diverse medical literature from PubMed
    """
    
    def __init__(self):
        self.search_service = LiteratureSearchService()
        self.auto_labeler = AutoLabeler()
        
        # Search queries for each category
        self.queries = {
            'ICSR': [
                # Individual case reports
                'adverse drug reaction case report',
                'adverse event following immunization case',
                'drug induced liver injury case report',
                'anaphylaxis drug case report',
                'Stevens-Johnson syndrome drug case',
                'drug hypersensitivity case report',
                'medication error adverse event',
                'vaccine adverse event case report',
                'drug overdose case report',
                'fatal adverse drug reaction case',
            ],
            'Safety_Information': [
                # Clinical trials and safety studies
                'clinical trial drug safety',
                'phase III adverse events',
                'post-marketing safety study',
                'pharmacovigilance study',
                'drug safety surveillance',
                'observational study drug safety',
                'cohort study adverse events',
                'registry study drug safety',
            ],
            'Non-ICSR': [
                # General medical literature
                'diabetes mellitus treatment',
                'hypertension management',
                'cancer pathophysiology',
                'cardiovascular disease prevention',
                'infectious disease epidemiology',
                'antibiotic resistance mechanisms',
                'psychiatric disorder diagnosis',
                'chronic kidney disease treatment',
            ],
            'Rejected': [
                # Reviews, meta-analyses, etc.
                'systematic review drug therapy',
                'meta-analysis adverse events',
                'literature review pharmacology',
                'animal study drug toxicity',
                'in vitro drug effects',
                'editorial drug safety',
                'drug development protocol',
                'preclinical drug study',
            ]
        }
    
    async def collect_articles(
        self, 
        articles_per_query: int = 50,
        max_total: int = 2000
    ) -> pd.DataFrame:
        """
        Collect articles from PubMed across all categories
        """
        all_articles = []
        article_ids_seen = set()
        
        print("="*80)
        print("PUBMED DATA COLLECTION STARTING")
        print("="*80)
        print(f"Target: {max_total} articles")
        print(f"Articles per query: {articles_per_query}")
        print()
        
        for category, queries in self.queries.items():
            print(f"\n{'='*60}")
            print(f"Collecting {category} articles...")
            print(f"{'='*60}")
            
            category_count = 0
            
            for query in queries:
                print(f"\nQuery: '{query}'")
                
                try:
                    # Search PubMed
                    results = await self.search_service.search_literature(
                        query=query,
                        sources=[LiteratureSource.PUBMED],
                        max_results=articles_per_query,
                        date_range={
                            'from_date': (datetime.now() - timedelta(days=3650)).strftime('%Y/%m/%d'),
                            'to_date': datetime.now().strftime('%Y/%m/%d')
                        }
                    )
                    
                    print(f"  Retrieved: {len(results)} articles")
                    
                    # Process results
                    for article in results:
                        # Skip duplicates
                        if article.id in article_ids_seen:
                            continue
                        
                        article_ids_seen.add(article.id)
                        
                        # Auto-label
                        label, confidence, conf_score, reasoning = self.auto_labeler.auto_label(
                            article.title,
                            article.abstract
                        )
                        
                        all_articles.append({
                            'article_id': article.id,
                            'pmid': article.pmid,
                            'title': article.title,
                            'abstract': article.abstract,
                            'authors': ', '.join(article.authors[:5]),  # First 5 authors
                            'journal': article.journal,
                            'publication_date': article.publication_date,
                            'doi': article.doi,
                            'url': article.url,
                            'keywords': ', '.join(article.keywords[:10]) if article.keywords else '',
                            'mesh_terms': ', '.join(article.mesh_terms[:10]) if article.mesh_terms else '',
                            'source': 'pubmed',
                            'search_query': query,
                            'expected_label': category,
                            'auto_label': label,
                            'confidence_level': confidence,
                            'confidence_score': conf_score,
                            'label_scores': json.dumps(reasoning['scores']),
                            'collected_at': datetime.now().isoformat()
                        })
                        
                        category_count += 1
                    
                    print(f"  Category total: {category_count}")
                    
                    # Stop if we have enough
                    if len(all_articles) >= max_total:
                        print(f"\n✅ Reached target of {max_total} articles!")
                        break
                        
                except Exception as e:
                    print(f"  ⚠️ Error with query '{query}': {str(e)}")
                    continue
                
                # Small delay to respect rate limits
                await asyncio.sleep(1)
            
            if len(all_articles) >= max_total:
                break
        
        # Convert to DataFrame
        df = pd.DataFrame(all_articles)
        
        print("\n" + "="*80)
        print("COLLECTION COMPLETE")
        print("="*80)
        print(f"Total articles collected: {len(df)}")
        print(f"Unique articles: {df['article_id'].nunique()}")
        print()
        print("Distribution by auto-label:")
        print(df['auto_label'].value_counts())
        print()
        print("Distribution by confidence level:")
        print(df['confidence_level'].value_counts())
        print()
        
        return df


async def main():
    """Main execution function"""
    
    # Create output directory
    output_dir = Path('ml_training/data')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize collector
    collector = PubMedDataCollector()
    
    # Collect articles
    print("Starting PubMed data collection...")
    print("This may take 2-4 hours depending on network speed")
    print()
    
    df = await collector.collect_articles(
        articles_per_query=50,  # 50 articles per query
        max_total=2000  # Total target: 2000 articles
    )
    
    # Save raw dataset
    raw_file = output_dir / 'pubmed_raw_dataset.csv'
    df.to_csv(raw_file, index=False)
    print(f"\n✅ Raw dataset saved to: {raw_file}")
    
    # Analyze label agreement
    print("\n" + "="*80)
    print("LABEL AGREEMENT ANALYSIS")
    print("="*80)
    
    agreement = (df['expected_label'] == df['auto_label']).sum()
    total = len(df)
    agreement_rate = agreement / total * 100
    
    print(f"Expected vs Auto-label agreement: {agreement}/{total} ({agreement_rate:.1f}%)")
    print()
    
    # Show confusion matrix
    confusion = pd.crosstab(
        df['expected_label'], 
        df['auto_label'],
        rownames=['Expected'],
        colnames=['Auto-label']
    )
    print("Confusion Matrix:")
    print(confusion)
    print()
    
    # Filter high confidence articles for training
    high_conf = df[df['confidence_level'].isin(['high', 'medium'])]
    print(f"High/Medium confidence articles: {len(high_conf)} ({len(high_conf)/len(df)*100:.1f}%)")
    
    # Use auto_label as final label for high confidence
    high_conf_file = output_dir / 'pubmed_labeled_dataset.csv'
    high_conf_labeled = high_conf.copy()
    high_conf_labeled['label'] = high_conf_labeled['auto_label']
    high_conf_labeled.to_csv(high_conf_file, index=False)
    print(f"✅ Labeled dataset saved to: {high_conf_file}")
    
    # Save statistics
    stats = {
        'collection_date': datetime.now().isoformat(),
        'total_articles': len(df),
        'unique_articles': df['article_id'].nunique(),
        'high_confidence': len(high_conf),
        'label_distribution': df['auto_label'].value_counts().to_dict(),
        'confidence_distribution': df['confidence_level'].value_counts().to_dict(),
        'agreement_rate': float(agreement_rate),
        'queries_used': collector.queries
    }
    
    stats_file = output_dir / 'collection_statistics.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Statistics saved to: {stats_file}")
    
    print("\n" + "="*80)
    print("✅ DATA COLLECTION COMPLETE!")
    print("="*80)
    print(f"\nNext steps:")
    print(f"1. Review the dataset: {high_conf_file}")
    print(f"2. Run data preparation: python ml_training/02_prepare_training_data.py")
    print(f"3. Train model: python ml_training/03_train_model.py")


if __name__ == "__main__":
    asyncio.run(main())

