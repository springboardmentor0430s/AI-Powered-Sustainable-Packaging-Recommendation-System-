from __future__ import annotations

import json
import math
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
import requests

import prediction


# Small utilities

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _truncate(s: str, n: int) -> str:
    s = s or ""
    if len(s) <= n:
        return s
    return s[: max(0, n - 1)] + "…"


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return -1.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0.0 or nb <= 0.0:
        return -1.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


def _env_bool(name: str, default: bool) -> bool:
    v = (os.getenv(name) or "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "y", "on")


# ----------------------------
# RAG document representation
# ----------------------------

@dataclass
class RagDoc:
    doc_id: str
    title: str
    text: str
    meta: Dict[str, Any]


# ----------------------------
# EcoPackAI Chatbot (OpenAI-first + Hybrid RAG)
# ----------------------------

class EcoPackAIChatbot:
    """
    OpenAI-first assistant with hybrid retrieval:

    1) PRIMARY: OpenAI response augmented with retrieved context (RAG).
       - Semantic retrieval using embeddings when OPENAI_API_KEY is available.
       - Keyword fallback retrieval when embeddings are not available.

    2) TOOL AUGMENTATION: If it looks like a recommendation query and we can parse
       structured inputs, we run prediction.recommend(...) and provide those results
       to OpenAI for grounded explanation.

    3) FALLBACK: If OpenAI fails/unavailable -> rule-based FAQ -> RAG-only summary.
    """

    def __init__(self) -> None:
        # Load models/materials once
        prediction.load_models()

        # Your repo uses prediction._materials_raw
        df = getattr(prediction, "_materials_raw", None)
        self._materials_df: pd.DataFrame = df if isinstance(df, pd.DataFrame) else pd.DataFrame()

        # OpenAI configuration
        self._openai_key: str = (os.getenv("OPENAI_API_KEY") or "").strip()
        self._chat_model: str = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
        self._embed_model: str = (os.getenv("OPENAI_EMBEDDING_MODEL") or "text-embedding-3-small").strip()

        # RAG configuration
        self._rag_enable: bool = _env_bool("RAG_ENABLE", True)
        self._rag_top_k: int = int(os.getenv("RAG_TOP_K") or "6")
        self._rag_min_score: float = float(os.getenv("RAG_MIN_SCORE") or "0.20")
        self._rag_max_context_chars: int = int(os.getenv("RAG_MAX_CONTEXT_CHARS") or "3800")

        # Embeddings cache
        self._cache_dir = os.getenv("RAG_CACHE_DIR") or ".rag_cache"
        os.makedirs(self._cache_dir, exist_ok=True)

        # Build doc store from materials
        self._docs: List[RagDoc] = self._build_docs_from_materials(self._materials_df)

        # Embeddings store
        self._doc_embeddings: List[List[float]] = []
        self._embeddings_ready: bool = False

        # Build/load embeddings only if we have a key
        if self._rag_enable and self._docs and self._openai_key:
            self._load_or_build_embeddings()

    # ----------------------------
    # Public API used by main.py
    # ----------------------------

    def respond(self, question: str, history: Sequence[dict] = ()) -> str:
        q_raw = (question or "").strip()
        if not q_raw:
            return "Ask me about sustainable packaging materials, cost/CO₂ trade-offs, or how to export reports."

        # Greeting-only -> short friendly response
        if self._is_greeting_only(q_raw):
            return "Hi! Ask me about sustainable materials, cost savings, CO₂ trade-offs, or how to export reports."

        # PRIMARY: OpenAI-first (with hybrid retrieval + optional tool augmentation)
        if self._openai_key:
            try:
                return self._openai_primary(q_raw, history)
            except Exception:
                # swallow and fallback
                pass

        # FALLBACKS if OpenAI fails/unavailable
        fb = self._rule_based_fallback(q_raw)
        if fb:
            return fb

        rag_only = self._rag_only_answer(q_raw)
        if rag_only:
            return rag_only

        return (
            "I couldn’t generate a good answer right now. "
            "Try including product type, budget per unit, and constraints like moisture/grease resistance."
        )

    # ----------------------------
    # OpenAI primary path (RAG + tool augmentation)
    # ----------------------------

    def _openai_primary(self, question: str, history: Sequence[dict]) -> str:
        # 1) Retrieve context (semantic if possible, else keyword)
        rag_context = ""
        if self._rag_enable and self._docs:
            retrieved = self._retrieve(question, top_k=self._rag_top_k)
            rag_context = self._format_rag_context(retrieved, self._rag_max_context_chars)

        # 2) Tool augmentation: try to parse recommendation params and run prediction.recommend
        tool_context = ""
        if self._looks_like_reco(question):
            product = self._try_parse_product_from_text(question)
            if product:
                try:
                    recs = prediction.recommend(product)
                    if recs:
                        tool_context = self._format_recommendations_for_llm(product, recs[:5])
                except Exception:
                    tool_context = ""

        # 3) Build OpenAI messages
        messages = self._build_messages(
            question=question,
            history=history,
            rag_context=rag_context,
            tool_context=tool_context,
        )

        # 4) Call OpenAI
        answer = self._openai_chat(messages)
        if not answer:
            raise RuntimeError("OpenAI returned empty response")
        return answer.strip()

    def _build_messages(
        self,
        question: str,
        history: Sequence[dict],
        rag_context: str,
        tool_context: str,
    ) -> List[Dict[str, str]]:
        user_email = os.getenv("CHATBOT_CURRENT_USER_EMAIL") or ""
        company = os.getenv("CHATBOT_CURRENT_COMPANY") or ""

        system = (
            "You are EcoPackAI, an expert assistant for sustainable packaging decisions.\n"
            "Always answer the user’s question directly and completely.\n"
            "When the user compares options (e.g., cardboard vs recycled paper), include:\n"
            "• Clear recommendation (one line)\n"
            "• Cost vs CO₂ trade-offs (state assumptions if needed)\n"
            "• Practical constraints (food safety, moisture/grease barrier, durability)\n"
            "• A simple rule of thumb: “If you prioritize X, choose Y.”\n"
            "If the user asks about the app (reports/export), give step-by-step UI instructions.\n"
            "If unsure, ask ONE brief follow-up question at the end, but still give best-effort guidance.\n"
        )

        if user_email or company:
            system += f"\nUser context: {user_email or 'user'} at {company or 'their organization'}.\n"

        if rag_context.strip():
            system += "\nRetrieved materials context (use when relevant):\n" + rag_context + "\n"

        if tool_context.strip():
            system += "\nSystem-generated recommendation results (use as ground truth):\n" + tool_context + "\n"

        msgs: List[Dict[str, str]] = [{"role": "system", "content": system}]

        # Keep last ~10 messages of history
        hist = list(history or [])[-10:]
        for m in hist:
            role = str(m.get("role") or "").strip().lower()
            content = str(m.get("content") or "").strip()
            if not content:
                continue
            if role not in ("user", "assistant"):
                continue
            msgs.append({"role": role, "content": content})

        msgs.append({"role": "user", "content": question})
        return msgs

    def _openai_chat(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Raw HTTP call to Chat Completions API. Retries transient errors.
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._openai_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._chat_model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 750,
            "n": 1,
        }

        for attempt in range(3):
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices") or []
                if not choices:
                    return None
                msg = choices[0].get("message") or {}
                return (msg.get("content") or "").strip() or None

            # transient errors: backoff and retry
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(0.8 * (attempt + 1))
                continue

            return None

        return None

    # ----------------------------
    # Greeting-only detection
    # ----------------------------

    def _is_greeting_only(self, text: str) -> bool:
        t = _norm(text)
        return bool(re.fullmatch(r"(hi|hello|hey)( there)?[!. ]*", t))

    # ----------------------------
    # Advanced Hybrid RAG
    # ----------------------------

    def _build_docs_from_materials(self, df: pd.DataFrame) -> List[RagDoc]:
        if df is None or df.empty:
            return []

        # Try to use meaningful columns when present
        docs: List[RagDoc] = []

        # We'll construct a "profile" text per row that is searchable
        # using whatever columns exist (robust across schemas).
        for i, row in df.iterrows():
            row_dict = {str(k): row[k] for k in df.columns}

            # Find a good title
            title = ""
            for c in ("MaterialName", "materialName", "name", "material", "Material"):
                if c in df.columns:
                    v = row_dict.get(c)
                    if pd.notna(v):
                        title = str(v).strip()
                        break
            if not title:
                title = f"Material {i+1}"

            # Build dense text
            lines = [f"Material: {title}"]
            for c in df.columns:
                v = row_dict.get(c)
                if pd.isna(v):
                    continue
                # Keep it readable and compact
                lines.append(f"{c}: {v}")
            text = "\n".join(lines)

            docs.append(
                RagDoc(
                    doc_id=f"mat_{i}",
                    title=title,
                    text=text,
                    meta={"title": title},
                )
            )

        return docs

    def _cache_path(self) -> str:
        # cache depends on embedding model
        safe_model = re.sub(r"[^a-zA-Z0-9_.-]+", "_", self._embed_model)
        return os.path.join(self._cache_dir, f"materials_emb_{safe_model}.json")

    def _load_or_build_embeddings(self) -> None:
        path = self._cache_path()

        # Attempt load
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if (
                    data.get("embed_model") == self._embed_model
                    and data.get("count") == len(self._docs)
                    and isinstance(data.get("embeddings"), list)
                ):
                    embs = data["embeddings"]
                    if len(embs) == len(self._docs):
                        self._doc_embeddings = embs
                        self._embeddings_ready = True
                        return
            except Exception:
                pass

        # Build fresh
        embs: List[List[float]] = []
        for d in self._docs:
            e = self._embed_text(d.text)
            if not e:
                self._embeddings_ready = False
                self._doc_embeddings = []
                return
            embs.append(e)

        self._doc_embeddings = embs
        self._embeddings_ready = True

        # Save cache
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "embed_model": self._embed_model,
                        "count": len(self._docs),
                        "created_at": int(time.time()),
                        "embeddings": self._doc_embeddings,
                    },
                    f,
                )
        except Exception:
            pass

    def _embed_text(self, text: str) -> Optional[List[float]]:
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self._openai_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self._embed_model, "input": text}

        for attempt in range(3):
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                arr = data.get("data") or []
                if not arr:
                    return None
                emb = arr[0].get("embedding")
                if isinstance(emb, list) and emb:
                    return [float(x) for x in emb]
                return None

            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(0.8 * (attempt + 1))
                continue

            return None

        return None

    def _retrieve(self, query: str, top_k: int) -> List[Tuple[float, RagDoc]]:
        # Semantic retrieval if embeddings ready; else keyword
        if self._embeddings_ready and self._doc_embeddings:
            q_emb = self._embed_text(query)
            if not q_emb:
                return self._retrieve_keyword(query, top_k)

            scored: List[Tuple[float, RagDoc]] = []
            for doc, emb in zip(self._docs, self._doc_embeddings):
                s = _cosine(q_emb, emb)
                scored.append((s, doc))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [(s, d) for s, d in scored[:top_k] if s >= self._rag_min_score]

        return self._retrieve_keyword(query, top_k)

    def _retrieve_keyword(self, query: str, top_k: int) -> List[Tuple[float, RagDoc]]:
        q = _norm(query)
        terms = [t for t in re.split(r"[^a-z0-9]+", q) if t]
        if not terms:
            return []

        scored: List[Tuple[float, RagDoc]] = []
        for d in self._docs:
            txt = _norm(d.text)
            hits = sum(1 for t in terms if t in txt)
            score = hits / max(3, len(terms))
            scored.append((score, d))

        scored.sort(key=lambda x: x[0], reverse=True)
        # keyword scores are smaller; allow a slightly higher threshold
        return [(s, d) for s, d in scored[:top_k] if s >= 0.25]

    def _format_rag_context(self, retrieved: List[Tuple[float, RagDoc]], max_chars: int) -> str:
        if not retrieved:
            return ""

        parts: List[str] = []
        used = 0
        for score, doc in retrieved:
            block = f"[{doc.doc_id}] {doc.title} (score={score:.2f})\n{doc.text}\n"
            if used + len(block) > max_chars:
                block = _truncate(block, max_chars - used)
            parts.append(block)
            used += len(block)
            if used >= max_chars:
                break
        return "\n".join(parts).strip()

    # ----------------------------
    # Tool augmentation: recommender parsing + formatting
    # ----------------------------

    def _looks_like_reco(self, question: str) -> bool:
        q = _norm(question)
        keywords = [
            "recommend", "suggest", "which is better", "best", "choose", "option",
            "lowest co2", "lowest cost", "eco friendly", "eco-friendly", "compare",
            "cardboard", "paper", "plastic", "biodegradable", "recyclable",
            "budget", "packaging"
        ]
        return any(k in q for k in keywords)

    def _try_parse_product_from_text(self, q: str) -> Optional[Dict[str, Any]]:
        """
        Same spirit as your original parser, but slightly safer:
        returns None if user didn’t provide any usable parameter.
        """
        text = q or ""
        qn = _norm(text)

        product: Dict[str, Any] = {
            "productName": "Chat product",
            "category": "General",
            "weightKg": 1.0,
            "fragility": 5,
            "maxBudget": 10.0,
            "shippingDistance": 500.0,
            "moistureReq": 5,
            "oxygenSensitivity": 5,
            "preferredBiodegradable": 0,
            "preferredRecyclable": 0,
        }

        def grab_float(pattern: str) -> Optional[float]:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            return float(m.group(1)) if m else None

        def grab_int(pattern: str) -> Optional[int]:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            return int(float(m.group(1))) if m else None

        # budget under $X
        m_under = re.search(r"\bunder\s*\$?\s*(\d+(\.\d+)?)\b", qn)
        if m_under:
            product["maxBudget"] = float(m_under.group(1))

        w = grab_float(r"\bweight\s*[:=]?\s*(\d+(\.\d+)?)\b")
        if w is not None:
            product["weightKg"] = w

        f = grab_int(r"\bfragility\s*[:=]?\s*(\d+)\b")
        if f is not None:
            product["fragility"] = max(1, min(10, f))

        b = grab_float(r"\bbudget\s*[:=]?\s*\$?\s*(\d+(\.\d+)?)\b")
        if b is not None:
            product["maxBudget"] = b

        sd = grab_float(r"\bshipping\s*[:=]?\s*(\d+(\.\d+)?)\b")
        if sd is not None:
            product["shippingDistance"] = sd

        mr = grab_int(r"\bmoisture\s*[:=]?\s*(\d+)\b")
        if mr is not None:
            product["moistureReq"] = max(0, min(10, mr))

        ox = grab_int(r"\boxygen\s*[:=]?\s*(\d+)\b")
        if ox is not None:
            product["oxygenSensitivity"] = max(0, min(10, ox))

        cm = re.search(r"\bcategory\s*[:=]?\s*([a-zA-Z][a-zA-Z0-9 _-]{0,40})", text)
        if cm:
            product["category"] = cm.group(1).strip()

        # preferences
        if "recyclable" in qn:
            product["preferredRecyclable"] = 1
        if "biodegradable" in qn or "compostable" in qn:
            product["preferredBiodegradable"] = 1

        # heuristic: if user mentions a budget value like "0.4 dollars"
        m_budget2 = re.search(r"\b(\d+(\.\d+)?)\s*(usd|dollars|\$)\b", qn)
        if m_budget2 and "budget" not in qn:
            # treat as likely budget per unit in casual phrasing
            product["maxBudget"] = float(m_budget2.group(1))

        provided_any = any(k in qn for k in ["weight", "fragility", "budget", "shipping", "category", "moisture", "oxygen", "under", "$", "dollars", "usd"])
        return product if provided_any else None

    def _format_recommendations_for_llm(self, product: Dict[str, Any], recs: List[Dict[str, Any]]) -> str:
        lines = [
            f"User product constraints: {json.dumps(product, ensure_ascii=False)}",
            "Top system recommendations (from prediction.recommend):",
        ]
        for i, r in enumerate(recs, start=1):
            name = r.get("materialName", r.get("MaterialName", r.get("MaterialType", "Material")))
            score = r.get("suitabilityScore", r.get("rankingScore", ""))
            cost = r.get("predictedCost", r.get("predictedCostUSD", r.get("predicted_cost_unit_usd", "")))
            co2 = r.get("predictedCO2", r.get("predictedCO2KG", r.get("predicted_co2_unit_kg", "")))
            reason = r.get("reason", r.get("recommendationReason", ""))

            lines.append(
                f"{i}. {name} | score={score} | cost={cost} | co2={co2} | reason={_truncate(str(reason), 180)}"
            )
        return "\n".join(lines)

    # ----------------------------
    # Fallbacks
    # ----------------------------

    def _rule_based_fallback(self, question: str) -> Optional[str]:
        q = _norm(question)

        # Reports/export
        if any(k in q for k in ("export", "download", "report", "pdf", "excel")):
            return (
                "To export reports:\n"
                "1) Open the Dashboard page.\n"
                "2) In the Export/Download section, click PDF or Excel.\n"
                "3) The report summarizes your saved recommendations.\n"
                "If you don’t see buttons, confirm you’re logged in and you’ve generated at least one recommendation."
            )

        # Explain score
        if "suitability score" in q or ("suitability" in q and "score" in q):
            return (
                "Suitability score is a combined 0–100 ranking that balances CO₂ impact, cost efficiency, "
                "and constraint penalties (like barrier requirements). Higher is better overall."
            )

        return None

    def _rag_only_answer(self, question: str) -> Optional[str]:
        if not self._docs:
            return None

        retrieved = self._retrieve_keyword(question, top_k=5)
        if not retrieved:
            return None

        lines = ["I can’t reach the AI model right now, but here are the closest matching materials I found:"]
        for score, doc in retrieved[:3]:
            lines.append(f"- {doc.title} (match={score:.2f})")
        lines.append(
            "If you tell me your product type, budget per unit, and moisture/grease needs, I can narrow it down further."
        )
        return "\n".join(lines)


# Module-level singleton used by main.py: `from chatbot import chatbot`
chatbot = EcoPackAIChatbot()
