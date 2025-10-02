from PIL import Image
import streamlit as st
import pandas as pd
import re
import ast

def app_filtro_relatorio_macro():

    @st.cache_data
    def load_data():
        return pd.read_csv("data/base_completa.csv")

    df = load_data()

    # Corrigir a variável text_percentage, nos valores que forem acimas de 1 100
    if "text_percentage" in df.columns:
        df["text_percentage"] = df["text_percentage"].apply(
            lambda x: x / 100 if pd.notnull(x) and x > 1 else x
        )


    df["post_date"] = (
            pd.to_datetime(df["post_date"], errors="coerce", utc=True)
            .dt.tz_localize(None)
        )

    with st.expander("Filtros"):
        c1, c2 = st.columns(2)

        # 1) Filtro de datas
        if df["post_date"].notna().any():
            min_date = df["post_date"].min().date()
            max_date = df["post_date"].max().date()
            date_start, date_end = c1.slider(
                "Período de publicação",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="DD/MM/YYYY",
            )
        else:
            date_start = date_end = None
            c1.info("Sem datas válidas em 'post_date'.")

        # 2) Filtro por tipo de post
        post_types = sorted(df["media_kind"].dropna().unique().tolist()) if "media_kind" in df.columns else []
        post_type_sel = c2.multiselect("Tipo de Publicação", post_types, default=post_types)

    # =========================
    # Aplicar filtros
    # =========================
    base_filtrada = df.copy()

    if date_start and date_end:
        base_filtrada = base_filtrada[
            (base_filtrada["post_date"] >= pd.to_datetime(date_start))
            & (base_filtrada["post_date"] <= pd.to_datetime(date_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1))
        ]

    if post_types and post_type_sel:
        base_filtrada = base_filtrada[base_filtrada["media_kind"].isin(post_type_sel)]

    return base_filtrada