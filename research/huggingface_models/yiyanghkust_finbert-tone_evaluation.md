# Model Evaluation: yiyanghkust/finbert-tone

## Basic Information
- **Model ID**: yiyanghkust/finbert-tone
- **HuggingFace URL**: https://huggingface.co/yiyanghkust/finbert-tone
- **Model Type**: Text Classification (Financial Tone/Sentiment Analysis)
- **Base Architecture**: BERT (custom FinBERT pre-trained on financial text)
- **Size**: ~110M parameters, ~440 MB
- **License**: Not explicitly stated (check before commercial deployment)

## Relevance to HERMES_Quantum
- **Primary Agent**: 22_psychology (Market Sentiment)
- **Secondary Agent**: 11_analyst (Integration and Analysis)
- **Use Case**: Analyze financial tone in analyst reports, earnings transcripts, corporate filings for quantum computing stocks
- **Relevance Score**: 4/5 (High - specialized for analyst reports and formal financial documents)
- **Priority**: HIGH

## Technical Details

### Input/Output
- **Input Format**: Raw text (analyst reports, earnings transcripts, corporate filings)
- **Output Format**: Three-class classification
  - LABEL_0: neutral
  - LABEL_1: positive
  - LABEL_2: negative
- **Max Sequence Length**: 512 tokens
- **Preprocessing Requirements**: BertTokenizer from yiyanghkust/finbert-tone

### Performance
- **Reported Accuracy**: Superior performance on financial tone analysis (specific metrics not provided in model card)
- **Training Dataset**: 10,000 manually annotated sentences from analyst reports
- **Benchmark Results**: Claims superior performance but lacks specific comparative metrics
- **Inference Speed**: ~50-100ms per sample on GPU, ~200-500ms on CPU (BERT-base architecture)
- **Resource Requirements**: 
  - GPU: Optional but recommended, ~2GB VRAM
  - CPU: Functional, moderate performance
  - Memory: ~1.5GB RAM for model loading

### Training Details
- **Pre-training Data**: Massive financial corpus (4.9B tokens):
  - Corporate Reports (10-K & 10-Q): 2.5B tokens
  - Earnings Call Transcripts: 1.3B tokens
  - Analyst Reports: 1.1B tokens
- **Fine-tuning Data**: 10,000 manually annotated sentences from analyst reports
- **Domain**: Highly specialized for formal financial communications
- **Academic Backing**: Huang, Allen H., Hui Wang, and Yi Yang. "FinBERT: A Large Language Model for Extracting Information from Financial Text." Contemporary Accounting Research (2022)
- **GitHub**: https://github.com/yya518/FinBERT

## Integration Notes

### Pros
- Extensive pre-training on financial text (4.9B tokens) - most comprehensive financial corpus
- Trained on all three key financial document types: 10-Ks, earnings calls, analyst reports
- Specifically fine-tuned on analyst reports - ideal for professional financial analysis
- 49.4M downloads (1.1M monthly) - highly popular
- 214 likes, 100+ Spaces - strong community validation
- Academic publication in top accounting research journal
- More domain-specific than general FinBERT models

### Cons
- Last updated October 2022 - older than ProsusAI/finbert
- Label mapping is reversed from ProsusAI/finbert (LABEL_0=neutral vs positive)
- Lacks detailed performance metrics in model card
- May be over-specialized for formal documents vs news articles
- Training focused on analyst reports - may not generalize as well to news
- License not explicitly stated

### Dependencies
```
transformers>=4.30.0
torch>=2.0.0
```

### Deployment Considerations
- **Model Serving**: Local inference recommended; requires careful label mapping
- **Latency Requirements**: Same as BERT-base (50-100ms GPU)
- **Scaling**: Batch processing capable
- **Caching Strategy**: Cache by document hash, especially for repeated analyst reports
- **Label Mapping**: CRITICAL - Different from ProsusAI/finbert (0=neutral, 1=positive, 2=negative)

## Code Example

```python
# Usage for HERMES_Quantum 22_psychology agent
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import pipeline

# Load model and tokenizer
model = BertForSequenceClassification.from_pretrained('yiyanghkust/finbert-tone', num_labels=3)
tokenizer = BertTokenizer.from_pretrained('yiyanghkust/finbert-tone')

# Create pipeline
nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# Example: Analyze quantum computing analyst reports
sentences = [
    "D-Wave demonstrates strong execution with record bookings growth",
    "IonQ faces significant technical challenges and funding constraints",
    "Rigetti maintains operations with adequate cash reserves",
    "QUBT shows promising technology but uncertain commercialization path"
]

results = nlp(sentences)

# IMPORTANT: Label mapping for this model
# LABEL_0: neutral
# LABEL_1: positive  
# LABEL_2: negative

for sentence, result in zip(sentences, results):
    label_map = {'LABEL_0': 'neutral', 'LABEL_1': 'positive', 'LABEL_2': 'negative'}
    sentiment = label_map[result['label']]
    print(f"Text: {sentence}")
    print(f"Sentiment: {sentiment} (confidence: {result['score']:.2%})")
    print()
```

## Testing Results

### Test Dataset
- **Source**: Synthetic analyst-style statements for quantum computing stocks
- **Size**: 4 sample sentences (to be expanded)
- **Domain**: Analyst-report style commentary on QBTS, IONQ, RGTI, QUBT

### Performance Metrics
| Metric | Value | Notes |
|--------|-------|-------|
| Accuracy | Not specified | Claims "superior" but no specific number |
| Training Samples | 10,000 | Manually annotated analyst sentences |
| Inference Time | ~50-100ms | Per sample, GPU (BERT-base) |
| Corpus Size | 4.9B tokens | Pre-training corpus |

### Example Outputs
```
Input: "D-Wave demonstrates strong execution with record bookings growth"
Expected: LABEL_1 (positive)
Confidence: High (analyst-style positive language)

Input: "IonQ faces significant technical challenges and funding constraints"
Expected: LABEL_2 (negative)
Confidence: High (clear negative signals)

Input: "Rigetti maintains operations with adequate cash reserves"
Expected: LABEL_0 (neutral)
Confidence: Medium (neutral maintenance language)
```

### Edge Cases Observed
- Specialized for analyst report tone - may differ from news sentiment
- Formal financial language is strength, but casual news may be weakness

## Comparison with Alternatives

| Model | Pre-training | Fine-tuning | Downloads | Domain Focus | Label Map |
|-------|--------------|-------------|-----------|--------------|-----------|
| **yiyanghkust/finbert-tone** | 4.9B tokens financial | 10K analyst sentences | 49.4M | Analyst reports | 0=N, 1=P, 2=Neg |
| ProsusAI/finbert | Reuters TRC2 | Financial PhraseBank | 69.6M | Financial news | 0=P, 1=Neg, 2=N |
| mrm8488/distilroberta | N/A | Financial PhraseBank | 144M | News sentiment | Varies |

### Key Differences: yiyanghkust vs ProsusAI
1. **Training Corpus**: yiyanghkust has 4.9B tokens vs Reuters TRC2
2. **Document Focus**: yiyanghkust targets analyst reports; ProsusAI targets news
3. **Label Mapping**: Different label encodings (requires careful handling)
4. **Updates**: ProsusAI more recently updated (May 2023 vs Oct 2022)
5. **Popularity**: ProsusAI more downloads (69.6M vs 49.4M)

## Integration Prototype

### Implementation Status
- [x] Basic documentation complete
- [x] Code example provided with label mapping
- [ ] Performance benchmarked on target hardware
- [ ] Integrated with sample 22_psychology agent code
- [ ] Comparison testing with ProsusAI/finbert
- [ ] Error handling implemented

### Code Location
- Notebook: `../notebooks/finbert_comparison.ipynb` (to be created)
- Prototype: `../experiments/sentiment_pipeline/` (to be created)

### Integration Effort Estimate
- **Development Time**: 4-8 hours (similar to ProsusAI/finbert)
- **Testing Time**: 6-10 hours (need comparison testing)
- **Documentation**: 2-4 hours

## Evaluation Status
- [x] Basic documentation complete
- [x] Code example tested conceptually
- [ ] Performance benchmarked locally
- [ ] Direct comparison with ProsusAI/finbert
- [x] Comparison with alternatives done
- [x] Decision made

## Decision
**Status**: DEFER

**Rationale**: 
While yiyanghkust/finbert-tone has impressive pre-training (4.9B tokens) and is specifically optimized for analyst reports, ProsusAI/finbert is the better primary choice for HERMES_Quantum for several reasons:

1. **More Popular**: 69.6M vs 49.4M downloads suggests broader validation
2. **Better Documentation**: ProsusAI has clearer metrics and academic backing
3. **News-Focused**: ProsusAI trained on financial news, which is our primary data source
4. **Standard Labels**: ProsusAI uses more intuitive label mapping
5. **More Recent**: Updated May 2023 vs October 2022

However, yiyanghkust/finbert-tone has significant value for specific use cases.

**If DEFER**:
- **Reason for deferral**: ProsusAI/finbert better matches primary use case (news analysis)
- **Conditions for reconsideration**: 
  - If we add analyst report analysis in Phase 2+
  - If we need more formal financial document analysis
  - If comparative testing shows significantly better performance
- **Alternative approach**: 
  - Use ProsusAI/finbert for news and press releases
  - Consider yiyanghkust for earnings transcripts and analyst reports in future phases
  - Potential ensemble: Different models for different document types

**Future Consideration**:
- Phase 2+: Create document-type router that selects appropriate model
- Analyst reports → yiyanghkust/finbert-tone
- News articles → ProsusAI/finbert
- Social media → FinTwitBERT-sentiment

## Related Resources
- Model Card: https://huggingface.co/yiyanghkust/finbert-tone
- GitHub: https://github.com/yya518/FinBERT
- Paper: Huang, Allen H., Hui Wang, and Yi Yang. "FinBERT: A Large Language Model for Extracting Information from Financial Text." Contemporary Accounting Research (2022)
- Related Models: 
  - ProsusAI/finbert (news-focused alternative)
  - StephanAkkerman/FinTwitBERT-sentiment (social media)
- 18 fine-tuned models based on this model
- 100+ Spaces using this model

## Notes
- The 4.9B token pre-training corpus is notably larger than most alternatives
- Training on earnings transcripts could be valuable for parsing QBTS/IONQ earnings calls
- Consider for Phase 2 when adding earnings call analysis
- Label mapping difference could cause integration errors if not handled carefully
- Academic publication in Contemporary Accounting Research adds credibility
- yiyanghkust appears to be from Hong Kong University of Science and Technology

---

**Evaluated By**: HERMES_Quantum Research Process
**Date**: 2025-12-28
**Last Updated**: 2025-12-28
