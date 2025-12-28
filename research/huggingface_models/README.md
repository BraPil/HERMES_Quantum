# HuggingFace Models Research

This directory contains research and evaluation of HuggingFace models for integration into the HERMES_Quantum system.

## Priority Models to Investigate

### Financial Sentiment Analysis
| Model | Status | Relevance | Notes |
|-------|--------|-----------|-------|
| ProsusAI/finbert | 🔴 Not Started | High - Core sentiment | Industry standard for financial text |
| yiyanghkust/finbert-tone | 🔴 Not Started | High - Tone analysis | Positive/negative/neutral classification |
| mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis | 🔴 Not Started | Medium | Lighter weight option |
| StephanAkkerman/FinTwitBERT-sentiment | 🔴 Not Started | High - Social media | Twitter-specific financial sentiment |

### Time Series Forecasting
| Model | Status | Relevance | Notes |
|-------|--------|-----------|-------|
| amazon/chronos-t5-large | 🔴 Not Started | High | Zero-shot time series forecasting |
| huggingface/autoformer | 🔴 Not Started | Medium | Long-term series forecasting |

### News/Text Classification
| Model | Status | Relevance | Notes |
|-------|--------|-----------|-------|
| nlptown/bert-base-multilingual-uncased-sentiment | 🔴 Not Started | Medium | General sentiment |

## Evaluation Criteria

When evaluating models, consider:

### Technical Criteria
- **Model Size**: Parameter count, memory requirements
- **Inference Speed**: Latency for real-time analysis
- **Accuracy**: Performance on relevant benchmarks
- **Fine-tuning Requirements**: Can we use out-of-box or need training?

### Domain Criteria
- **Domain Specificity**: Financial vs general domain
- **Data Compatibility**: Works with our target data types (news, tweets, filings)
- **Language Support**: English focus, multilingual support?
- **Time Sensitivity**: Handles current events and evolving language?

### Integration Criteria
- **API Compatibility**: Works with HuggingFace transformers library
- **Dependencies**: Compatible with our tech stack
- **Deployment**: Can be deployed in our infrastructure
- **Licensing**: Compatible with project license

### Agent Mapping
- **22_psychology**: Market psychology, investor sentiment models
- **23_social**: Social media monitoring, Twitter sentiment models
- **24_politics**: News classification, regulatory text analysis
- **25_market**: Time series forecasting, market trend models
- **11_analyst**: Integration frameworks, ensemble models

## Status Legend
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Evaluated
- ✅ Adopted
- ⏸️ Deferred
- ❌ Rejected

## Documentation Process

For each model:

1. **Discovery**: Add to priority list above
2. **Initial Review**: Check model card, basic specs
3. **Create Evaluation**: Use `TEMPLATE_model_evaluation.md`
4. **Testing**: Create notebook in `../notebooks/`
5. **Documentation**: Complete evaluation document
6. **Decision**: Mark status (Adopt/Defer/Reject)
7. **Update Log**: Add entry to `../EXPLORATION_LOG.md`
8. **Update State**: Increment counter in `../STATE.yaml`

## Evaluation Files

Create individual evaluation files in this directory:
- `finbert_evaluation.md`
- `finbert_tone_evaluation.md`
- `chronos_evaluation.md`
- etc.

Use the template: `TEMPLATE_model_evaluation.md`

## Quick Links

- [HuggingFace Models Hub](https://huggingface.co/models)
- [Financial NLP Models](https://huggingface.co/models?pipeline_tag=text-classification&search=financial)
- [Time Series Models](https://huggingface.co/models?pipeline_tag=time-series-forecasting)
- [Sentiment Analysis Models](https://huggingface.co/models?pipeline_tag=sentiment-analysis)

## Notes

### Model Selection Strategy
1. Start with established financial models (FinBERT family)
2. Evaluate lightweight alternatives for production deployment
3. Test social media specific models for Agent 23
4. Explore time series models for Agent 25
5. Consider ensemble approaches for Agent 11

### Testing Approach
- Use sample financial news articles
- Test with quantum computing stock mentions (QBTS, IONQ, RGTI, QUBT)
- Measure inference time on representative hardware
- Compare outputs across similar models
- Document edge cases and failure modes

### Integration Planning
- Plan for model serving architecture (local vs API)
- Consider caching strategies for repeated inference
- Design fallback mechanisms for model failures
- Document resource requirements for deployment
