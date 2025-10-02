import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import re
from wordcloud import WordCloud, STOPWORDS


def app_funcao_conceito_basico(base_filtrada):
    
    with st.container():
        st.subheader("📊 Conceitos Básicos")

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        total_posts = len(base_filtrada)
        pct_faces   = (base_filtrada["face_present"].mean()*100) if "face_present"     in base_filtrada.columns else 0
        pct_prod    = (base_filtrada["produto_divulgado"].mean()*100) if "produto_divulgado"  in base_filtrada.columns else 0
        avg_chars   =  base_filtrada["num_characters"].mean() if "num_characters"   in base_filtrada.columns else 0
        avg_textp   = (base_filtrada["text_percentage"].mean()*100) if "text_percentage"  in base_filtrada.columns else 0
        pct_cupom   = (base_filtrada["coupon_detected"].mean()*100) if "coupon_detected"  in base_filtrada.columns else 0

        c1.metric("Total de posts", total_posts)
        c2.metric("% com rosto", f"{pct_faces:.1f}%")
        c3.metric("% produto visível", f"{pct_prod:.1f}%")
        c4.metric("Média caracteres por post", f"{avg_chars:.0f}")
        c5.metric("Texto na imagem (média %)", f"{avg_textp:.1f}%")
        c6.metric("% com cupom", f"{pct_cupom:.1f}%")

# Gráfico de barras para tipos de post
def app_funcao_tipo_post(base_filtrada):
    # Verifique se a coluna 'media_kind' existe na base e se a base não está vazia
    if "media_kind" in base_filtrada.columns and not base_filtrada.empty:
        # Contagem dos tipos de post e cálculo das porcentagens
        tipo_contagem = base_filtrada["media_kind"].value_counts(normalize=True).reset_index()
        tipo_contagem.columns = ["Tipo de Post", "Porcentagem"]

        # Multiplica por 100 para transformar em porcentagem e arredonda para 2 casas decimais
        tipo_contagem["Porcentagem"] = (tipo_contagem["Porcentagem"] * 100).round(2)

        # Verifique se existe apenas um tipo de post e exiba a porcentagem de 100%
        if len(tipo_contagem) == 1:
            # Exibe o valor de 100% se existir apenas um tipo de post
            st.write(f"O tipo de post único representa 100% dos posts: {tipo_contagem.iloc[0, 0]} - 100.00%")
        else:
            # Cria o gráfico de barras vertical
            fig = px.bar(tipo_contagem, 
                         x="Tipo de Post", 
                         y="Porcentagem", 
                         title="Porcentagem de Tipos de Posts",
                         labels={"Porcentagem": "Porcentagem (%)", "Tipo de Post": "Tipo de Post"},
                         color="Porcentagem",  # A cor vai depender da porcentagem
                         color_continuous_scale="Blues",  # Escala de cores azul
                         text="Porcentagem"  # Mostrar o valor de porcentagem nas barras
                         )

            # Exibe o gráfico
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.update_layout(showlegend=False)  # Remove a legenda
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Coluna `media_kind` não encontrada ou base vazia.")



def app_funcao_objetos(base_filtrada):
    
    # Contador para os objetos
    objeto_counter = Counter()

    # Iterar sobre cada linha da base_filtrada e contar os objetos
    for top_3 in base_filtrada['top3_objects']:
        if pd.notnull(top_3):  # Verifica se a célula não está vazia
            objetos = top_3.split('/')  # Divide os objetos por "/"
            objeto_counter.update(objetos)  # Conta cada objeto encontrado
    
    # Extrair os 10 objetos mais comuns
    top_10_objetos = objeto_counter.most_common(10)
    
    # Separar os dados para plotagem
    objetos = [item[0] for item in top_10_objetos]  # Lista dos objetos
    contagem = [item[1] for item in top_10_objetos]  # Contagem de cada objeto

    # Criar um DataFrame para o Plotly
    df = pd.DataFrame({
        'Objeto': objetos,
        'Contagem': contagem
    })

    # Ordenar os dados em ordem decrescente
    df = df.sort_values(by='Contagem', ascending=True)

    # Criar o gráfico de barras horizontais
    fig = px.bar(df, 
                 x='Contagem', 
                 y='Objeto', 
                 title='Top 10 Objetos mais Encontrados',
                 labels={'Contagem': 'Contagem de Objetos', 'Objeto': 'Objeto'},
                 color='Contagem',  # Cor das barras com base na contagem
                 color_continuous_scale='RdBu',  # Escala de cores vermelho para azul
                 orientation='h',  # Definir barras horizontais
                 text='Contagem'  # Exibir os valores das contagens nas barras
                 )

    # Excluir a legenda de cores
    fig.update_layout(coloraxis_showscale=False)

    # Exibir o gráfico
    fig.update_traces(texttemplate='%{text}', textposition='inside')
    st.plotly_chart(fig, use_container_width=True)

def app_funcao_serie_dia_tipo(base_filtrada):
    # Criar série temporal de posts por dia e tipo
    if "media_kind" in base_filtrada.columns and "post_date" in base_filtrada.columns and not base_filtrada.empty:
        # Converter a coluna 'post_date' para datetime
        base_filtrada['post_date'] = pd.to_datetime(base_filtrada['post_date'], errors='coerce')

        # Filtrar apenas as linhas com datas válidas
        base_filtrada = base_filtrada.dropna(subset=['post_date'])

        # Agrupar por data e tipo de mídia, contando o número de posts
        serie_tipo = (base_filtrada
                      .groupby([base_filtrada['post_date'].dt.date, 'media_kind'])
                      .size()
                      .reset_index(name='Contagem'))

        # Renomear colunas para clareza
        serie_tipo.columns = ['Data', 'Tipo de Post', 'Contagem']

        # Verificar se há apenas um tipo de post
        if len(serie_tipo['Tipo de Post'].unique()) == 1:
            # Se houver apenas um tipo de post, criar gráfico com uma única linha
            fig = px.line(serie_tipo, 
                          x='Data', 
                          y='Contagem', 
                          title='Série Temporal de Posts por Dia',
                          labels={'Data': 'Data', 'Contagem': 'Número de Posts'},
                          markers=True)  # Adiciona marcadores nos pontos de dados
        else:
            # Se houver mais de um tipo de post, incluir linha pontilhada para o total
            total_posts = serie_tipo.groupby('Data')['Contagem'].sum().reset_index(name='Total de Posts')
            fig = px.line(serie_tipo, 
                          x='Data', 
                          y='Contagem', 
                          color='Tipo de Post', 
                          title='Série Temporal de Posts por Dia e Tipo',
                          labels={'Data': 'Data', 'Contagem': 'Número de Posts', 'Tipo de Post': 'Tipo de Post'},
                          markers=True)  # Adiciona marcadores nos pontos de dados
            
            # Adicionar linha pontilhada para o total de posts
            fig.add_scatter(x=total_posts['Data'], 
                            y=total_posts['Total de Posts'], 
                            mode='lines', 
                            name='Total de Posts', 
                            line=dict(dash='dash', color='purple'))

        # Exibir o gráfico
        st.plotly_chart(fig, use_container_width=True)


def app_funcao_mostrar_cta(posts_df):
    # Breve explicação do que é CTA
    st.write("Call to Action (CTA) são elementos que incentivam o usuário a realizar uma ação específica, como clicar em um link, fazer uma compra ou se inscrever em um serviço.")

    # Calcular a quantidade de posts com CTA
    total_posts = len(posts_df)
    posts_com_cta = len(posts_df[posts_df['cta_present'] == True])

    # Calcular a porcentagem de posts com CTA
    percentual_cta = (posts_com_cta / total_posts) * 100 if total_posts > 0 else 0

    # Exibir o valor percentual em cima do gráfico
    st.write(f"Percentual de posts com CTA: {percentual_cta:.2f}%")

    # Contar a quantidade de posts por tipo de CTA
    cta_count = posts_df['cta_type'].value_counts().reset_index()

    # Renomear as colunas para que sejam interpretadas corretamente pelo Plotly
    cta_count.columns = ['cta_type', 'count']

    # Criar o gráfico de barras horizontais no estilo do Plotly Express
    fig = px.bar(cta_count, 
                 x='count', 
                 y='cta_type', 
                 title='Quantidade de Posts por Tipo de CTA',
                 labels={'cta_type': 'Tipo de CTA', 'count': 'Número de Posts'},
                 color='cta_type',  # Cor das barras com base no tipo de CTA
                 color_continuous_scale='RdBu',  # Escala de cores
                 orientation='h',  # Definir barras horizontais
                 text='count'  # Exibir os valores das contagens nas barras
                 )

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)

def app_funcao_vis_tendencias_topicos(posts_df):
    # Dividir os tópicos considerando vírgula, barra ou espaço em branco e limpar
    all_topics = posts_df['topics'].apply(lambda x: re.split(r'[,\s/]+', x))  # Regex para dividir por ',', ' ' ou '/'
    all_topics = all_topics.explode().str.strip()  # Explode para separar em linhas e remove espaços extras
    
    # Remover tópicos vazios ou com somente "/"
    all_topics = all_topics[all_topics != '/']
    all_topics = all_topics[all_topics != '']  # Remove tópicos vazios após o split
    
    # Contar a frequência de cada tópico
    topic_counts = Counter(all_topics)

    # Converter a contagem para um DataFrame e ordenar em ordem decrescente
    topic_df = pd.DataFrame(topic_counts.items(), columns=['Tópico', 'Contagem'])
    topic_df = topic_df.sort_values(by='Contagem', ascending=False)  # Ordenar decrescentemente

    # Criar um filtro de tópicos (exibição limitada com base na contagem mínima)
    filtro_contagem_min = st.slider("Selecione a contagem mínima de tópicos", 
                                   min_value=1, 
                                   max_value=topic_df['Contagem'].max(), 
                                   value=1, 
                                   step=1)
    
    # Filtrar os tópicos com base na contagem mínima
    filtered_topics = topic_df[topic_df['Contagem'] >= filtro_contagem_min]

    # Criar gráfico de barras horizontais com plotly express
    fig = px.bar(filtered_topics, 
                 x='Contagem', 
                 y='Tópico', 
                 title=f'Top Tópicos mais Comuns (Com contagem mínima de {filtro_contagem_min})',
                 labels={'Contagem': 'Contagem de Tópicos', 'Tópico': 'Tópico'},
                 color='Contagem',  # Cor das barras com base na contagem
                 color_continuous_scale='RdBu',  # Escala de cores vermelho para azul
                 orientation='h',  # Definir barras horizontais
                 text='Contagem'  # Exibir os valores das contagens nas barras
                 )

    # Excluir a legenda de cores
    fig.update_layout(coloraxis_showscale=False)

    # Atualizar as barras para exibir os valores dentro delas
    fig.update_traces(texttemplate='%{text}', textposition='inside')

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)


    with st.expander("Ver Gráfico de Rede dos Tópicos mais Relacionados"):
        st.write("O gráfico de rede abaixo mostra como os tópicos estão relacionados entre si com base na co-ocorrência nos posts. Tópicos que aparecem juntos em posts são conectados por linhas.")
        # Criar gráfico de rede para mostrar os tópicos mais relacionados (com base no filtro)
        G = nx.Graph()

        # Criar uma lista de pares de tópicos para contar co-ocorrências
        for topics in posts_df['topics']:
            topic_list = re.split(r'[,\s/]+', topics)  # Split novamente para tratar os tópicos
            topic_list = [t.strip() for t in topic_list if t.strip() != '/']  # Remover '/'
            
            for i in range(len(topic_list)):
                for j in range(i + 1, len(topic_list)):
                    t1, t2 = topic_list[i], topic_list[j]
                    if t1 != t2:
                        G.add_edge(t1, t2)

        # Desenhar o gráfico de rede
        plt.figure(figsize=(12, 12))
        pos = nx.spring_layout(G, k=0.15, iterations=20)
        nx.draw_networkx(G, pos, node_size=5000, with_labels=True, font_size=10, node_color='skyblue', edge_color='gray', width=2)
        plt.title('Relacionamento entre Tópicos', fontsize=14)

        # Exibir o gráfico de rede no Streamlit
        st.pyplot(plt)

def app_funcao_nuvem_palavras(posts_df):
    # Combinar todos os textos dos posts em uma única string
    all_text = ' '.join(posts_df['words_used'].dropna().astype(str).tolist())

    # Remover as stopwords da língua portuguesa
    stopwords_portuguese = set(STOPWORDS)  # Stopwords padrão do WordCloud
    stopwords_portuguese.update([
        'de', 'a', 'o', 'que', 'e', 'em', 'um', 'para', 'com', 'não', 'uma', 'os', 'nas', 'da', 'do', 
        'se', 'na', 'por', 'mais', 'mas', 'ao', 'as', 'dos', 'ou', 'como', 'nas', 'num', 'numa', 'até', 
        'isso', 'essa', 'essa', 'entre', 'é', 'ser', 'muito', 'foi', 'tem', 'todas', 'isso', 'pela'
    ])  # Adicionar palavras comuns em português

    # Criar a nuvem de palavras com as stopwords removidas
    wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords=stopwords_portuguese).generate(all_text)

    # Exibir a nuvem de palavras
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Nuvem de Palavras dos Textos dos Posts', fontsize=16)
    
    # Exibir no Streamlit
    st.pyplot(plt)

def app_funcao_mostrar_video(posts_df):
    # Filtrar posts do tipo vídeo
    posts_video_df = posts_df[posts_df['media_kind'] == 'video'].copy()

    if not posts_video_df.empty:
        # 1° Container - Estatísticas resumidas
        with st.container():
            st.markdown("## Análise Específica para Vídeos")
            st.write("A análise abaixo é focada exclusivamente em posts de vídeo.")

            # Tempo médio de duração
            avg_duration = posts_video_df['duration_time'].mean()
            st.write(f"**Tempo médio de duração dos vídeos**: {avg_duration:.2f} segundos")

            # % de vídeos com movimento
            percent_with_movement = (posts_video_df['movement_within_env'] == True).mean() * 100
            st.write(f"**% de vídeos que têm movimento**: {percent_with_movement:.2f}%")

            # % de vídeos com áudio conferindo se aud_transcript é NaN ou Nulo
            percent_with_audio = (posts_video_df['aud_transcript'].notna()).mean() * 100
            st.write(f"**% de vídeos com áudio**: {percent_with_audio:.2f}%")

        # 2° Container - Gráficos
        with st.container():
            st.markdown("## Gráficos de Vídeos por Características")
            col1, col2, col3, col4 = st.columns([1, 2, 2, 2])

            # Gráfico: Intenção Captada
            with col1:
                df_intent = posts_video_df['aud_intent'].value_counts().reset_index()
                df_intent.columns = ['aud_intent', 'count']
                fig_intent = px.bar(df_intent,
                                    x='count',
                                    y='aud_intent',
                                    orientation='h',
                                    color='count',
                                    color_continuous_scale='RdBu',
                                    text='count',
                                    labels={'aud_intent': 'Intenção Captada', 'count': 'Número de Posts'},
                                    title='Quantidade de Posts por Intenção Captada')
                st.plotly_chart(fig_intent, use_container_width=True)

            # Gráfico: Categoria de Performance
            with col2:
                df_category = posts_video_df['aud_category_main'].value_counts().reset_index()
                df_category.columns = ['aud_category_main', 'count']
                fig_category = px.bar(df_category,
                                      x='count',
                                      y='aud_category_main',
                                      orientation='h',
                                      color='count',
                                      color_continuous_scale='RdBu',
                                      text='count',
                                      labels={'aud_category_main': 'Categoria de Performance', 'count': 'Número de Posts'},
                                      title='Quantidade de Posts por Categoria de Performance')
                st.plotly_chart(fig_category, use_container_width=True)

            # Gráfico: Tipo de Gatilho
            with col3:
                df_triggers = posts_video_df['aud_triggers'].value_counts().reset_index()
                df_triggers.columns = ['aud_triggers', 'count']
                fig_triggers = px.bar(df_triggers,
                                      x='count',
                                      y='aud_triggers',
                                      orientation='h',
                                      color='count',
                                      color_continuous_scale='RdBu',
                                      text='count',
                                      labels={'aud_triggers': 'Tipo de Gatilho', 'count': 'Número de Posts'},
                                      title='Quantidade de Posts por Tipo de Gatilho')
                st.plotly_chart(fig_triggers, use_container_width=True)

            # Gráfico: Tipo de Movimento
            with col4:
                df_movement = posts_video_df['movement_type'].value_counts().reset_index()
                df_movement.columns = ['movement_type', 'count']
                fig_movement = px.bar(df_movement,
                                      x='count',
                                      y='movement_type',
                                      orientation='h',
                                      color='count',
                                      color_continuous_scale='RdBu',
                                      text='count',
                                      labels={'movement_type': 'Tipo de Movimento', 'count': 'Número de Posts'},
                                      title='Quantidade de Posts por Tipo de Movimento')
                st.plotly_chart(fig_movement, use_container_width=True)