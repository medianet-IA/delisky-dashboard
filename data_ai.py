# -*- coding: utf-8 -*-
"""
=============================================================
  DELISKY WORKFLOW — AI & DEEP ANALYSIS
  Market Basket Analysis, ABC Segmentation, Clustering
=============================================================
"""

import pandas as pd
import numpy as np
from pathlib import Path
from mlxtend.frequent_patterns import apriori, association_rules
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ─── PATHS ──────────────────────────────────────────────────────────────────
BASE    = Path(__file__).parent
CLEANED = BASE / "cleaned"
RESULTS = BASE / "analysis_results"

def run_ai_analysis():
    print("--- Starting AI & Deep Analysis ---")
    
    # Load Cleaned Data
    df_sales = pd.read_csv(CLEANED / "Sales_all.csv")
    df_items = pd.read_csv(CLEANED / "Items_all.csv")
    df_pos   = pd.read_csv(CLEANED / "PoS_all.csv")
    
    # ─── 1. MARKET BASKET ANALYSIS (MBA) ───────────────────────────────────
    print("1. Running Market Basket Analysis...")
    # Transaction = Nom du client or Invoice (if we had one)
    # Pivot items per client/visit
    # We group by "Nom du client" for overall associations
    basket = (df_items.groupby(['Client', 'Article'])['Qté vendue']
              .sum().unstack().reset_index().fillna(0)
              .set_index('Client'))
    
    # Encode values to 1/0
    def encode_units(x):
        return 1 if x >= 1 else 0
    basket_sets = basket.applymap(encode_units)
    
    # Filter out empty baskets
    basket_sets = basket_sets[(basket_sets.sum(axis=1) > 0)]
    
    try:
        frequent_itemsets = apriori(basket_sets, min_support=0.05, use_colnames=True)
        rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1)
        rules = rules.sort_values(['lift', 'confidence'], ascending=False)
        rules.to_csv(RESULTS / "AI_market_basket_rules.csv", index=False)
        print(f"   MBA: Found {len(rules)} rules.")
    except Exception as e:
        print(f"   MBA Error: {e}")

    # ─── 2. ABC PRODUCT SEGMENTATION ────────────────────────────────────────
    print("2. Running ABC Product Segmentation...")
    product_revenue = df_items.groupby('Article')['Qté vendue'].sum().reset_index()
    # Merging with prices would be better, but we use qty as a proxy or join from Sales
    # Let's join with Sales to get real revenue if possible, or use total units
    product_revenue = df_items.groupby('Article').agg({
        'Qté vendue': 'sum'
    }).sort_values('Qté vendue', ascending=False).reset_index()
    
    product_revenue['CumSum'] = product_revenue['Qté vendue'].cumsum()
    product_revenue['TotalSum'] = product_revenue['Qté vendue'].sum()
    product_revenue['CumPct'] = product_revenue['CumSum'] / product_revenue['TotalSum']
    
    def abc_class(pct):
        if pct <= 0.8: return 'A (VIP)'
        elif pct <= 0.95: return 'B (Medium)'
        else: return 'C (Low)'
    
    product_revenue['Class'] = product_revenue['CumPct'].apply(abc_class)
    product_revenue.to_csv(RESULTS / "AI_product_abc_analysis.csv", index=False)
    print("   ABC: Segmentation complete.")

    # ─── 3. CLIENT CLUSTERING (K-MEANS) ─────────────────────────────────────
    print("3. Running Client Clustering...")
    client_stats = df_sales.groupby('Nom du client').agg({
        'Total': 'sum',
        'Nom du client': 'count'
    }).rename(columns={'Nom du client': 'Visits'}).reset_index()
    
    # Feature Scaling
    features = client_stats[['Total', 'Visits']]
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    # K-Means (3 clusters: VIP, Regular, Low)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    client_stats['Cluster'] = kmeans.fit_predict(scaled_features)
    
    # Name clusters based on mean Total Spend
    cluster_means = client_stats.groupby('Cluster')['Total'].mean().sort_values(ascending=False)
    name_map = {
        cluster_means.index[0]: "VIP (High Value)",
        cluster_means.index[1]: "Regular",
        cluster_means.index[2]: "Low Frequency/Value"
    }
    client_stats['Segment'] = client_stats['Cluster'].map(name_map)
    client_stats.to_csv(RESULTS / "AI_client_segments.csv", index=False)
    print("   Clustering: Complete.")
    
    print("--- AI Analysis Finished! ---")

if __name__ == "__main__":
    run_ai_analysis()
