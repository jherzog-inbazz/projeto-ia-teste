from PIL import Image
import streamlit as st
import pandas as pd
import re
import ast


def app_relatorio_macro():
    st.markdown("# Insights de Performance dos Conteúdos")

    @st.cache_data
    def load_data():
        return pd.read_csv("data/base_completa.csv")

    df = load_data()

    # =========================
    # Preparos de campos (datas e interação)
    # =========================
    if "post_date" in df.columns:
        # se suas datas estiverem no formato dia/mês/ano, habilite dayfirst=True
        df["post_date"] = (
            pd.to_datetime(df["post_date"], errors="coerce", utc=True)
            .dt.tz_localize(None)
        )
    else:
        st.warning("Coluna 'post_date' não encontrada no CSV.")
        df["post_date"] = pd.NaT

    # Mantemos o cálculo de interações para métricas internas (não filtra mais por isso)
    interaction_cols = [c for c in ["post_likes", "post_comments", "post_interactions"] if c in df.columns]
    for col in interaction_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if interaction_cols:
        df["sum_interactions"] = df[interaction_cols].sum(axis=1)
        df["has_interaction"] = df["sum_interactions"] > 0
    else:
        df["sum_interactions"] = 0
        df["has_interaction"] = False

    # =========================
    # Filtros (apenas datas e post_type)
    # =========================
    with st.expander("Filtros"):
        c1, c2 = st.columns(2)

        # 1) Filtro de datas
        if df["post_date"].notna().any():
            min_date = df["post_date"].min().date()
            max_date = df["post_date"].max().date()
            date_start, date_end = c1.slider(
                "Período (post_date)",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="DD/MM/YYYY",
            )
        else:
            date_start = date_end = None
            c1.info("Sem datas válidas em 'post_date'.")

        # 2) Filtro por tipo de post
        post_types = sorted(df["post_type"].dropna().unique().tolist()) if "post_type" in df.columns else []
        post_type_sel = c2.multiselect("Tipo de post (post_type)", post_types, default=post_types)

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
        base_filtrada = base_filtrada[base_filtrada["post_type"].isin(post_type_sel)]

    st.write(f"**Posts filtrados:** {len(base_filtrada)}")

    # =========================
    # 📊 Conceitos Básicos
    # =========================
    with st.container():
        st.subheader("📊 Conceitos Básicos")

        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

        total_posts = len(base_filtrada)
        pct_faces   = (base_filtrada["face_present"].mean()*100)     if "face_present"     in base_filtrada.columns else 0
        pct_prod    = (base_filtrada["product_visible"].mean()*100)  if "product_visible"  in base_filtrada.columns else 0
        avg_chars   =  base_filtrada["num_characters"].mean()        if "num_characters"   in base_filtrada.columns else 0
        avg_textp   =  base_filtrada["text_percentage"].mean()       if "text_percentage"  in base_filtrada.columns else 0
        pct_hashtag = (base_filtrada["hashtag_detected"].mean()*100) if "hashtag_detected" in base_filtrada.columns else 0
        pct_cupom   = (base_filtrada["coupon_detected"].mean()*100)  if "coupon_detected"  in base_filtrada.columns else 0

        c1.metric("Total de posts", total_posts)
        c2.metric("% com rosto", f"{pct_faces:.1f}%")
        c3.metric("% produto visível", f"{pct_prod:.1f}%")
        c4.metric("Média caracteres", f"{avg_chars:.0f}")
        c5.metric("Texto na imagem (média %)", f"{avg_textp:.1f}%")
        c6.metric("% com hashtag", f"{pct_hashtag:.1f}%")
        c7.metric("% com cupom", f"{pct_cupom:.1f}%")

    # =========================
    # 🌎 Ambiente & 📍 Localização
    # =========================
    with st.container():
        st.subheader("🌎 Ambiente & 📍 Localização")

        col1, col2 = st.columns(2)

        # 1) % de posts por environment
        with col1:
            st.markdown("**Distribuição de posts por ambiente (%)**")
            if "environment" in base_filtrada.columns and not base_filtrada.empty:
                env_series = (
                    base_filtrada["environment"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .replace({"": "unknown", "nan": "unknown"})
                    .fillna("unknown")
                )
                # restringe a 3 grupos principais
                env_series = env_series.where(env_series.isin(["externo", "interno", "unknown"]), "unknown")

                env_pct = (
                    env_series.value_counts(normalize=True)
                    .mul(100.0)
                    .rename("percent")
                    .reset_index()
                    .rename(columns={"index": "environment"})
                )

                # ordenação fixa
                env_order = pd.CategoricalDtype(categories=["externo", "interno", "unknown"], ordered=True)
                env_pct["environment"] = env_pct["environment"].astype(env_order)
                env_pct = env_pct.sort_values("environment")

                if not env_pct.empty:
                    # para charts Altair/Vega-Lite use 'container' ou número
                    st.bar_chart(env_pct.set_index("environment"), width='container')
                else:
                    st.info("Sem dados para exibir em `environment` após filtros.")
            else:
                st.info("Coluna `environment` não encontrada na base ou base vazia.")

        # 2) % de posts por location
        with col2:
            st.markdown("**Distribuição de posts por localização (%)**")
            if "location" in base_filtrada.columns and not base_filtrada.empty:
                loc_series = (
                    base_filtrada["location"]
                    .astype(str)
                    .str.strip()
                    .replace({"": "unknown", "nan": "unknown"})
                    .fillna("unknown")
                )

                loc_pct = (
                    loc_series.value_counts(normalize=True)
                    .mul(100.0)
                    .rename("percent")
                    .reset_index()
                    .rename(columns={"index": "location"})
                    .sort_values("percent", ascending=False)
                )

                if not loc_pct.empty:
                    st.bar_chart(loc_pct.set_index("location"), width='container')
                else:
                    st.info("Sem dados para exibir em `location` após filtros.")
            else:
                st.info("Coluna `location` não encontrada na base ou base vazia.")


    # =========================
    # 🔤 Nuvem de Palavras + 🏷️ Top 3 Objetos (mesmo container, 2 colunas)
    # =========================
    with st.container():
        st.subheader("🔤 Nuvem de Palavras & 🏷️ Top 3 Objetos")
        col_wc, col_obj = st.columns(2)

        # -------- Coluna Esquerda: Nuvem de Palavras (words_used) --------
        with col_wc:
            st.markdown("**Nuvem de Palavras (words_used)**")
            if "words_used" in base_filtrada.columns and not base_filtrada.empty:
                import re, ast
                # aceita lista real, string de lista ou texto simples
                def to_text(x):
                    if pd.isna(x):
                        return ""
                    if isinstance(x, list):
                        return " ".join(str(i) for i in x)
                    s = str(x)
                    try:
                        parsed = ast.literal_eval(s)
                        if isinstance(parsed, list):
                            return " ".join(str(i) for i in parsed)
                    except Exception:
                        pass
                    return s

                texts = base_filtrada["words_used"].apply(to_text).astype(str)
                full_text = " ".join(texts.tolist())

                # limpeza simples
                full_text = re.sub(r"http\S+", " ", full_text)        # URLs
                full_text = re.sub(r"[@#]\w+", " ", full_text)        # @user e #hashtag
                full_text = re.sub(r"[\n\r\t]", " ", full_text)
                full_text = re.sub(r"\s{2,}", " ", full_text).strip()

                try:
                    from wordcloud import WordCloud, STOPWORDS
                    import matplotlib.pyplot as plt

                    extra_stops = {
                        "de","da","do","das","dos","e","a","o","as","os","pra","para","com","sem","em",
                        "na","no","nas","nos","um","uma","que","por","se","ao","aos","à","às","é","vai",
                        "tá","hoje","amanhã","ontem","mais","menos","muito","pouco","já"
                    }
                    stops = STOPWORDS.union(extra_stops)

                    wc = WordCloud(
                        width=1200,
                        height=450,
                        background_color="white",
                        stopwords=stops,
                        collocations=False,
                    ).generate(full_text)

                    fig = plt.figure(figsize=(12, 4.5))
                    plt.imshow(wc, interpolation="bilinear")
                    plt.axis("off")
                    st.pyplot(fig, clear_figure=True)
                except ModuleNotFoundError:
                    st.info("Pacote `wordcloud` não encontrado. Instale com: `pip install wordcloud`")
            else:
                st.info("Coluna `words_used` não encontrada ou sem dados após os filtros.")

        # -------- Coluna Direita: Top 3 Objetos (top_3_objects) --------
        with col_obj:
            st.markdown("**Top 3 Objetos (top_3_objects)**")
            if "top_3_objects" in base_filtrada.columns and not base_filtrada.empty:
                def split_objects(val):
                    if pd.isna(val):
                        return []
                    s = str(val)
                    return [p.strip().lower() for p in s.split("/") if p.strip()]

                exploded = base_filtrada[["top_3_objects"]].assign(
                    _obj=lambda d: d["top_3_objects"].apply(split_objects)
                ).explode("_obj")

                if "_obj" in exploded.columns and exploded["_obj"].notna().any():
                    counts = exploded["_obj"].value_counts()
                    top3 = counts.head(3)
                    if not top3.empty:
                        st.bar_chart(top3, width='container')
                    else:
                        st.info("Sem objetos suficientes após o parsing.")
                else:
                    st.info("Nenhum objeto válido encontrado em `top_3_objects`.")
            else:
                st.info("Coluna `top_3_objects` não encontrada ou sem dados após os filtros.")

