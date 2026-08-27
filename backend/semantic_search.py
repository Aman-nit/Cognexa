"""Semantic search over the insurance business rules YAML."""

from pathlib import Path

import streamlit as st
import yaml


# YAML knowledge base path.
YAML_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "semantic_insurance_business_rules.yaml"
)


# Load YAML file.
def load_yaml():
    with open(YAML_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


# Convert important YAML sections into passages.
def create_passages(data):
    passages = []

    # Create a dictionary of rules for easy lookup.
    rules_dict = {
        rule.get('rule_id'): rule for rule in data.get("business_rules", [])
    }

    # Add business rules.
    for rule in data.get("business_rules", []):
        text = (
            f"Rule ID: {rule.get('rule_id')}\n"
            f"Rule Name: {rule.get('name')}\n"
            f"Category: {rule.get('category')}\n"
            f"Description: {rule.get('description')}\n"
            f"Severity: {rule.get('severity')}\n"
            f"Logic: {rule.get('logic')}\n"
            f"Recommended Action: {rule.get('recommended_action', '')}\n"
            f"Interpretation: {rule.get('interpretation_note', '')}"
        )

        passages.append(text)

    # Add question patterns.
    for pattern in data.get("question_patterns", []):
        required_rules = pattern.get('required_rule_ids', [])
        rule_texts = []
        for r_id in required_rules:
            if r_id in rules_dict:
                r = rules_dict[r_id]
                rule_texts.append(f"  - {r_id}: {r.get('name')} ({r.get('description')})")
        rule_info = "\n" + "\n".join(rule_texts) if rule_texts else " None"

        text = (
            f"Question Pattern: {pattern.get('pattern_id')}\n"
            f"Example Question: {pattern.get('example_question')}\n"
            f"Intent: {pattern.get('intent')}\n"
            f"Required Rules: {pattern.get('required_rule_ids', [])}\n"
            f"Rule Definitions:{rule_info}\n"
            f"Requirements: {pattern.get('requirements', [])}"
        )

        passages.append(text)

    # Add investigation categories.
    for category in data.get("investigation_categories", []):
        cat_rules = category.get('rule_ids', [])
        rule_texts = []
        for r_id in cat_rules:
            if r_id in rules_dict:
                r = rules_dict[r_id]
                rule_texts.append(f"  - {r_id}: {r.get('name')} ({r.get('description')})")
        rule_info = "\n" + "\n".join(rule_texts) if rule_texts else " None"

        text = (
            f"Investigation Category: {category.get('category_id')}\n"
            f"Name: {category.get('name')}\n"
            f"Rules: {category.get('rule_ids')}\n"
            f"Rule Definitions:{rule_info}\n"
            f"Synonyms: {category.get('synonyms')}"
        )

        passages.append(text)

    # Add business objectives.
    objective = data.get("business_objective", {})

    if objective:
        text = (
            f"Business Objective\n"
            f"Primary Goal: {objective.get('primary_goal')}\n"
            f"Secondary Goals: {objective.get('secondary_goals')}"
        )

        passages.append(text)

    return passages


@st.cache_resource
def get_search_index():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    data = load_yaml()
    passages = create_passages(data)
    embeddings = model.encode(
        passages,
        convert_to_tensor=True,
        show_progress_bar=False,
    )

    return model, passages, embeddings


# Search YAML knowledge.
def semantic_search(query, top_k=5):

    from sentence_transformers import util

    model, passages, embeddings = get_search_index()

    # Convert question to embedding.
    query_embedding = model.encode(
        query,
        convert_to_tensor=True,
    )

    # Calculate similarity.
    scores = util.cos_sim(
        query_embedding,
        embeddings,
    )[0]

    # Get best results.
    top_results = scores.topk(
        min(top_k, len(passages))
    )

    results = []

    # Keep only relevant results.
    for score, index in zip(
        top_results.values.tolist(),
        top_results.indices.tolist(),
    ):
        if score >= 0.30:
            results.append(passages[index])

    return results


# Test semantic search.
if __name__ == "__main__":

    query = input("Enter search query: ")

    results = semantic_search(
        query,
        top_k=5,
    )

    print(f"\nTop {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        print(f"[{i}]")
        print(result)
        print()