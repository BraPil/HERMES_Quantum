# Model Evaluation: ProsusAI/finbert

## Basic Information
- **Model ID**: ProsusAI/finbert
- **HuggingFace URL**: https://huggingface.co/ProsusAI/finbert
- **Model Type**: Text Classification (Sentiment Analysis)
- **Base Architecture**: BERT (bert-base-uncased)
- **Size**: ~110M parameters, ~440 MB
- **License**: Not explicitly stated (check before commercial deployment)

## Relevance to HERMES_Quantum
- **Primary Agent**: 22_psychology (Market Sentiment)
- **Secondary Agent**: 11_analyst (Integration and Analysis)
- **Use Case**: Analyze sentiment of financial news, earnings reports, analyst reports, and press releases related to quantum computing stocks (QBTS, IONQ, RGTI, QUBT)
- **Relevance Score**: 5/5 (Critical - core capability for sentiment analysis)
- **Priority**: HIGH

## Technical Details

### Input/Output
- **Input Format**: Raw text (financial news, reports, statements)
- **Output Format**: Three-class classification: positive, negative, neutral
- **Max Sequence Length**: 512 tokens
- **Preprocessing Requirements**: Standard BERT tokenization via AutoTokenizer

### Performance
- **Reported Accuracy**: ~86% on Financial PhraseBank dataset (sentences with >66% annotator agreement)
- **Benchmark Results**: 
  - Outperforms general-purpose BERT on financial text
  - Trained specifically on financial corpus for domain adaptation
- **Inference Speed**: ~50-100ms per sample on GPU, ~200-500ms on CPU
- **Resource Requirements**: 
  - GPU: Optional but recommended, ~2GB VRAM
  - CPU: Functional, moderate performance
  - Memory: ~1.5GB RAM for model loading

### Training Details
- **Training Data**: 
  1. Pre-trained BERT further trained on financial corpus (Reuters TRC2 dataset, ~46,143 articles)
  2. Fine-tuned on Financial PhraseBank (Malo et al., 2014)
- **Domain**: Financial news and statements
- **Fine-tuning**: Domain-adapted BERT + task-specific fine-tuning
- **Paper**: arXiv:1908.10063 - "FinBERT: Financial Sentiment Analysis with Pre-trained Language Models"

## Integration Notes

### Pros
- Industry standard for financial sentiment analysis (2.7M+ monthly downloads)
- 1,047 likes, 100+ Spaces using it - strong community validation
- Pre-trained on financial domain - understands financial terminology
- Three-class output (positive/negative/neutral) matches typical sentiment needs
- Supports PyTorch, TensorFlow, and JAX - flexible deployment
- Well-documented with academic paper backing
- Active inference API available on HuggingFace

### Cons
- Trained on formal financial news - may need adaptation for social media text
- Last updated May 2023 - not the newest model
- 512 token limit may truncate longer documents
- License not explicitly stated - needs verification for commercial use
- BERT architecture is heavier than newer distilled alternatives

### Dependencies
```
transformers>=4.30.0
torch>=2.0.0
# OR tensorflow>=2.0.0
# OR jax
```

### Deployment Considerations
- **Model Serving**: Local inference recommended for production; API available for testing
- **Latency Requirements**: Real-time analysis feasible with GPU
- **Scaling**: Can batch process multiple texts; consider model serving framework (TorchServe, Triton) for high volume
- **Caching Strategy**: Cache results for repeated news articles; sentiment unlikely to change for same text

## Code Example

```python
# Basic usage example for HERMES_Quantum 22_psychology agent
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Load model and tokenizer
model_name = "ProsusAI/finbert"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Example: Analyze quantum computing stock news
texts = [
    "D-Wave Quantum Inc. reported strong revenue growth in Q3 2025, with bookings up 300% year-over-year.",
    "IonQ stock plummets after disappointing earnings miss expectations.",
    "Rigetti Computing maintains steady operations amid quantum computing sector volatility."
]

def analyze_sentiment(text):
    """Analyze financial sentiment of text."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    
    with torch.no_grad():
        outputs = model(**inputs)
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
    
    # Labels: 0=positive, 1=negative, 2=neutral (verify with model config)
    labels = ["positive", "negative", "neutral"]
    predicted_class = torch.argmax(probabilities, dim=-1).item()
    confidence = probabilities[0][predicted_class].item()
    
    return {
        "sentiment": labels[predicted_class],
        "confidence": confidence,
        "probabilities": {
            "positive": probabilities[0][0].item(),
            "negative": probabilities[0][1].item(),
            "neutral": probabilities[0][2].item()
        }
    }

# Analyze each text
for text in texts:
    result = analyze_sentiment(text)
    print(f"Text: {text[:60]}...")
    print(f"Sentiment: {result['sentiment']} (confidence: {result['confidence']:.2%})")
    print()
```

## Testing Results

### Test Dataset
- **Source**: Synthetic examples relevant to quantum computing stocks
- **Size**: 3 sample texts (to be expanded in notebooks/)
- **Domain**: Financial news about QBTS, IONQ, RGTI, QUBT

### Performance Metrics
| Metric | Value | Notes |
|--------|-------|-------|
| Accuracy | ~86% | Reported on Financial PhraseBank |
| Precision | ~85% | Estimated from paper |
| Recall | ~86% | Estimated from paper |
| F1 Score | ~85% | Estimated from paper |
| Inference Time | ~50-100ms | Per sample, GPU |

### Example Outputs
```
Input: "D-Wave Quantum Inc. reported strong revenue growth in Q3 2025, with bookings up 300% year-over-year."
Output: positive
Confidence: ~0.85-0.95 (expected based on strong positive language)

Input: "IonQ stock plummets after disappointing earnings miss expectations."
Output: negative
Confidence: ~0.85-0.95 (expected based on clear negative language)

Input: "Rigetti Computing maintains steady operations amid quantum computing sector volatility."
Output: neutral
Confidence: ~0.60-0.80 (expected - mixed signals in text)
```

### Edge Cases Observed
- Mixed sentiment sentences may produce lower confidence scores
- Very short texts may have reduced accuracy
- Technical jargon specific to quantum computing may need monitoring

## Comparison with Alternatives

| Model | Downloads | Speed | Size | Domain Focus | Notes |
|-------|-----------|-------|------|--------------|-------|
| **ProsusAI/finbert** | 69.6M | Medium | 110M | Financial News | Industry standard, well-documented |
| yiyanghkust/finbert-tone | 49.4M | Medium | ~110M | Financial Tone | Alternative FinBERT, tone-focused |
| mrm8488/distilroberta-financial | 144M | Fast | 82M | Financial News | Smaller, faster, very popular |
| StephanAkkerman/FinTwitBERT-sentiment | 497K | Medium | 110M | Twitter/Social | Better for social media |

### Recommendation for HERMES_Quantum
- **22_psychology (Market Sentiment)**: Use ProsusAI/finbert for formal financial news and reports
- **23_social (Social Media)**: Use FinTwitBERT-sentiment for Twitter/social media analysis
- **Consider**: mrm8488/distilroberta-financial as faster alternative if latency is critical

## Integration Prototype

### Implementation Status
- [x] Basic documentation complete
- [ ] Code example tested locally
- [ ] Performance benchmarked on target hardware
- [ ] Integrated with sample 22_psychology agent code
- [ ] Error handling implemented
- [ ] Caching/optimization tested

### Code Location
- Notebook: `../notebooks/finbert_evaluation.ipynb` (to be created)
- Prototype: `../experiments/sentiment_pipeline/` (to be created)

### Integration Effort Estimate
- **Development Time**: 4-8 hours for basic integration
- **Testing Time**: 4-8 hours for thorough testing
- **Documentation**: 2-4 hours

## Evaluation Status
- [x] Basic documentation complete
- [x] Code example provided
- [ ] Performance benchmarked locally
- [ ] Integration prototype created
- [x] Comparison with alternatives done
- [x] Decision made

## Decision
**Status**: ADOPT

**Rationale**: 
ProsusAI/finbert is the industry standard for financial sentiment analysis with 69.6M downloads and strong community validation. It is specifically trained on financial text, making it ideal for analyzing news, earnings reports, and analyst statements about quantum computing stocks. The model's three-class output (positive/negative/neutral) directly maps to the sentiment scoring needs of the 22_psychology agent.

**If ADOPT**:
- **Target agent**: 22_psychology (primary), 11_analyst (secondary consumer)
- **Integration timeline**: Phase 1 (Data Ingestion & Analysis)
- **Dependencies**: 
  - transformers library (already in optional dependencies)
  - torch (PyTorch framework)
  - Data ingestion pipeline for financial news
- **Success criteria**: 
  - Successfully analyze sentiment of quantum computing stock news
  - Achieve >80% agreement with human-labeled test samples
  - Process news in <500ms per article

**Complementary Models**:
- Use StephanAkkerman/FinTwitBERT-sentiment for 23_social agent (Twitter/social media)
- Consider mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis as backup for faster inference

## Related Resources
- Model Card: https://huggingface.co/ProsusAI/finbert
- Paper: https://arxiv.org/abs/1908.10063
- Blog Post: https://medium.com/prosus-ai-tech-blog/finbert-financial-sentiment-analysis-with-bert-b277a3607101
- Training Data: https://www.researchgate.net/publication/251231107_Good_Debt_or_Bad_Debt_Detecting_Semantic_Orientations_in_Economic_Texts
- Related Models: 
  - yiyanghkust/finbert-tone (alternative FinBERT)
  - StephanAkkerman/FinTwitBERT-sentiment (Twitter-focused)
  - mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis (faster alternative)

## Notes
- The model was created by Prosus AI (part of Naspers/Prosus global consumer internet group)
- Contact: dogu.araci[at]prosus[dot]com and zulkuf.genc[at]prosus[dot]com
- 83 fine-tuned models and 100+ Spaces built on this model indicate strong ecosystem
- Consider creating a HERMES_Quantum-specific fine-tuned version for quantum computing terminology in Phase 2+

---

**Evaluated By**: HERMES_Quantum Research Process
**Date**: 2025-12-28
**Last Updated**: 2025-12-28
