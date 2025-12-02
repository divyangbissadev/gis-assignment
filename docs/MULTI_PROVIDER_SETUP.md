# Multi-Provider Setup Guide

The NLP Query Parser now supports **three LLM providers**: Anthropic Claude, OpenAI GPT, and Google Gemini. This guide shows you how to set up and use each provider.

## 📦 Installation

Install the provider(s) you want to use:

```bash
# Install all providers
pip install anthropic openai google-generativeai

# Or install individually
pip install anthropic          # For Claude
pip install openai             # For GPT
pip install google-generativeai # For Gemini
```

## 🔑 Get API Keys

### Anthropic Claude

1. Sign up at: **https://console.anthropic.com/**
2. Navigate to **API Keys** section
3. Click **"Create Key"**
4. Copy your key (starts with `sk-ant-...`)

**Default Model**: `claude-sonnet-4-5-20250929`

**Other Models**:
- `claude-opus-4-5-20250229` (more powerful)
- `claude-3-5-sonnet-20241022` (faster)

### OpenAI GPT

1. Sign up at: **https://platform.openai.com/signup**
2. Navigate to **API Keys**
3. Click **"Create new secret key"**
4. Copy your key (starts with `sk-...`)

**Default Model**: `gpt-4o`

**Other Models**:
- `gpt-4o-mini` (faster, cheaper)
- `gpt-4-turbo`
- `gpt-3.5-turbo` (cheapest)

### Google Gemini

1. Go to: **https://makersuite.google.com/app/apikey**
2. Click **"Create API Key"**
3. Copy your key

**Default Model**: `gemini-1.5-pro`

**Other Models**:
- `gemini-1.5-flash` (faster)
- `gemini-pro`

## ⚙️ Configuration

### Option 1: Environment Variables (Recommended)

Create a `.env` file in your project root:

```bash
# Choose one or more providers

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# OpenAI GPT
OPENAI_API_KEY=sk-your-key-here

# Google Gemini
GEMINI_API_KEY=your-key-here
```

### Option 2: Direct in Code

Pass API keys directly when creating the parser:

```python
from src.nlp_query_parser import NLPQueryParser

# With API key
parser = NLPQueryParser(
    provider="openai",
    api_key="sk-your-key-here"
)
```

## 🚀 Usage Examples

### Basic Usage (Anthropic - Default)

```python
from src.nlp_query_parser import NLPQueryParser

# Uses ANTHROPIC_API_KEY from environment
parser = NLPQueryParser()

result = parser.parse("find counties in Texas under 2500 square miles")
print(result.where_clause)
# Output: STATE_NAME = 'Texas' AND SQMI < 2500
```

### Use OpenAI GPT

```python
from src.nlp_query_parser import NLPQueryParser

# Uses OPENAI_API_KEY from environment
parser = NLPQueryParser(provider="openai")

result = parser.parse("counties in California with population over 1 million")
print(result.where_clause)
# Output: STATE_NAME = 'California' AND POPULATION > 1000000
```

### Use Google Gemini

```python
from src.nlp_query_parser import NLPQueryParser

# Uses GEMINI_API_KEY from environment
parser = NLPQueryParser(provider="gemini")

result = parser.parse("show me counties in Texas or Oklahoma")
print(result.where_clause)
# Output: STATE_NAME IN ('Texas', 'Oklahoma')
```

### Custom Model Selection

```python
# Use GPT-4 Turbo
parser = NLPQueryParser(provider="openai", model="gpt-4-turbo")

# Use Claude Opus (more powerful)
parser = NLPQueryParser(provider="anthropic", model="claude-opus-4-5-20250229")

# Use Gemini Flash (faster)
parser = NLPQueryParser(provider="gemini", model="gemini-1.5-flash")
```

### Pass API Key Directly

```python
parser = NLPQueryParser(
    provider="openai",
    api_key="sk-your-key-here",
    model="gpt-4o"
)
```

## 📊 Provider Comparison

| Feature | Anthropic Claude | OpenAI GPT | Google Gemini |
|---------|-----------------|------------|---------------|
| **Default Model** | claude-sonnet-4-5 | gpt-4o | gemini-1.5-pro |
| **Speed** | Fast | Fast | Very Fast |
| **Accuracy** | Excellent | Excellent | Excellent |
| **Cost** | $$ | $$$ | $ |
| **Context Window** | 200K tokens | 128K tokens | 1M tokens |
| **Best For** | Accuracy & Safety | General Purpose | Long Context |

## 🔍 Check Available Providers

```python
from src.nlp_query_parser import NLPQueryParser

providers = NLPQueryParser.get_available_providers()

for name, info in providers.items():
    print(f"\n{info['name']}")
    print(f"  Default Model: {info['default_model']}")
    print(f"  Environment Variable: {info['env_var']}")
    print(f"  Sign Up: {info['signup_url']}")
    print(f"  Available Models: {', '.join(info['models'])}")
```

Output:
```
Anthropic Claude
  Default Model: claude-sonnet-4-5-20250929
  Environment Variable: ANTHROPIC_API_KEY
  Sign Up: https://console.anthropic.com/
  Available Models: claude-sonnet-4-5-20250929, claude-opus-4-5-20250229, ...

OpenAI GPT
  Default Model: gpt-4o
  Environment Variable: OPENAI_API_KEY
  Sign Up: https://platform.openai.com/signup
  Available Models: gpt-4o, gpt-4o-mini, gpt-4-turbo, ...

Google Gemini
  Default Model: gemini-1.5-pro
  Environment Variable: GEMINI_API_KEY
  Sign Up: https://makersuite.google.com/app/apikey
  Available Models: gemini-1.5-pro, gemini-1.5-flash, ...
```

## 💰 Cost Comparison (Approximate)

Per 100 queries (assuming ~700 tokens per query):

| Provider | Model | Cost |
|----------|-------|------|
| Anthropic | claude-sonnet-4-5 | ~$0.21 |
| Anthropic | claude-opus-4-5 | ~$1.05 |
| OpenAI | gpt-4o | ~$0.35 |
| OpenAI | gpt-4o-mini | ~$0.05 |
| OpenAI | gpt-3.5-turbo | ~$0.07 |
| Gemini | gemini-1.5-pro | ~$0.25 |
| Gemini | gemini-1.5-flash | ~$0.03 |

**Recommendation for Production**:
- **Best Value**: Gemini Flash or GPT-4o Mini
- **Best Accuracy**: Claude Opus or GPT-4o
- **Balanced**: Claude Sonnet or Gemini Pro

## 🧪 Testing Different Providers

```python
from src.nlp_query_parser import NLPQueryParser

query = "find large counties in Texas over 3000 square miles"

# Test with all providers
providers = ["anthropic", "openai", "gemini"]

for provider_name in providers:
    try:
        parser = NLPQueryParser(provider=provider_name)
        result = parser.parse(query)

        print(f"\n{provider_name.upper()}:")
        print(f"  WHERE: {result.where_clause}")
        print(f"  Confidence: {result.confidence:.2%}")

    except Exception as e:
        print(f"\n{provider_name.upper()}: {e}")
```

## 🔒 Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** or secure vaults
3. **Rotate keys regularly** (every 90 days)
4. **Set usage limits** in provider dashboards
5. **Monitor usage** for unexpected spikes
6. **Use different keys** for dev/staging/production

## 🛠️ Troubleshooting

### "API key required" error

**Problem**: API key not found

**Solution**:
```bash
# Check if environment variable is set
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
echo $GEMINI_API_KEY

# Set it
export ANTHROPIC_API_KEY='your-key'
```

### "Module not found" error

**Problem**: Provider package not installed

**Solution**:
```bash
pip install anthropic  # For Claude
pip install openai     # For GPT
pip install google-generativeai  # For Gemini
```

### "Unsupported provider" error

**Problem**: Invalid provider name

**Solution**: Use one of: `"anthropic"`, `"openai"`, or `"gemini"`

```python
# ✓ Correct
parser = NLPQueryParser(provider="openai")

# ✗ Wrong
parser = NLPQueryParser(provider="gpt")  # Use "openai" not "gpt"
```

### Rate limit errors

**Problem**: Too many requests

**Solutions**:
- Add delays between requests
- Implement caching for common queries
- Upgrade to higher tier plan
- Use a faster/cheaper model for testing

## 📚 Complete Example

```python
#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

from src.nlp_query_parser import NLPQueryParser
from src.arcgis_client import ArcGISClient

# Initialize with your preferred provider
parser = NLPQueryParser(
    provider="anthropic",  # or "openai" or "gemini"
    # api_key="optional-key",  # or use env var
    # model="custom-model"     # or use default
)

# Parse natural language query
query = "find counties in Texas under 2500 square miles"
result = parser.parse(query)

print(f"Query: {query}")
print(f"WHERE: {result.where_clause}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Explanation: {result.explanation}")

# Execute against ArcGIS
service_url = (
    "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
    "USA_Census_Counties/FeatureServer/0"
)

client = ArcGISClient(service_url)
features = client.query(where=result.where_clause, page_size=100)

print(f"\nFound {len(features['features'])} counties")
```

## 🔄 Switching Providers

You can easily switch between providers without changing your code:

```bash
# .env file - just comment/uncomment the one you want
# ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...
```

Then in code:
```python
# Reads from active env var
parser = NLPQueryParser(provider="openai")  # Change provider name only
```

## 📖 Additional Resources

- **Anthropic Docs**: https://docs.anthropic.com/
- **OpenAI Docs**: https://platform.openai.com/docs
- **Gemini Docs**: https://ai.google.dev/docs

---

**Last Updated**: 2025-12-02
**Supported Providers**: Anthropic, OpenAI, Google Gemini
